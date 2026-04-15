"""Lifecycle helpers for run status and report persistence."""

import logging
from dataclasses import dataclass

from utils.performance.performance_helper import PerformanceHelper
from utils.performance.performance_repository import PerformanceRepository
from utils.performance.performance_html_report import PerformanceHtmlReportBuilder
from utils.performance.report_opener import ReportOpener

logger = logging.getLogger(__name__)


@dataclass
class RunLifecycleState:
    """Mutable lifecycle state used across one test run."""

    run_failed: bool = False
    run_completed_successfully: bool = False


def create_run_state() -> RunLifecycleState:
    """Create a fresh lifecycle state container for a run."""
    return RunLifecycleState()


def mark_run_success(state: RunLifecycleState) -> None:
    """Mark that the flow finished all business steps successfully."""
    state.run_completed_successfully = True


def mark_run_failed(state: RunLifecycleState, perf_helper: PerformanceHelper, reason: str) -> None:
    """Mark current run as failed and store failure details in context."""
    state.run_failed = True
    perf_helper.set_run_context(run_status="FAILED", failure_details=reason)


def finalize_run_context(
    state: RunLifecycleState,
    perf_helper: PerformanceHelper,
) -> None:
    """Finalize run status before persisting report."""
    if state.run_completed_successfully and not state.run_failed:
        perf_helper.set_run_context(run_status="PASSED", failure_details="")
        return
    if not state.run_failed:
        mark_run_failed(state, perf_helper, "Run ended before completion")


def persist_and_publish_report(
    perf_helper: PerformanceHelper,
    performance_repo: PerformanceRepository,
    html_report_builder: PerformanceHtmlReportBuilder,
    report_opener: ReportOpener,
) -> None:
    """Append run to repository and regenerate/open HTML report."""
    run_entry = perf_helper.build_run_entry(test_name="automation_test")
    report_data = performance_repo.append_run(run_entry, perf_helper.thresholds)
    try:
        html_path = html_report_builder.generate_from_report_data(report_data)
        report_opener.open_file(html_path)
    except Exception as report_error:
        logger.warning("Could not open HTML report automatically: %s", report_error)
