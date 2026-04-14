import logging
from pathlib import Path

import pytest

from utils.performance.performance_helper import PerformanceHelper
from utils.performance.performance_html_report import PerformanceHtmlReportBuilder


class FakePerformancePage:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.waited_states: list[str] = []

    async def wait_for_load_state(self, state: str) -> None:
        self.waited_states.append(state)

    async def evaluate(self, script: str, arg: str | None = None) -> object:
        return self.responses.pop(0)


def test_record_test_metric_marks_negative_value_invalid(caplog: pytest.LogCaptureFixture) -> None:
    helper = PerformanceHelper()
    helper.thresholds = {"search_page_load_time_ms": 3000}

    with caplog.at_level(logging.WARNING):
        helper.record_test_metric("search_page", "search_page_load_time_ms", -1.77e12)

    assert helper.test_results[0]["status"] == "INVALID"
    assert "Invalid performance metric recorded for search_page_load_time_ms" in caplog.text


@pytest.mark.asyncio
async def test_measure_page_performance_records_invalid_missing_navigation_metrics() -> None:
    helper = PerformanceHelper()
    helper.thresholds = {
        "search_page_first_paint_ms": 3000,
        "search_page_dom_content_loaded_ms": 3000,
        "search_page_load_time_ms": 3000,
    }
    page = FakePerformancePage([125.0, None, None])

    metrics = await helper.measure_page_performance(page, "search_page")

    assert page.waited_states == ["load"]
    assert metrics == {
        "first_paint_ms": 125,
        "dom_content_loaded_ms": None,
        "load_time_ms": None,
    }
    assert [entry["status"] for entry in helper.test_results] == ["OK", "INVALID", "INVALID"]


def test_html_report_marks_invalid_metric(tmp_path: Path) -> None:
    template_path = tmp_path / "template.html"
    output_path = tmp_path / "report.html"
    template_path.write_text(
        "{{LAST_UPDATED}}|{{TOTAL_RUNS}}|{{TOTAL_METRICS}}|{{RUN_SECTIONS}}",
        encoding="utf-8",
    )

    builder = PerformanceHtmlReportBuilder(
        template_path=str(template_path),
        html_output_path=str(output_path),
    )
    builder.generate_from_report_data(
        {
            "last_updated": "2026-04-14T00:00:00",
            "runs": [
                {
                    "test_name": "demo",
                    "started_at": "2026-04-14T00:00:00",
                    "finished_at": "2026-04-14T00:01:00",
                    "context": {},
                    "thresholds": {"search_page_load_time_ms": 3000},
                    "metrics": [
                        {
                            "metric_name": "search_page_load_time_ms",
                            "value": -1.77e12,
                            "status": "INVALID",
                        }
                    ],
                }
            ],
        }
    )

    html_output = output_path.read_text(encoding="utf-8")
    assert "INVALID" in html_output