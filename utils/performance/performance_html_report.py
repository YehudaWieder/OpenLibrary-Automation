"""HTML renderer for performance run history."""

import html
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PerformanceHtmlReportBuilder:
    """Single responsibility: render HTML report from performance JSON data."""

    def __init__(
        self,
        template_path: str = "templates/performance_report_template.html",
        html_output_path: str = "performance_report.html",
    ) -> None:
        self.template_path = Path(template_path)
        self.html_output_path = Path(html_output_path)

    def generate_from_report_data(self, report_data: Dict[str, object]) -> str:
        runs = report_data.get("runs", []) if isinstance(report_data.get("runs"), list) else []
        valid_runs = [r for r in runs if isinstance(r, dict)]
        total_metrics = sum(len(run.get("metrics", [])) for run in valid_runs)
        reversed_runs = list(reversed(valid_runs))
        run_sections = [
            self._render_run_section(run, i + 1)
            for i, run in enumerate(reversed_runs)
        ]

        if not self.template_path.exists():
            raise FileNotFoundError(f"HTML template not found: {self.template_path}")

        with self.template_path.open("r", encoding="utf-8") as handle:
            template = handle.read()

        page_html = (
            template.replace("{{LAST_UPDATED}}", html.escape(str(report_data.get("last_updated", ""))))
            .replace("{{TOTAL_RUNS}}", str(len(runs)))
            .replace("{{TOTAL_METRICS}}", str(total_metrics))
            .replace("{{RUN_SECTIONS}}", "".join(run_sections) or "<p>No runs found.</p>")
        )

        with self.html_output_path.open("w", encoding="utf-8") as handle:
            handle.write(page_html)

        logger.info("HTML report generated at %s", self.html_output_path)
        return str(self.html_output_path)

    def _render_run_section(self, run: Dict[str, object], run_num: int) -> str:
        context = run.get("context", {}) if isinstance(run.get("context"), dict) else {}
        metrics = run.get("metrics", []) if isinstance(run.get("metrics"), list) else []
        thresholds = run.get("thresholds", {}) if isinstance(run.get("thresholds"), dict) else {}
        screenshots = context.get("screenshots", []) if isinstance(context.get("screenshots"), list) else []

        # Context chips
        ctx_items = "".join(
            f"<div class='ctx-item'>"
            f"<div class='ctx-key'>{html.escape(str(k))}</div>"
            f"<div class='ctx-val'>{html.escape(str(v))}</div>"
            f"</div>"
            for k, v in context.items()
            if k != "screenshots"
        ) or "<div class='ctx-item'><div class='ctx-val' style='color:#94a3b8'>No context</div></div>"

        # Metric rows with progress bars
        metric_rows: List[str] = []
        for metric in metrics:
            if not isinstance(metric, dict):
                continue
            name = metric.get("metric_name", "")
            value = metric.get("value", "")
            threshold = thresholds.get(name)

            if isinstance(value, (int, float)) and isinstance(threshold, (int, float)):
                status = "OK" if value <= threshold else "EXCEEDED"
                threshold_display = str(threshold)
                data_attrs = f"data-value='{value}' data-threshold='{threshold}'"
            else:
                status = "N/A"
                threshold_display = str(threshold) if threshold is not None else "—"
                data_attrs = ""

            metric_rows.append(
                f"<tr class='metric-row' {data_attrs}>"
                f"<td><span class='metric-name'>{html.escape(str(name))}</span></td>"
                f"<td><div class='metric-val-wrap'>"
                f"<span class='metric-val'>{html.escape(str(value))}</span>"
                f"<div class='metric-bar-track'><div class='metric-bar-fill'></div></div>"
                f"</div></td>"
                f"<td>{html.escape(threshold_display)}</td>"
                f"<td class='status-cell'>{status}</td>"
                f"</tr>"
            )

        metric_rows_html = "".join(metric_rows) or (
            "<tr><td colspan='4' style='text-align:center;color:#94a3b8;padding:18px 14px'>"
            "No metrics recorded</td></tr>"
        )

        # Screenshot cards
        screenshot_cards: List[str] = []
        for image_path in screenshots:
            rel = html.escape(str(Path(str(image_path))))
            name_only = html.escape(Path(str(image_path)).name)
            screenshot_cards.append(
                f"<div class='shot'>"
                f"<a href='{rel}' target='_blank'>"
                f"<img src='{rel}' alt='screenshot' loading='lazy'>"
                f"</a>"
                f"<div class='shot-caption'>{name_only}</div>"
                f"</div>"
            )

        screenshot_html = "".join(screenshot_cards) or (
            "<p style='color:#94a3b8;font-size:0.84rem'>No screenshots for this run.</p>"
        )

        return (
            f"<article class='run'>"
            f"<div class='run-header'>"
            f"<div class='run-badge'>#{run_num}</div>"
            f"<div class='run-meta'>"
            f"<div class='run-title'>{html.escape(str(run.get('test_name', 'automation_test')))}</div>"
            f"<div class='run-ts'>"
            f"<span>&#9654; {html.escape(str(run.get('started_at', '')))}</span>"
            f"<span>&#9632; {html.escape(str(run.get('finished_at', '')))}</span>"
            f"</div>"
            f"</div>"
            f"<div class='run-pills'></div>"
            f"<div class='run-toggle'>&#9660;</div>"
            f"</div>"
            f"<div class='run-body'>"
            f"<div class='section-label'>Context</div>"
            f"<div class='ctx-grid'>{ctx_items}</div>"
            f"<div class='section-label'>Performance Metrics</div>"
            f"<div class='metrics-wrap'>"
            f"<table>"
            f"<thead><tr>"
            f"<th>Metric</th><th>Value (ms)</th><th>Threshold</th><th>Status</th>"
            f"</tr></thead>"
            f"<tbody>{metric_rows_html}</tbody>"
            f"</table>"
            f"</div>"
            f"<div class='section-label'>Screenshots</div>"
            f"<div class='shots'>{screenshot_html}</div>"
            f"</div>"
            f"</article>"
        )
