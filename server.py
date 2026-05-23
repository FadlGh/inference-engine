"""
gym_assistant — WebSocket server
Run: uvicorn server:app --reload
Then open the React dashboard (dev server or index.html).
"""

import asyncio
import base64
import json
import time
from collections import Counter

import cv2
import mediapipe as mp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from gym_assistant.counter import RepCounter
from gym_assistant.evaluation import FormEvaluator
from gym_assistant.exercises import EXERCISES
from gym_assistant.movement_memory import MovementMemory
from gym_assistant.csv_logger import CSVLogger
from gym_assistant.pose_utils import build_kp, primary_angle  # FIX: shared helpers, no duplication

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils


def _frame_to_jpeg_b64(frame) -> str:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
    return base64.b64encode(buf).decode()


@app.websocket("/ws/{exercise}")
async def pose_stream(ws: WebSocket, exercise: str):
    await ws.accept()

    if exercise not in EXERCISES:
        await ws.send_text(json.dumps({"error": f"Unknown exercise '{exercise}'"}))
        await ws.close()
        return

    cfg       = EXERCISES[exercise]
    memory    = MovementMemory(metrics=cfg["memory_metrics"], maxlen=cfg.get("memory_maxlen", 1500))
    counter   = RepCounter(rep_rules=cfg["rep_rules"])
    evaluator = FormEvaluator(memory=memory, form_checks=cfg["form_checks"])
    logger    = CSVLogger(exercise_name=cfg["name"], output_dir="sessions")

    all_issues:  list[str]  = []
    per_rep_log: list[dict] = []
    feedback_msg   = ""
    feedback_timer = 0          # counts down in frames-with-pose only (FIX)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await ws.send_text(json.dumps({"error": "Cannot open webcam"}))
        await ws.close()
        return

    with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
        try:
            while True:
                # Non-blocking check for client commands (stop, etc.)
                try:
                    msg  = await asyncio.wait_for(ws.receive_text(), timeout=0.001)
                    data = json.loads(msg)
                    if data.get("cmd") == "stop":
                        break
                except asyncio.TimeoutError:
                    pass
                except Exception:
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                h, w = frame.shape[:2]
                rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                res = pose.process(rgb)
                rgb.flags.writeable = True

                phase          = "up"
                smoothed_angle = None

                if res.pose_landmarks:
                    lmks = res.pose_landmarks.landmark
                    kp   = build_kp(lmks, cfg["keypoints"], w, h)
                    raw  = primary_angle(lmks, kp, cfg)

                    if raw is not None:
                        smoothed_angle, depth_ok, phase = counter.update(raw)

                        if counter.descent_started:
                            memory.mark_rep_start()
                        memory.add(kp)

                        if depth_ok:
                            issues = evaluator.evaluate()
                            all_issues.extend(issues)

                            logger.log(
                                rep=counter.reps,
                                min_angle=counter.last_min_angle,
                                tempo=counter.last_tempo,
                                issues=issues,
                            )

                            per_rep_log.append({
                                "rep":       counter.reps,
                                "time":      time.strftime("%H:%M:%S"),
                                "min_angle": round(counter.last_min_angle, 1),
                                "tempo":     round(counter.last_tempo, 2) if counter.last_tempo else None,
                                "issues":    issues or [],
                            })

                            feedback_msg   = issues[0] if issues else "Good rep!"
                            feedback_timer = 90 if issues else 45

                        # FIX: only tick down timer when pose is visible,
                        # so a brief occlusion doesn't prematurely clear feedback.
                        if feedback_timer > 0:
                            feedback_timer -= 1
                        else:
                            feedback_msg = ""

                    mp_draw.draw_landmarks(
                        frame,
                        res.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        mp_draw.DrawingSpec(color=(200, 200, 200), thickness=2),
                        mp_draw.DrawingSpec(color=(100, 200, 255), thickness=2),
                    )

                # FIX: call avg_tempo() once, reuse the value
                avg_tempo_val = counter.avg_tempo()

                freq = Counter(all_issues).most_common(3)

                payload = {
                    "frame":          _frame_to_jpeg_b64(frame),
                    "reps":           counter.reps,
                    "phase":          phase,
                    "angle":          round(smoothed_angle, 1) if smoothed_angle is not None else None,
                    "tempo":          round(counter.last_tempo, 2) if counter.last_tempo else None,
                    "avg_tempo":      round(avg_tempo_val, 2) if avg_tempo_val is not None else None,
                    "feedback":       feedback_msg,
                    "per_rep_log":    per_rep_log[-20:],
                    "top_issues":     [{"msg": m, "count": c} for m, c in freq],
                    "session_issues": evaluator.session_issues(),
                    "exercise":       cfg["name"],
                }

                await ws.send_text(json.dumps(payload))
                await asyncio.sleep(0.033)   # ~30 fps

        except WebSocketDisconnect:
            pass
        finally:
            cap.release()
            logger.close()