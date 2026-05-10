class FormEvaluator:
    def __init__(self, memory, form_checks: list):
        """
        form_checks: list of check dicts from exercise config.

        Supported check types:
            max       – flag per-rep if metric exceeds warn/error threshold
            range     – flag per-rep if metric outside [low, high]
            stability – flag per-rep if metric changed by > delta vs last rep
            fatigue   – session-level only; evaluated by session_issues()
        """
        self.memory      = memory
        self.form_checks = form_checks
        self._prev: dict[str, float]          = {}
        self._history: dict[str, list[float]] = {}  # all per-rep values

    def evaluate(self) -> list[str]:
        """
        Evaluate per-rep checks (max, range, stability).
        Fatigue checks are intentionally skipped here — use session_issues().
        """
        issues   = []
        snapshot = self.memory.rep_snapshot()

        if snapshot is None:
            return issues

        for check in self.form_checks:
            metric = check["metric"]
            value  = snapshot.get(metric)

            if value is None:
                # Keypoint occluded this rep — invalidate stale baseline.
                self._prev.pop(metric, None)
                continue

            # Record every rep's value for session-level fatigue analysis.
            self._history.setdefault(metric, []).append(value)

            ctype = check["type"]

            if ctype == "fatigue":
                # Deferred to session_issues() — skip here.
                continue

            elif ctype == "max":
                if value > check["error"]:
                    issues.append(check["msg_error"])
                elif value > check["warn"]:
                    issues.append(check["msg_warn"])

            elif ctype == "range":
                if not (check["low"] <= value <= check["high"]):
                    issues.append(check["msg"])

            elif ctype == "stability":
                prev = self._prev.get(metric)
                if prev is not None and abs(value - prev) > check["delta"]:
                    issues.append(check["msg"])
                self._prev[metric] = value

        return issues

    def session_issues(self) -> list[str]:
        """
        Evaluate fatigue checks across the full session.
        Compares average metric value of the first third of reps to the last
        third. Requires at least 3 reps to produce a meaningful result.
        """
        issues = []

        for check in self.form_checks:
            if check["type"] != "fatigue":
                continue

            metric = check["metric"]
            vals   = self._history.get(metric, [])

            if len(vals) < 3:
                continue

            n     = max(1, len(vals) // 3)
            early = sum(vals[:n]) / n
            late  = sum(vals[-n:]) / n

            if (late - early) > check["delta"]:
                issues.append(check["msg"])

        return issues