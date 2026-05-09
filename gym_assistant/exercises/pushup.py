PUSHUP = {
    "name": "Push-up",
    "memory_maxlen": 1500,
    # MediaPipe landmark indices used by this exercise
    "keypoints": {
        "shoulder":     11,
        "elbow":        13,
        "wrist":        15,
        "shoulder_r":   12,
        "elbow_r":      14,
        "wrist_r":      16,
        "hip":          23,
        "knee":         25,
        "ankle":        27,
        "nose":         0,
    },

    # Which angle drives rep counting (uses visibility to pick left vs right)
    "primary_angle": {
        "joints":           ["shoulder", "elbow", "wrist"],
        "joints_r":         ["shoulder_r", "elbow_r", "wrist_r"],
        "vis_index":        13,   # left elbow
        "vis_index_r":      14,   # right elbow
    },

    "rep_rules": {
        "down_threshold":   120,  # angle < this → going down
        "up_threshold":     155,  # angle > this → rep complete (must also have gone down)
        "min_depth":        110,  # must have reached this angle to count
        "lockout_frames":   20,
    },

    # Metrics tracked per frame by MovementMemory
    "memory_metrics": [
        {
            "name":   "spine_dev",
            "type":   "deviation_from_straight",   # abs(180 - angle)
            "joints": ["shoulder", "hip", "ankle"],
        },
        {
            "name":   "neck",
            "type":   "angle",
            "joints": ["nose", "shoulder", "hip"],
        },
    ],

    # Form checks evaluated after each rep
    "form_checks": [
        {
            "metric":    "spine_dev",
            "type":      "max",          # flag if value exceeds threshold
            "warn":      12,
            "error":     18,
            "msg_warn":  "Mild loss of core alignment — stay tighter",
            "msg_error": "Core stability is breaking down — reset tension",
        },
        {
            "metric":       "spine_dev",
            "type":         "fatigue",   # flag if increasing rep-to-rep
            "delta":        4,
            "msg":          "Form is degrading across reps — slow down or stop early",
        },
        {
            "metric":    "neck",
            "type":      "range",        # flag if outside [low, high]
            "low":       150,
            "high":      172,
            "msg":       "Keep head more neutral",
        },
        {
            "metric":    "neck",
            "type":      "stability",    # flag if changing too fast rep-to-rep
            "delta":     6,
            "msg":       "Neck position changing under fatigue",
        },
    ],
}