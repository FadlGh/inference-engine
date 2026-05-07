from .geometry import angle3


class FormEvaluator:
    def evaluate(self, kp):
        """Returns feedback strings in priority order."""
        issues = []

        spine = angle3(kp["shoulder"], kp["hip"], kp["ankle"])
        deviation = abs(180 - spine)
        if deviation > 25:
            sagging = kp["hip"][1] > kp["shoulder"][1] + 20
            issues.append(
                "Hips dropping — tighten your core"
                if sagging else
                "Lower your hips — keep body straight"
            )
        elif deviation > 15:
            issues.append("Minor back sag — engage your core")

        neck = angle3(kp["nose"], kp["shoulder"], kp["hip"])
        if neck < 160:
            issues.append("Keep head neutral — don't crane your neck")

        return issues
