import csv
import os
import time


class CSVLogger:
    def __init__(self, exercise_name: str, output_dir: str = "."):
        os.makedirs(output_dir, exist_ok=True)
        ts       = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{exercise_name}_{ts}.csv"
        self.path = os.path.join(output_dir, filename)

        self._file   = open(self.path, "w", newline="")
        self._writer = csv.writer(self._file)
        self._writer.writerow([
            "rep", "timestamp", "min_angle", "tempo_sec", "issues"
        ])

    def log(self, rep: int, min_angle: float, tempo: float | None, issues: list[str]):
        self._writer.writerow([
            rep,
            time.strftime("%H:%M:%S"),
            f"{min_angle:.1f}",
            f"{tempo:.2f}" if tempo is not None else "",
            "; ".join(issues) if issues else "ok",
        ])
        self._file.flush()

    def close(self):
        self._file.close()