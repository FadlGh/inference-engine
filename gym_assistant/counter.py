class EMA:
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.val = None

    def update(self, x):
        self.val = x if self.val is None else self.alpha * x + (1 - self.alpha) * self.val
        return self.val


class RepCounter:
    def __init__(self, rep_rules: dict):
        """
        rep_rules keys:
            down_threshold  – angle below this means the joint is bending (going down)
            up_threshold    – angle above this (after going down) counts as a completed rep
            min_depth       – joint must have reached at least this angle during the rep
            lockout_frames  – frames to ignore after a rep is counted (debounce)
        """
        self.down_threshold  = rep_rules["down_threshold"]
        self.up_threshold    = rep_rules["up_threshold"]
        self.min_depth       = rep_rules["min_depth"]
        self.lockout_frames  = rep_rules["lockout_frames"]

        self.reps      = 0
        self.smoother  = EMA(alpha=0.5)
        self.min_angle = 180
        self.went_down = False
        self.lockout   = 0

    def update(self, raw_angle: float):
        """
        Returns (smoothed_angle, depth_ok, phase).
        depth_ok is True only on the frame a valid rep is completed.
        """
        angle    = self.smoother.update(raw_angle)
        depth_ok = False

        if self.lockout > 0:
            self.lockout -= 1
            return angle, depth_ok, self._phase(angle)

        self.min_angle = min(self.min_angle, angle)
        self.went_down = self.went_down or angle < self.down_threshold

        if (
            angle > self.up_threshold
            and self.min_angle < self.min_depth
            and self.went_down
        ):
            self.reps   += 1
            depth_ok     = True
            self.lockout = self.lockout_frames
            self.went_down = False
            self.min_angle = 180

        return angle, depth_ok, self._phase(angle)

    def _phase(self, angle: float) -> str:
        if angle < self.min_depth:
            return "bottom"
        if self.went_down:
            return "down"
        return "up"