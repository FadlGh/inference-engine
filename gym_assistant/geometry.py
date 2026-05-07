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
