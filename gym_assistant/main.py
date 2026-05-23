import cv2
import mediapipe as mp
from collections import Counter

from .counter import RepCounter
from .evaluation import FormEvaluator
from .ui import put_text, phase_color
from .movement_memory import MovementMemory
from .csv_logger import CSVLogger
from .exercises import EXERCISES
from .pose_utils import build_kp, primary_angle, VIS_THRESHOLD

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils


def _normalize_source(source):
    if isinstance(source, str) and source.isdigit():
        return int(source)
    return source


def _session_summary(exercise_name: str, counter: RepCounter, all_issues: list[str], evaluator: "FormEvaluator"):
    print("\n" + "=" * 40)
    print(f"SESSION SUMMARY — {exercise_name}")
    print(f"  Total reps : {counter.reps}")

    avg = counter.avg_tempo()
    if avg is not None:
        print(f"  Avg tempo  : {avg:.1f}s per rep")

    if all_issues:
        freq = Counter(all_issues).most_common(3)
        print("  Top issues :")
        for msg, count in freq:
            print(f"    [{count}x] {msg}")
    else:
        print("  Form       : No issues detected")

    session_issues = evaluator.session_issues()
    if session_issues:
        print("  Session    :")
        for msg in session_issues:
            print(f"    {msg}")

    print("=" * 40)


def run(source=0, exercise: str = "pushup"):
    source = _normalize_source(source)

    if exercise not in EXERCISES:
        print(f"Unknown exercise '{exercise}'. Available: {list(EXERCISES.keys())}")
        return

    cfg = EXERCISES[exercise]
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error: cannot open source '{source}'")
        return

    memory    = MovementMemory(metrics=cfg["memory_metrics"], maxlen=cfg.get("memory_maxlen", 1500))
    counter   = RepCounter(rep_rules=cfg["rep_rules"])
    evaluator = FormEvaluator(memory=memory, form_checks=cfg["form_checks"])
    logger    = CSVLogger(exercise_name=cfg["name"], output_dir="sessions")

    feedback_msg   = ""
    feedback_timer = 0
    all_issues     = []

    with mp_pose.Pose(
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    ) as pose:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            res = pose.process(rgb)
            rgb.flags.writeable = True

            phase = "up"

            if res.pose_landmarks:
                lmks = res.pose_landmarks.landmark
                kp   = build_kp(lmks, cfg["keypoints"], w, h)

                raw_angle = primary_angle(lmks, kp, cfg)

                if raw_angle is not None:
                    smoothed_angle, depth_ok, phase = counter.update(raw_angle)

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

                        if issues:
                            feedback_msg   = issues[0]
                            feedback_timer = 90
                        else:
                            feedback_msg   = "Good rep!"
                            feedback_timer = 45

                    mp_draw.draw_landmarks(
                        frame,
                        res.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        mp_draw.DrawingSpec(color=(200, 200, 200), thickness=2),
                        mp_draw.DrawingSpec(color=(100, 200, 255), thickness=2),
                    )

                    # Angle indicator at primary joint
                    pa     = cfg["primary_angle"]
                    vis_l  = lmks[pa["vis_index"]].visibility
                    vis_r  = lmks[pa["vis_index_r"]].visibility
                    joints = pa["joints"] if vis_l >= vis_r else pa["joints_r"]

                    if all(j in kp for j in joints):
                        jx, jy = int(kp[joints[1]][0]), int(kp[joints[1]][1])
                        color  = (0, 200, 100) if smoothed_angle > cfg["rep_rules"]["down_threshold"] else (0, 80, 255)
                        cv2.circle(frame, (jx, jy), 10, color, -1)
                        put_text(frame, f"{int(smoothed_angle)}deg", (jx + 12, jy - 8))

            put_text(frame, f"{cfg['name']}  |  Reps: {counter.reps}", (20, 40))
            put_text(frame, f"Phase: {phase}", (20, 80), color=phase_color(phase))

            if counter.last_tempo is not None:
                put_text(frame, f"Tempo: {counter.last_tempo:.1f}s", (20, 120))

            if feedback_timer > 0:
                put_text(frame, feedback_msg, (20, h - 30))
                feedback_timer -= 1

            cv2.imshow(cfg["name"], frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()
    logger.close()
    _session_summary(cfg["name"], counter, all_issues, evaluator)