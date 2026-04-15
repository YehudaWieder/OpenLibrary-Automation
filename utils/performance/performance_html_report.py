"""HTML renderer for performance run history."""

import html
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from utils.performance.performance_helper import PerformanceHelper

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
            template.replace("{{LAST_UPDATED}}", html.escape(self._format_datetime(report_data.get("last_updated"))))
            .replace("{{TOTAL_RUNS}}", str(len(runs)))
            .replace("{{TOTAL_METRICS}}", str(total_metrics))
            .replace("{{RUN_SECTIONS}}", "".join(run_sections) or "<p>No runs found.</p>")
        )

        with self.html_output_path.open("w", encoding="utf-8") as handle:
            handle.write(page_html)

        logger.info("HTML report generated at %s", self.html_output_path)
        return str(self.html_output_path)

    @staticmethod
    def _format_datetime(value: object) -> str:
        """Format ISO date values to a readable local timestamp."""
        if not value:
            return "—"

        raw = str(value).strip()
        if not raw:
            return "—"

        candidate = raw.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(candidate)
            return dt.strftime("%d %b %Y, %H:%M:%S")
        except ValueError:
            return raw

    def _render_run_section(self, run: Dict[str, object], run_num: int) -> str:
        context = run.get("context", {}) if isinstance(run.get("context"), dict) else {}
        metrics = run.get("metrics", []) if isinstance(run.get("metrics"), list) else []
        thresholds = run.get("thresholds", {}) if isinstance(run.get("thresholds"), dict) else {}
        screenshots = context.get("screenshots", []) if isinstance(context.get("screenshots"), list) else []
        added_urls = context.get("added_book_urls") if isinstance(context.get("added_book_urls"), list) else []
        requested_urls = (
            context.get("requested_book_urls")
            if isinstance(context.get("requested_book_urls"), list)
            else []
        )
        urls_to_render = requested_urls or added_urls

        run_status_raw = str(context.get("run_status") or run.get("run_status") or "PASSED").upper()
        run_status = "FAILED" if run_status_raw == "FAILED" else "PASSED"
        failure_details = context.get("failure_details")
        has_failure_details = run_status == "FAILED" and bool(failure_details)

        expected_count = context.get("expected_count")
        requested_books_count = context.get("requested_books_count")
        added_books_count = context.get("added_books_count")

        filtered_context: Dict[str, object] = {}
        for key, value in context.items():
            if key in {
                "screenshots",
                "added_book_urls",
                "requested_book_urls",
                "requested_books_count",
                "failure_details",
                "run_status",
            }:
                continue
            # Avoid duplicate count presentation when both represent the same number.
            if key == "added_books_count" and expected_count is not None and value == expected_count:
                continue
            if key == "added_books_count" and isinstance(added_urls, list) and value == len(added_urls):
                continue
            filtered_context[key] = value

        urls_html = ""
        if urls_to_render:
            urls_items = "".join(
                f"<li><a href='{html.escape(str(url))}' target='_blank' rel='noopener noreferrer'>{html.escape(str(url))}</a></li>"
                for url in urls_to_render
            )
            urls_html = (
                "<div class='section-label'>Book URLs</div>"
                "<div class='urls-panel'><ol class='urls-list'>"
                f"{urls_items}"
                "</ol></div>"
            )

        # Context chips
        ctx_items = "".join(
            f"<div class='ctx-item'>"
            f"<div class='ctx-key'>{html.escape(str(k))}</div>"
            f"<div class='ctx-val'>{html.escape(str(v))}</div>"
            f"</div>"
            for k, v in filtered_context.items()
        ) or "<div class='ctx-item'><div class='ctx-val' style='color:#94a3b8'>No context</div></div>"

        # Metric rows with progress bars
        metric_rows: List[str] = []
        for metric in metrics:
            if not isinstance(metric, dict):
                continue
            name = metric.get("metric_name", "")
            value = metric.get("value", "")
            threshold = thresholds.get(name)
            status = str(metric.get("status") or PerformanceHelper.classify_metric(value, threshold)[0])

            if PerformanceHelper.is_valid_metric_value(value) and isinstance(threshold, (int, float)):
                threshold_display = str(threshold)
                data_attrs = f"data-value='{value}' data-threshold='{threshold}'"
            else:
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

        failure_html = ""
        if has_failure_details:
            failure_html = (
                "<div class='section-label'>Failure Details</div>"
                "<div class='failure-box'>"
                f"<pre>{html.escape(str(failure_details))}</pre>"
                "</div>"
            )

        status_class = "run-result-failed" if run_status == "FAILED" else "run-result-passed"
        status_text = "FAILED" if run_status == "FAILED" else "PASSED"

        return (
            f"<article class='run'>"
            f"<div class='run-header'>"
            f"<div class='run-badge'>#{run_num}</div>"
            f"<div class='run-meta'>"
            f"<div class='run-title'>{html.escape(str(run.get('test_name', 'automation_test')))}</div>"
            f"<div class='run-ts'>"
            f"<span>&#9654; {html.escape(self._format_datetime(run.get('started_at')))}</span>"
            f"<span>&#9632; {html.escape(self._format_datetime(run.get('finished_at')))}</span>"
            f"</div>"
            f"</div>"
            f"<div class='run-result {status_class}'>{status_text}</div>"
            f"<div class='run-pills'></div>"
            f"<div class='run-toggle'>&#9660;</div>"
            f"</div>"
            f"<div class='run-body'>"
            f"{urls_html}"
            f"<div class='section-label'>Context</div>"
            f"<div class='ctx-grid'>{ctx_items}</div>"
            f"{failure_html}"
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
