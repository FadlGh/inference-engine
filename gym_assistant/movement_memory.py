from collections import deque
from .geometry import angle3, vertical_deviation


class _EMA:
    """Lightweight EMA for per-metric smoothing inside MovementMemory."""
    def __init__(self, alpha: float = 0.4):
        self.alpha = alpha
        self.val   = None

    def update(self, x: float) -> float:
        self.val = x if self.val is None else self.alpha * x + (1 - self.alpha) * self.val
        return self.val


class MovementMemory:
    def __init__(self, metrics: list, maxlen: int = 90):
        self.metrics  = metrics
        self.history  = deque(maxlen=maxlen)

        # Per-metric EMA smoothers — eliminates landmark jitter before storing.
        self._smoothers: dict[str, _EMA] = {
            m["name"]: _EMA(alpha=0.4) for m in metrics
        }

        # Rep-boundary tracking.
        # We count total frames added so we can always slice the correct
        # number of tail frames regardless of deque eviction.
        self._total_added:     int = 0
        self._rep_start_count: int = 0

    def mark_rep_start(self):
        """
        Call this on the frame descent begins (counter.descent_started is True).
        rep_snapshot() will use only frames added after this marker.
        """
        self._rep_start_count = self._total_added

    def add(self, kp: dict):
        entry = {}
        for m in self.metrics:
            joints = m["joints"]
            if not all(j in kp for j in joints):
                continue

            if m["type"] == "vertical_deviation":
                a, b    = kp[joints[0]], kp[joints[1]]
                raw_val = vertical_deviation(a, b)
            else:
                a, b, c = kp[joints[0]], kp[joints[1]], kp[joints[2]]
                raw     = angle3(a, b, c)
                raw_val = abs(180 - raw) if m["type"] == "deviation_from_straight" else raw

            # Smooth before storing to suppress per-frame landmark noise.
            entry[m["name"]] = self._smoothers[m["name"]].update(raw_val)

        self.history.append(entry)
        self._total_added += 1

    def rep_snapshot(self, window: int = 60) -> dict | None:
        """
        Aggregate metrics over the current rep's frames.

        Priority:
          1. Frames since mark_rep_start() — exact rep boundary.
          2. Fallback to `window` frames if no mark has been set yet
             (e.g. very first rep before descent tracking is active).

        Resets the rep-start marker after aggregating so the next call
        doesn't re-include the same frames.
        """
        frames_in_rep = self._total_added - self._rep_start_count
        available     = frames_in_rep if frames_in_rep > 0 else min(window, len(self.history))
        available     = min(available, len(self.history))

        # Reset marker so subsequent reps start fresh.
        self._rep_start_count = self._total_added

        if available == 0:
            return None

        recent   = list(self.history)[-available:]
        snapshot = {}

        for m in self.metrics:
            name = m["name"]
            agg  = m.get("agg", "mean")
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