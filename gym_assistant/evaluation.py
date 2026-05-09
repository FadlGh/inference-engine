class FormEvaluator:
    def __init__(self, memory):
        self.memory = memory
        self.prev_spine = None
        self.prev_neck = None

    def evaluate(self):
        issues = []

        snapshot = self.memory.rep_snapshot()
        if snapshot is None:
            return issues

        spine, neck = snapshot

        # -------------------------
        # SPINE (core stability)
        # -------------------------
        if spine > 18:
            issues.append("Core stability is breaking down — reset tension")
        elif spine > 12:
            issues.append("Mild loss of core alignment — stay tighter")

        # -------------------------
        # FATIGUE (rep-to-rep change)
        # -------------------------
        if self.prev_spine is not None:
            if spine - self.prev_spine > 4:
                issues.append("Form is degrading across reps — slow down or stop early")

        self.prev_spine = spine

        # -------------------------
        # NECK (light signal only)
        # -------------------------
        if neck < 150 or neck > 172:
            issues.append("Keep head more neutral")

        if self.prev_neck is not None:
            if abs(neck - self.prev_neck) > 6:
                issues.append("Neck position changing under fatigue")

        self.prev_neck = neck

        return issues