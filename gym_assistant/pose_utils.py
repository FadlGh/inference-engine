"""
gym_assistant.pose_utils
------------------------
Shared helpers used by both the CV loop (main.py) and the WebSocket
server (server.py).  Keeping them here avoids the copy-paste bug where
a fix in one file is forgotten in the other.
"""

import mediapipe as mp

from .geometry import lm, angle3

VIS_THRESHOLD = 0.5


def build_kp(lmks, keypoints: dict, w: int, h: int) -> dict:
    """
    Extract named keypoints from MediaPipe landmarks.
    Skips any landmark whose visibility is below VIS_THRESHOLD.
    """
    kp = {}
    for name, idx in keypoints.items():
        pt = lmks[idx]
        if pt.visibility >= VIS_THRESHOLD:
            kp[name] = lm(lmks, idx, w, h)
    return kp


def primary_angle(lmks, kp: dict, cfg: dict) -> float | None:
    """
    Pick the more-visible side (left vs right) and return the joint angle
    for the exercise's primary angle joints.
    Returns None if any required keypoint is missing / occluded.
    """
    pa     = cfg["primary_angle"]
    vis_l  = lmks[pa["vis_index"]].visibility
    vis_r  = lmks[pa["vis_index_r"]].visibility
    joints = pa["joints"] if vis_l >= vis_r else pa["joints_r"]

    if not all(j in kp for j in joints):
        return None

    a, b, c = kp[joints[0]], kp[joints[1]], kp[joints[2]]
    return angle3(a, b, c)