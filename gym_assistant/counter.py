class EMA:
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.val = None

    def update(self, x):
        self.val = x if self.val is None else self.alpha * x + (1 - self.alpha) * self.val
        return self.val


class RepCounter:
    def __init__(self):
        self.reps = 0
        self.smoother = EMA(alpha=0.5)
        self.min_angle = 180
        self.went_down = False
        self.lockout = 0

    def update(self, raw_angle):
        angle = self.smoother.update(raw_angle)
        depth_ok = False

        if self.lockout > 0:
            self.lockout -= 1
            return angle, depth_ok, self.phase(angle)

        self.min_angle = min(self.min_angle, angle)
        self.went_down = self.went_down or angle < 120

        if angle > 155 and self.min_angle < 110 and self.went_down:
            self.reps += 1
            depth_ok = True
            self.lockout = 20
            self.went_down = False
            self.min_angle = 180

        return angle, depth_ok, self.phase(angle)

    def phase(self, angle):
        if angle < 90:
            return "bottom"
        if self.went_down:
            return "down"
        return "up"
