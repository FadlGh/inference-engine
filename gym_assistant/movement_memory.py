from collections import deque
from .geometry import angle3


class MovementMemory:
    def __init__(self, maxlen=90):
        self.history = deque(maxlen=maxlen)

    def add(self, kp):
        spine = angle3(kp["shoulder"], kp["hip"], kp["ankle"])
        neck = angle3(kp["nose"], kp["shoulder"], kp["hip"])

        self.history.append({
            "spine_dev": abs(180 - spine),
            "neck": neck
        })

    def rep_snapshot(self, window=20):
        if len(self.history) < window:
            return None

        recent = list(self.history)[-window:]

        spine = sum(x["spine_dev"] for x in recent) / window
        neck = sum(x["neck"] for x in recent) / window

        return spine, neck