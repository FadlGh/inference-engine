from collections import deque
from .geometry import angle3, vertical_deviation


class MovementMemory:
    def __init__(self, metrics: list, maxlen: int = 90):
        self.metrics = metrics
        self.history = deque(maxlen=maxlen)

    def add(self, kp: dict):
        entry = {}
        for m in self.metrics:
            joints = m["joints"]
            if not all(j in kp for j in joints):
                continue

            if m["type"] == "vertical_deviation":
                a, b = kp[joints[0]], kp[joints[1]]
                entry[m["name"]] = vertical_deviation(a, b)

            else:
                a, b, c = kp[joints[0]], kp[joints[1]], kp[joints[2]]
                raw = angle3(a, b, c)
                if m["type"] == "deviation_from_straight":
                    entry[m["name"]] = abs(180 - raw)
                else:
                    entry[m["name"]] = raw

        self.history.append(entry)

    def rep_snapshot(self, window: int = 60) -> dict | None:
        if len(self.history) < window:
            return None

        recent = list(self.history)[-window:]
        snapshot = {}

        for m in self.metrics:
            name = m["name"]
            agg  = m.get("agg", "mean")   # default to mean
            vals = [f[name] for f in recent if name in f]
            if not vals:
                continue

            if agg == "min":
                snapshot[name] = min(vals)
            elif agg == "max":
                snapshot[name] = max(vals)
            else:
                snapshot[name] = sum(vals) / len(vals)

        return snapshot if snapshot else None