import cv2
import mediapipe as mp

from .counter import RepCounter
from .evaluation import FormEvaluator
from .geometry import lm, angle3
from .ui import put_text, phase_color

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils


def _normalize_source(source):
    if isinstance(source, str) and source.isdigit():
        return int(source)
    return source


def run(source=0):
    source = _normalize_source(source)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error: cannot open source '{source}'")
        return

    counter = RepCounter()
    evaluator = FormEvaluator()
    feedback_msg = ""
    feedback_timer = 0

    with mp_pose.Pose(
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    ) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            res = pose.process(rgb)
            rgb.flags.writeable = True

            smoothed_angle = None
            phase = "up"

            if res.pose_landmarks:
                landmarks = res.pose_landmarks.landmark
                kp = {
                    "shoulder": lm(landmarks, 11, w, h),
                    "elbow": lm(landmarks, 13, w, h),
                    "wrist": lm(landmarks, 15, w, h),
                    "hip": lm(landmarks, 23, w, h),
                    "knee": lm(landmarks, 25, w, h),
                    "ankle": lm(landmarks, 27, w, h),
                    "nose": lm(landmarks, 0, w, h),
                }

                angle_left = angle3(kp["shoulder"], kp["elbow"], kp["wrist"])
                angle_right = angle3(lm(landmarks, 12, w, h), lm(landmarks, 14, w, h), lm(landmarks, 16, w, h))
                vis_left = landmarks[13].visibility
                vis_right = landmarks[14].visibility
                elbow_angle = angle_left if vis_left > vis_right else angle_right

                smoothed_angle, depth_ok, phase = counter.update(elbow_angle)
                issues = evaluator.evaluate(kp)

                if issues:
                    feedback_msg = issues[0]
                    feedback_timer = 90
                elif depth_ok:
                    feedback_msg = "Good rep!"
                    feedback_timer = 45

                mp_draw.draw_landmarks(
                    frame,
                    res.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(200, 200, 200), thickness=2, circle_radius=3),
                    mp_draw.DrawingSpec(color=(100, 200, 255), thickness=2),
                )

                ex, ey = int(kp["elbow"][0]), int(kp["elbow"][1])
                elbow_col = (0, 200, 100) if smoothed_angle > 90 else (0, 80, 255)
                cv2.circle(frame, (ex, ey), 10, elbow_col, -1)
                put_text(frame, f"{int(smoothed_angle)}deg", (ex + 12, ey - 8), scale=0.6, color=(255, 220, 50))

            put_text(frame, f"Reps: {counter.reps}", (20, 40), scale=1.0, color=(255, 220, 50))
            put_text(frame, f"Phase: {phase}", (20, 80), scale=0.8, color=phase_color(phase))

            if feedback_timer > 0:
                fb_color = (0, 220, 100) if "Good" in feedback_msg else (30, 100, 255)
                put_text(frame, feedback_msg, (20, h - 30), scale=0.8, color=fb_color, thickness=2)
                feedback_timer -= 1

            cv2.imshow("Push-up Analyzer  [q to quit]", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nSession complete. Total reps: {counter.reps}")
