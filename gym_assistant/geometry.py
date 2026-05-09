import numpy as np


def angle3(a, b, c):
    """Angle (degrees) at joint B, formed by points A-B-C."""
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cos_a = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return np.degrees(np.arccos(np.clip(cos_a, -1, 1)))


def lm(landmarks, idx, w, h):
    """Return pixel coords for landmark index."""
    point = landmarks[idx]
    return [point.x * w, point.y * h]

def vertical_deviation(a, b):
    """
    Angle (degrees) between the vector a→b and the vertical axis.
    a, b are [x, y] pixel coords.
    0° = perfectly vertical, 90° = horizontal.
    """
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    # vertical vector is (0, 1) in image coords (y increases downward)
    angle = np.degrees(np.arctan2(abs(dx), abs(dy)))
    return angle