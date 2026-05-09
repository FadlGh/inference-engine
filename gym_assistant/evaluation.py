class FormEvaluator:
    def __init__(self, memory, form_checks: list):
        """
        form_checks: list of check dicts from exercise config.

        Supported check types:
            max       – flag if metric > warn/error threshold
            range     – flag if metric outside [low, high]
            fatigue   – flag if metric increased by > delta vs last rep
            stability – flag if metric changed by > delta vs last rep
        """
        self.memory      = memory
        self.form_checks = form_checks
        self._prev       = {}   # previous rep values keyed by metric name

    def evaluate(self, window=60) -> list[str]:
        issues   = []
        snapshot = self.memory.rep_snapshot(window=window)

        if snapshot is None:
            return issues

        for check in self.form_checks:
            metric = check["metric"]
            value  = snapshot.get(metric)

            if value is None:
                continue

            ctype = check["type"]

            if ctype == "max":
                if value > check["error"]:
                    issues.append(check["msg_error"])
                elif value > check["warn"]:
                    issues.append(check["msg_warn"])

            elif ctype == "range":
                if not (check["low"] <= value <= check["high"]):
                    issues.append(check["msg"])

            elif ctype == "fatigue":
                prev = self._prev.get(metric)
                if prev is not None and (value - prev) > check["delta"]:
                    issues.append(check["msg"])

            elif ctype == "stability":
                prev = self._prev.get(metric)
                if prev is not None and abs(value - prev) > check["delta"]:
                    issues.append(check["msg"])

            # Update previous value for fatigue/stability checks
            if ctype in ("fatigue", "stability"):
                self._prev[metric] = value

        return issues