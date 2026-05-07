# requirements: mediapipe opencv-python numpy
# install: pip install mediapipe opencv-python numpy
# run:     python pushup_analyzer.py
#          pass a video path as arg: python pushup_analyzer.py myvideo.mp4

import sys
import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils


# ── Geometry helpers ──────────────────────────────────────────────────────────

def angle3(a, b, c):
    """Angle (degrees) at joint B, formed by points A-B-C."""
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cos_a = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return np.degrees(np.arccos(np.clip(cos_a, -1, 1)))


def lm(landmarks, idx, w, h):
    """Return pixel coords for landmark index."""
    p = landmarks[idx]
    return [p.x * w, p.y * h]


# ── Exponential moving average smoother ───────────────────────────────────────

class EMA:
    def __init__(self, alpha=0.4):
        self.alpha = alpha
        self.val = None

    def update(self, x):
        self.val = x if self.val is None else self.alpha * x + (1 - self.alpha) * self.val
        return self.val


# ── Form evaluator ────────────────────────────────────────────────────────────

class FormEvaluator:
    def evaluate(self, kp):
        """
        Returns a list of feedback strings, highest priority first.
        kp: dict of named keypoints as [x, y] pixel coords.
        """
        issues = []

        # 1. Back alignment — spine angle deviation from 180°
        spine = angle3(kp['shoulder'], kp['hip'], kp['ankle'])
        deviation = abs(180 - spine)
        if deviation > 25:
            # y increases downward in image coords
            sagging = kp['hip'][1] > kp['shoulder'][1] + 20
            issues.append(
                "Hips dropping — tighten your core"
                if sagging else
                "Lower your hips — keep body straight"
            )
        elif deviation > 15:
            issues.append("Minor back sag — engage your core")

        # 2. Neck alignment
        neck = angle3(kp['nose'], kp['shoulder'], kp['hip'])
        if neck < 160:
            issues.append("Keep head neutral — don't crane your neck")

        return issues


# ── Rep counter with phase state machine ──────────────────────────────────────

class RepCounter:
    def __init__(self):
        self.reps = 0
        self.smoother = EMA(alpha=0.5)
        self.min_angle = 180
        self.went_down = False
        self.lockout = 0

    def update(self, raw_angle):
        angle = self.smoother.update(raw_angle)
        depth_ok = False

        if self.lockout > 0:
            self.lockout -= 1
            return angle, depth_ok

        self.min_angle = min(self.min_angle, angle)

        if angle > 155 and self.min_angle < 110:
            self.reps += 1
            depth_ok = True
            self.lockout = 20
            # do NOT reset min_angle here

        # Only reset min_angle when clearly at top and not moving down
        if angle > 160 and self.min_angle > 150:
            self.min_angle = 180

        return angle, depth_ok

# ── UI helpers ────────────────────────────────────────────────────────────────

def put_text(frame, text, pos, scale=0.7, color=(255, 255, 255), thickness=2):
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, (0,0,0), thickness+2)
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)


def phase_color(phase):
    return {'up': (0, 200, 100), 'down': (0, 165, 255), 'bottom': (0, 80, 255)}.get(phase, (200, 200, 200))


# ── Main loop ─────────────────────────────────────────────────────────────────

def run(source=0):
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

            if res.pose_landmarks:
                L = res.pose_landmarks.landmark

                # Use left-side landmarks for side-view (adjust to right if needed)
                kp = {
                    'shoulder': lm(L, 11, w, h),
                    'elbow':    lm(L, 13, w, h),
                    'wrist':    lm(L, 15, w, h),
                    'hip':      lm(L, 23, w, h),
                    'knee':     lm(L, 25, w, h),
                    'ankle':    lm(L, 27, w, h),
                    'nose':     lm(L,  0, w, h),
                }

                # With this:
                angle_left  = angle3(lm(L,11,w,h), lm(L,13,w,h), lm(L,15,w,h))
                angle_right = angle3(lm(L,12,w,h), lm(L,14,w,h), lm(L,16,w,h))

                # Use whichever elbow is more visible (higher confidence)
                vis_left  = L[13].visibility
                vis_right = L[14].visibility
                elbow_angle = angle_left if vis_left > vis_right else angle_right
                smoothed_angle, depth_ok = counter.update(elbow_angle)
                issues = evaluator.evaluate(kp)

                # Update feedback (anti-spam: highest priority, min display time)
                if issues:
                    feedback_msg = issues[0]
                    feedback_timer = 90   # ~3s at 30fps
                elif depth_ok:
                    feedback_msg = "Good rep!"
                    feedback_timer = 45

                # Draw skeleton
                mp_draw.draw_landmarks(
                    frame,
                    res.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(200, 200, 200), thickness=2, circle_radius=3),
                    mp_draw.DrawingSpec(color=(100, 200, 255), thickness=2),
                )

                # Highlight elbow joint
                ex, ey = int(kp['elbow'][0]), int(kp['elbow'][1])
                elbow_col = (0, 200, 100) if smoothed_angle > 90 else (0, 80, 255)
                cv2.circle(frame, (ex, ey), 10, elbow_col, -1)
                put_text(frame, f"{int(smoothed_angle)}deg", (ex + 12, ey - 8),
                         scale=0.6, color=(255, 220, 50))

            # ── HUD ──────────────────────────────────────────────────────────
            put_text(frame, f"Reps: {counter.reps}", (20, 40), scale=1.0, color=(255, 220, 50))
            if res.pose_landmarks:
                phase = 'down' if smoothed_angle < 100 else 'up'
                if counter.went_down:
                    phase = 'bottom' if smoothed_angle < 90 else 'down'
                put_text(frame, f"Phase: {phase}", (20, 80), scale=0.8, color=phase_color(phase))

            # Feedback message
            if feedback_timer > 0:
                fb_color = (0, 220, 100) if "Good" in feedback_msg else (30, 100, 255)
                put_text(frame, feedback_msg, (20, h - 30),
                         scale=0.8, color=fb_color, thickness=2)
                feedback_timer -= 1
                

            cv2.imshow("Push-up Analyzer  [q to quit]", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nSession complete. Total reps: {counter.reps}")


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else 0
    # source = 0         → webcam
    # source = "vid.mp4" → video file
    run(source)