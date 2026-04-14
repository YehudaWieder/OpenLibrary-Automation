"""Performance measurement helper for automation tests."""

import logging
from typing import Dict, Optional
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
