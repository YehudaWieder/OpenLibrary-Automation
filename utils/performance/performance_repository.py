"""Persistence layer for performance run history."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class PerformanceRepository:
    """Single responsibility: read/write performance JSON history."""

    def __init__(self, report_path: str = "performance_report.json") -> None:
        self.report_path = Path(report_path)

    def load_report(self) -> Dict[str, object]:
        if not self.report_path.exists():
            return {}

        try:
            with self.report_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:
            logger.warning("Existing report file %s is invalid JSON. Starting fresh.", self.report_path)
            return {}

    def append_run(self, run_entry: Dict[str, object], thresholds: Dict[str, float]) -> Dict[str, object]:
        existing_data = self.load_report()

        previous_runs = existing_data.get("runs") if isinstance(existing_data.get("runs"), list) else []
        previous_metrics = existing_data.get("metrics") if isinstance(existing_data.get("metrics"), list) else []
        run_metrics = run_entry.get("metrics") if isinstance(run_entry.get("metrics"), list) else []

        report_data = {
            "last_updated": datetime.now().isoformat(),
            "thresholds": thresholds,
            "metrics": previous_metrics + run_metrics,
            "runs": previous_runs + [run_entry],
        }

        with self.report_path.open("w", encoding="utf-8") as handle:
            json.dump(report_data, handle, indent=2, ensure_ascii=False)

        logger.info("Performance report saved to %s (appended %d metrics)", self.report_path, len(run_metrics))
        return report_data
