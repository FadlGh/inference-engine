"""
gym_assistant — WebSocket server
Run: uvicorn server:app --reload
Then open the React dashboard (index.html or dev server).
"""

import asyncio
import base64
import json
import time
from collections import Counter

import cv2
import mediapipe as mp
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# ── gym_assistant internals ──────────────────────────────────────────────────
from gym_assistant.counter import RepCounter
from gym_assistant.evaluation import FormEvaluator
from gym_assistant.exercises import EXERCISES
from gym_assistant.geometry import lm, angle3
from gym_assistant.movement_memory import MovementMemory
from gym_assistant.csv_logger import CSVLogger

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils
VIS_THRESHOLD = 0.5


# ── helpers (copied from main.py, kept local to avoid import side effects) ──

def _build_kp(lmks, keypoints, w, h):
    kp = {}
    for name, idx in keypoints.items():
        pt = lmks[idx]
        if pt.visibility >= VIS_THRESHOLD:
            kp[name] = lm(lmks, idx, w, h)
    return kp


def _primary_angle(lmks, kp, cfg):
    pa    = cfg["primary_angle"]
    vis_l = lmks[pa["vis_index"]].visibility
    vis_r = lmks[pa["vis_index_r"]].visibility
    joints = pa["joints"] if vis_l >= vis_r else pa["joints_r"]
    if not all(j in kp for j in joints):
        return None
    a, b, c = kp[joints[0]], kp[joints[1]], kp[joints[2]]
    return angle3(a, b, c)


def _frame_to_jpeg_b64(frame) -> str:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
    return base64.b64encode(buf).decode()


# ── WebSocket endpoint ───────────────────────────────────────────────────────

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

    all_issues: list[str] = []
    per_rep_log: list[dict] = []
    feedback_msg   = ""
    feedback_timer = 0

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await ws.send_text(json.dumps({"error": "Cannot open webcam"}))
        await ws.close()
        return

    with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
        try:
            while True:
                # Check for client messages (start/stop/change exercise)
                try:
                    msg = await asyncio.wait_for(ws.receive_text(), timeout=0.001)
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

                phase         = "up"
                smoothed_angle = None

                if res.pose_landmarks:
                    lmks = res.pose_landmarks.landmark
                    kp   = _build_kp(lmks, cfg["keypoints"], w, h)
                    raw  = _primary_angle(lmks, kp, cfg)

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

                    # Draw skeleton on frame
                    mp_draw.draw_landmarks(
                        frame,
                        res.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        mp_draw.DrawingSpec(color=(200, 200, 200), thickness=2),
                        mp_draw.DrawingSpec(color=(100, 200, 255), thickness=2),
                    )

                if feedback_timer > 0:
                    feedback_timer -= 1
                else:
                    feedback_msg = ""

                # Session-level issue frequency
                freq = Counter(all_issues).most_common(3)

                payload = {
                    "frame":         _frame_to_jpeg_b64(frame),
                    "reps":          counter.reps,
                    "phase":         phase,
                    "angle":         round(smoothed_angle, 1) if smoothed_angle is not None else None,
                    "tempo":         round(counter.last_tempo, 2) if counter.last_tempo else None,
                    "avg_tempo":     round(counter.avg_tempo(), 2) if counter.avg_tempo() else None,
                    "feedback":      feedback_msg,
                    "per_rep_log":   per_rep_log[-20:],   # last 20 reps
                    "top_issues":    [{"msg": m, "count": c} for m, c in freq],
                    "session_issues": evaluator.session_issues(),
                    "exercise":      cfg["name"],
                }

                await ws.send_text(json.dumps(payload))
                await asyncio.sleep(0.033)   # ~30 fps

        except WebSocketDisconnect:
            pass
        finally:
            cap.release()
            logger.close()