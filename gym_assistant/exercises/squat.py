SQUAT = {
    "name": "Squat",
    "memory_maxlen": 1500,
    "keypoints": {
        "hip":          23,
        "knee":         25,
        "ankle":        27,
        "hip_r":        24,
        "knee_r":       26,
        "ankle_r":      28,
        "shoulder":     11,
        "shoulder_r":   12,
        "nose":         0,
    },

    "primary_angle": {
        "joints":       ["hip", "knee", "ankle"],
        "joints_r":     ["hip_r", "knee_r", "ankle_r"],
        "vis_index":    25,   # left knee
        "vis_index_r":  26,   # right knee
    },

    "rep_rules": {
        "down_threshold":   140,  # knee angle < this → going down
        "up_threshold":     160,  # knee angle > this → rep complete
        "min_depth":        110,  # must reach at least this depth
        "lockout_frames":   20,
    },

    "memory_metrics": [
        {
            # Angle between shoulder→hip vector and vertical axis.
            # Normal squat at depth: 30–45°. agg:max catches the worst lean
            # in the rep (typically at the bottom).
            "name":   "spine_dev",
            "type":   "vertical_deviation",
            "agg":    "max",
            "joints": ["shoulder", "hip"],
        },
    ],

    "form_checks": [
        {
            # Normal squat peak lean is 30–45°. Warn starts at 52° to avoid
            # flagging people with normal hip mobility on every rep.
            "metric":    "spine_dev",
            "type":      "max",
            "warn":      52,
            "error":     68,
            "msg_warn":  "Slight excessive lean — keep chest up",
            "msg_error": "Excessive forward lean — reduce depth or check mobility",
        },
        {
            # Session-level only — evaluated in summary, not per-rep.
            # Compares average lean of last third of reps vs first third.
            "metric":    "spine_dev",
            "type":      "fatigue",
            "delta":     5,
            "msg":       "Posture degraded across the session — work on core endurance",
        },
    ],
}