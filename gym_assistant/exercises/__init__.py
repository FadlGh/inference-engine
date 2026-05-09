from .pushup import PUSHUP
from .squat import SQUAT

# Registry: key is the CLI/UI name, value is the config dict
EXERCISES = {
    "pushup": PUSHUP,
    "squat":  SQUAT,
}

__all__ = ["EXERCISES", "PUSHUP", "SQUAT"]