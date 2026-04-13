"""Performance measurement helper for automation tests."""

import html
import json
import logging
import webbrowser
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from playwright.async_api import Page
from config import Config

logger = logging.getLogger(__name__)


class PerformanceHelper:
    """
    Helper class for measuring and reporting page performance metrics.
    
    Implements Single Responsibility Principle - handles performance measurement only.
    Measures metrics like first paint, DOM content loaded, and load time.
    """

    current_instance: Optional['PerformanceHelper'] = None
    DEFAULT_TEMPLATE_PATH = Path("templates/performance_report_template.html")

    def __init__(self, report_path: str = "performance_report.json") -> None:
        """
        Initialize performance helper.
        
        Args:
            report_path: Path to save performance report
        """
        self.report_path: str = report_path
        self.test_results: list = []
        self.run_context: Dict[str, object] = {}
        self.run_started_at: str = datetime.now().isoformat()
        self.thresholds: Dict[str, float] = Config.PERFORMANCE_THRESHOLDS
        if not isinstance(self.thresholds, dict):
            logger.error(f"Invalid thresholds type: {type(self.thresholds)}, value: {self.thresholds}, using empty dict")
            self.thresholds = {}
        PerformanceHelper.current_instance = self

    def set_run_context(self, **kwargs: object) -> None:
        """Set arbitrary context values for the current run."""
        self.run_context.update(kwargs)

    async def get_first_paint_time(self, page: Page) -> float:
        """
        Get first paint time from page performance API.
        
        Args:
            page: Playwright page instance
            
        Returns:
            First paint time in milliseconds
        """
        return await page.evaluate("""() => {
            const entries = performance.getEntriesByType('paint');
            const firstPaint = entries.find(entry => entry.name === 'first-paint');
            return firstPaint ? firstPaint.startTime : 0;
        }""")

    async def get_dom_content_loaded_time(self, page: Page) -> float:
        """
        Get DOM content loaded time from performance API.
        
        Args:
            page: Playwright page instance
            
        Returns:
            DOM content loaded time in milliseconds
        """
        return await page.evaluate("""() => {
            const timing = performance.timing;
            return timing.domContentLoadedEventEnd - timing.navigationStart;
        }""")

    async def get_load_time(self, page: Page) -> float:
        """
        Get page load time from performance API.
        
        Args:
            page: Playwright page instance
            
        Returns:
            Page load time in milliseconds
        """
        return await page.evaluate("""() => {
            const timing = performance.timing;
            return timing.loadEventEnd - timing.navigationStart;
        }""")

    async def measure_page_performance(self, page: Page, page_type: str) -> Dict[str, float]:
        """
        Measure all performance metrics for a page.
        
        Args:
            page: Playwright page instance
            page_type: Type of page (search, book, reading_list)
            
        Returns:
            Dictionary with performance metrics
        """
        first_paint_ms = await self.get_first_paint_time(page)
        dom_content_loaded_ms = await self.get_dom_content_loaded_time(page)
        load_time_ms = await self.get_load_time(page)
        
        metrics = {
            'first_paint_ms': first_paint_ms,
            'dom_content_loaded_ms': dom_content_loaded_ms,
            'load_time_ms': load_time_ms
        }
        
        # Record metrics
        for metric_name, value in metrics.items():
            full_metric_name = f"{page_type}_{metric_name}"
            self.record_test_metric(page_type, full_metric_name, value)
        
        return metrics

    def record_test_metric(
        self, 
        test_name: str, 
        metric_name: str, 
        value: float
    ) -> None:
        """
        Record a performance metric for a test.
        
        Args:
            test_name: Name of the test
            metric_name: Name of the metric
            value: Metric value
        """
        self.test_results.append({
            "test_name": test_name,
            "metric_name": metric_name,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
        
        # Check threshold and log warning if exceeded
        if (isinstance(self.thresholds, dict) and 
            metric_name in self.thresholds and 
            isinstance(value, (int, float)) and 
            isinstance(self.thresholds[metric_name], (int, float)) and
            value > self.thresholds[metric_name]):
            logger.warning(f"Performance threshold exceeded for {metric_name}: {value:.2f}ms > {self.thresholds[metric_name]}ms")

    async def save_performance_report(self, test_name: Optional[str] = None) -> None:
        """
        Save performance metrics to JSON report file.
        
        Args:
            test_name: Optional specific test name to include in report
        """
        report_path = self.report_path
        existing_data = {}

        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            existing_data = {}
        except json.JSONDecodeError:
            logger.warning(f"Existing report file {report_path} is invalid JSON. Overwriting with new report.")
            existing_data = {}

        previous_metrics = existing_data.get("metrics") if isinstance(existing_data.get("metrics"), list) else []
        combined_metrics = previous_metrics + self.test_results
        previous_runs = existing_data.get("runs") if isinstance(existing_data.get("runs"), list) else []

        run_entry = {
            "run_id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "started_at": self.run_started_at,
            "finished_at": datetime.now().isoformat(),
            "test_name": test_name or "automation_test",
            "context": self.run_context,
            "thresholds": self.thresholds,
            "metrics": self.test_results,
        }

        report_data = {
            "last_updated": datetime.now().isoformat(),
            "thresholds": self.thresholds,
            "metrics": combined_metrics,
            "runs": previous_runs + [run_entry],
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Performance report saved to {report_path} (appended %d metrics)", len(self.test_results))

    def generate_html_report(
        self,
        html_path: str = "performance_report.html",
        template_path: Optional[str] = None,
    ) -> str:
        """Generate an HTML report from JSON history and return the HTML file path."""
        report_path = Path(self.report_path)
        output_path = Path(html_path)
        template_file = Path(template_path) if template_path else self.DEFAULT_TEMPLATE_PATH

        if not report_path.exists():
            raise FileNotFoundError(f"Performance report JSON not found: {report_path}")

        with report_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        runs = data.get("runs", []) if isinstance(data.get("runs"), list) else []
        total_metrics = sum(len(run.get("metrics", [])) for run in runs)

        run_sections = []
        for run in reversed(runs):
            context = run.get("context", {}) if isinstance(run.get("context"), dict) else {}
            metrics = run.get("metrics", []) if isinstance(run.get("metrics"), list) else []
            screenshots = context.get("screenshots", []) if isinstance(context.get("screenshots"), list) else []

            context_rows = "".join(
                f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
                for key, value in context.items()
                if key != "screenshots"
            )

            metric_rows = []
            for metric in metrics:
                name = metric.get("metric_name", "")
                value = metric.get("value", "")
                threshold = run.get("thresholds", {}).get(name) if isinstance(run.get("thresholds"), dict) else None
                if isinstance(value, (int, float)) and isinstance(threshold, (int, float)):
                    status = "OK" if value <= threshold else "EXCEEDED"
                else:
                    status = "N/A"
                metric_rows.append(
                    f"<tr><td>{html.escape(str(name))}</td><td>{html.escape(str(value))}</td>"
                    f"<td>{html.escape(str(threshold))}</td><td>{status}</td></tr>"
                )

            screenshot_cards = []
            for image_path in screenshots:
                rel = html.escape(str(Path(image_path)))
                screenshot_cards.append(
                    f"<div class='shot'><a href='{rel}' target='_blank'><img src='{rel}' alt='screenshot'></a><p>{rel}</p></div>"
                )

            run_sections.append(
                """
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
                    context_rows=context_rows or "<tr><td colspan='2'>No context</td></tr>",
                    metric_rows="".join(metric_rows) or "<tr><td colspan='4'>No metrics</td></tr>",
                    screenshot_cards="".join(screenshot_cards) or "<p>No screenshots found for this run.</p>",
                )
            )

        if not template_file.exists():
            raise FileNotFoundError(f"HTML template not found: {template_file}")

        with template_file.open("r", encoding="utf-8") as handle:
            template = handle.read()

        page_html = (
            template.replace("{{LAST_UPDATED}}", html.escape(str(data.get("last_updated", ""))))
            .replace("{{TOTAL_RUNS}}", str(len(runs)))
            .replace("{{TOTAL_METRICS}}", str(total_metrics))
            .replace("{{RUN_SECTIONS}}", "".join(run_sections) or "<p>No runs found.</p>")
        )

        with output_path.open("w", encoding="utf-8") as handle:
            handle.write(page_html)

        logger.info("HTML report generated at %s", output_path)
        return str(output_path)

    def open_html_report(self, html_path: str = "performance_report.html") -> None:
        """Open HTML report in the default browser."""
        target = Path(html_path).resolve()
        webbrowser.open(target.as_uri())
