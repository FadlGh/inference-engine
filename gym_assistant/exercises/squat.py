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
            "name":   "spine_dev",
            "type":   "vertical_deviation",
            "joints": ["shoulder", "hip"],   # just 2 points — torso vector
        },
        {
            "name":   "knee_angle",
            "type":   "angle",
            "agg":    "min", 
            "joints": ["hip", "knee", "ankle"],
        },
        # Tracks lateral knee deviation proxy via left side only
        # (full valgus detection needs frontal camera — this is a sagittal proxy)
        {
            "name":   "neck",
            "type":   "angle",
            "joints": ["nose", "shoulder", "hip"],
        },
    ],

    "form_checks": [
        {
            "metric":    "spine_dev",
            "type":      "max",
            "warn":      45,      
            "error":     60,       
            "msg_warn":  "Slight excessive lean — keep chest up",
            "msg_error": "Excessive forward lean — reduce depth or check mobility",
        },
        {
            "metric":    "spine_dev",
            "type":      "fatigue",
            "delta":     8,        # was 5
            "msg":       "Posture degrading across reps — rest or stop",
        },
        {
            "metric":    "knee_angle",
            "type":      "range",
            "low":       60,
            "high":      175,
            "msg":       "Check knee alignment — avoid caving inward",
        },
        {
            "metric":    "neck",
            "type":      "range",
            "low":       145,
            "high":      175,
            "msg":       "Keep your gaze forward — avoid looking down",
        },
    ],
}