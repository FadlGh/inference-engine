import cv2


def put_text(frame, text, pos, scale=0.7, color=(255, 255, 255), thickness=2):
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness + 2)
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)


def phase_color(phase):
    return {
        "up": (0, 200, 100),
        "down": (0, 165, 255),
        "bottom": (0, 80, 255),
    }.get(phase, (200, 200, 200))
