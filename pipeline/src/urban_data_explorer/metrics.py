"""Mesure de la performance du pipeline ETL (C2.4).

Chronometre chaque etape du build et compte la volumetrie (nombre de lignes par
dataset produit), puis ecrit un rapport `reports/pipeline_metrics.csv`. Cela
complete `scripts/benchmark.py` (qui mesure l'API) en mesurant cette fois le
*pipeline* lui-meme : temps d'execution par etape et volumes traites.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import time

from .paths import repo_path


class PipelineProfiler:
    """Profiler simple a base de `lap()` : pas de re-indentation du code mesure.

    Usage :
        profiler = PipelineProfiler()
        ...                       # etape 1
        profiler.lap("ingestion")
        ...                       # etape 2
        profiler.lap("build")
        profiler.record_rows("gold_sales_yearly", df)
        profiler.write_report()
    """

    def __init__(self) -> None:
        self._t0 = time.perf_counter()
        self._last = self._t0
        self.stages: list[dict[str, object]] = []
        self.volumetry: dict[str, int] = {}

    def lap(self, name: str) -> None:
        now = time.perf_counter()
        self.stages.append({"stage": name, "seconds": round(now - self._last, 3)})
        self._last = now

    def record_rows(self, name: str, frame: object) -> None:
        try:
            self.volumetry[name] = int(len(frame))  # type: ignore[arg-type]
        except TypeError:
            self.volumetry[name] = 0

    def total_seconds(self) -> float:
        return round(time.perf_counter() - self._t0, 3)

    def write_report(self, path: object | None = None) -> str:
        report_dir = repo_path("reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        csv_path = path if path is not None else (report_dir / "pipeline_metrics.csv")
        generated_at = datetime.now(timezone.utc).isoformat()

        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["generated_at", "kind", "name", "value"])
            for stage in self.stages:
                writer.writerow([generated_at, "stage_seconds", stage["stage"], stage["seconds"]])
            for name, rows in self.volumetry.items():
                writer.writerow([generated_at, "rows", name, rows])
            writer.writerow([generated_at, "stage_seconds", "TOTAL", self.total_seconds()])

        return str(csv_path)

    def summary_lines(self) -> list[str]:
        lines = ["== Performance pipeline (C2.4) =="]
        for stage in self.stages:
            lines.append(f"  {stage['stage']:<22} {stage['seconds']:>8.3f}s")
        lines.append(f"  {'TOTAL':<22} {self.total_seconds():>8.3f}s")
        if self.volumetry:
            lines.append("  -- volumetrie (lignes) --")
            for name, rows in self.volumetry.items():
                lines.append(f"  {name:<30} {rows:>12,}")
        return lines
