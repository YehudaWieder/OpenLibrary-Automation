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
        total_metrics = sum(len(run.get("metrics", [])) for run in runs if isinstance(run, dict))
        run_sections = [self._render_run_section(run) for run in reversed(runs) if isinstance(run, dict)]

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

    def _render_run_section(self, run: Dict[str, object]) -> str:
        context = run.get("context", {}) if isinstance(run.get("context"), dict) else {}
        metrics = run.get("metrics", []) if isinstance(run.get("metrics"), list) else []
        thresholds = run.get("thresholds", {}) if isinstance(run.get("thresholds"), dict) else {}
        screenshots = context.get("screenshots", []) if isinstance(context.get("screenshots"), list) else []

        context_rows = "".join(
            f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
            for key, value in context.items()
            if key != "screenshots"
        ) or "<tr><td colspan='2'>No context</td></tr>"

        metric_rows = []
        for metric in metrics:
            if not isinstance(metric, dict):
                continue
            name = metric.get("metric_name", "")
            value = metric.get("value", "")
            threshold = thresholds.get(name)
            if isinstance(value, (int, float)) and isinstance(threshold, (int, float)):
                status = "OK" if value <= threshold else "EXCEEDED"
            else:
                status = "N/A"
            metric_rows.append(
                f"<tr><td>{html.escape(str(name))}</td><td>{html.escape(str(value))}</td>"
                f"<td>{html.escape(str(threshold))}</td><td>{status}</td></tr>"
            )

        metric_rows_html = "".join(metric_rows) or "<tr><td colspan='4'>No metrics</td></tr>"

        screenshot_cards = []
        for image_path in screenshots:
            rel = html.escape(str(Path(str(image_path))))
            screenshot_cards.append(
                f"<div class='shot'><a href='{rel}' target='_blank'><img src='{rel}' alt='screenshot'></a><p>{rel}</p></div>"
            )

        screenshot_html = "".join(screenshot_cards) or "<p>No screenshots found for this run.</p>"

        return """
            <section class='run'>
              <h2>Run {run_id} - {test_name}</h2>
              <p><strong>Started:</strong> {started_at} | <strong>Finished:</strong> {finished_at}</p>
              <h3>Run Context</h3>
              <table>{context_rows}</table>
              <h3>Performance Metrics</h3>
              <table>
                <tr><th>Metric</th><th>Value</th><th>Threshold</th><th>Status</th></tr>
                {metric_rows}
              </table>
              <h3>Screenshots</h3>
              <div class='shots'>{screenshot_cards}</div>
            </section>
        """.format(
            run_id=html.escape(str(run.get("run_id", ""))),
            test_name=html.escape(str(run.get("test_name", "automation_test"))),
            started_at=html.escape(str(run.get("started_at", ""))),
            finished_at=html.escape(str(run.get("finished_at", ""))),
            context_rows=context_rows,
            metric_rows=metric_rows_html,
            screenshot_cards=screenshot_html,
        )
