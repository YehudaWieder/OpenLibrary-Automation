"""Performance measurement helper for automation tests."""

import math
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from playwright.async_api import Page
from config import Config

logger = logging.getLogger(__name__)


class PerformanceHelper:
    """
    Helper class for measuring and reporting page performance metrics.

    Single responsibility: collect and validate performance measurements
    in memory for the current run.
    """

    def __init__(self) -> None:
        """
        Initialize performance collector for current run.
        """
        self.test_results: list = []
        self.run_context: Dict[str, object] = {}
        self.run_started_at: str = datetime.now().isoformat()
        self.thresholds: Dict[str, float] = Config.PERFORMANCE_THRESHOLDS
        if not isinstance(self.thresholds, dict):
            logger.error(f"Invalid thresholds type: {type(self.thresholds)}, value: {self.thresholds}, using empty dict")
            self.thresholds = {}

    def set_run_context(self, **kwargs: object) -> None:
        """Set arbitrary context values for the current run."""
        self.run_context.update(kwargs)

    @staticmethod
    def is_valid_metric_value(value: object) -> bool:
        """Return whether a performance metric value is finite and non-negative."""
        return isinstance(value, (int, float)) and math.isfinite(value) and value >= 0

    @classmethod
    def normalize_metric_value(cls, value: object) -> Optional[int]:
        """Normalize a metric value to integer milliseconds for storage/reporting."""
        if not cls.is_valid_metric_value(value):
            return None
        return int(round(float(value)))

    @classmethod
    def classify_metric(cls, value: object, threshold: object) -> Tuple[str, Optional[str]]:
        """Classify a metric value for logging and report rendering."""
        normalized_value = cls.normalize_metric_value(value)
        if normalized_value is None:
            return "INVALID", None
        if not isinstance(threshold, (int, float)):
            return "N/A", None
        if normalized_value > threshold:
            return "EXCEEDED", f"{normalized_value}ms > {threshold}ms"
        return "OK", f"{normalized_value}ms <= {threshold}ms"

    @staticmethod
    def format_metric_status(status: str, value: object, threshold: object) -> str:
        """Build a human-readable metric status string."""
        if status == "INVALID":
            return f"INVALID ({value})"
        if status == "EXCEEDED" and isinstance(threshold, (int, float)):
            return f"⚠ EXCEEDED ({value:.0f}ms > {threshold}ms)"
        if status == "OK" and isinstance(value, (int, float)):
            return f"✓ OK ({value:.0f}ms)"
        return "—"

    async def _get_navigation_timing_metric(self, page: Page, metric_name: str) -> Optional[float]:
        """Read a navigation timing metric from Navigation Timing Level 2 entries."""
        value = await page.evaluate(
            """(name) => {
                const navigationEntry = performance.getEntriesByType('navigation')[0];
                if (!navigationEntry || typeof navigationEntry[name] !== 'number') {
                    return null;
                }
                const navigationValue = navigationEntry[name];
                return Number.isFinite(navigationValue) && navigationValue > 0 ? navigationValue : null;
            }""",
            metric_name,
        )
        return float(value) if self.is_valid_metric_value(value) else None

    async def get_first_paint_time(self, page: Page) -> Optional[float]:
        """
        Get first paint time from page performance API.
        
        Args:
            page: Playwright page instance
            
        Returns:
            First paint time in milliseconds
        """
        value = await page.evaluate("""() => {
            const entries = performance.getEntriesByType('paint');
            const firstPaint = entries.find(entry => entry.name === 'first-paint');
            // A 0ms first-paint is treated as missing/invalid in this project.
            return firstPaint && Number.isFinite(firstPaint.startTime) && firstPaint.startTime > 0
                ? firstPaint.startTime
                : null;
        }""")
        if not self.is_valid_metric_value(value):
            return None
        first_paint = float(value)
        return first_paint if first_paint > 0 else None

    async def get_dom_content_loaded_time(self, page: Page) -> Optional[float]:
        """
        Get DOM content loaded time from performance API.
        
        Args:
            page: Playwright page instance
            
        Returns:
            DOM content loaded time in milliseconds
        """
        return await self._get_navigation_timing_metric(page, "domContentLoadedEventEnd")

    async def get_load_time(self, page: Page) -> Optional[float]:
        """
        Get page load time from performance API.
        
        Args:
            page: Playwright page instance
            
        Returns:
            Page load time in milliseconds
        """
        return await self._get_navigation_timing_metric(page, "loadEventEnd")

    async def measure_page_performance(self, page: Page, page_type: str) -> Dict[str, Optional[int]]:
        """
        Measure all performance metrics for a page.
        
        Args:
            page: Playwright page instance
            page_type: Type of page (search, book, reading_list)
            
        Returns:
            Dictionary with performance metrics
        """
        await page.wait_for_load_state("load")

        first_paint_ms = await self.get_first_paint_time(page)
        dom_content_loaded_ms = await self.get_dom_content_loaded_time(page)
        load_time_ms = await self.get_load_time(page)
        
        metrics = {
            'first_paint_ms': self.normalize_metric_value(first_paint_ms),
            'dom_content_loaded_ms': self.normalize_metric_value(dom_content_loaded_ms),
            'load_time_ms': self.normalize_metric_value(load_time_ms)
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
        value: Optional[int]
    ) -> None:
        """
        Record a performance metric for a test.
        
        Args:
            test_name: Name of the test
            metric_name: Name of the metric
            value: Metric value
        """
        threshold = self.thresholds.get(metric_name) if isinstance(self.thresholds, dict) else None
        status, details = self.classify_metric(value, threshold)

        self.test_results.append({
            "test_name": test_name,
            "metric_name": metric_name,
            "value": value,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })

        if status == "INVALID":
            logger.warning("Invalid performance metric recorded for %s: %s", metric_name, value)
        elif status == "EXCEEDED":
            logger.warning("Performance threshold exceeded for %s: %s", metric_name, details)

    def build_run_entry(self, test_name: Optional[str] = None) -> Dict[str, object]:
        """Build an immutable run payload to persist in repository layer."""
        return {
            "run_id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "started_at": self.run_started_at,
            "finished_at": datetime.now().isoformat(),
            "test_name": test_name or "automation_test",
            "context": self.run_context.copy(),
            "thresholds": self.thresholds.copy(),
            "metrics": list(self.test_results),
        }
