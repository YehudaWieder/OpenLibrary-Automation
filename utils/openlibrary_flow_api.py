"""Spec-facing flow API with exact function signatures required by the assignment."""

from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import Page

from config import Config
from pages.book_details_page import BookDetailsPage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.user_books_page import UserBooksPage
from utils.performance.performance_helper import PerformanceHelper
from utils.reading_list_utils import assert_reading_lists_count
from utils.search_utils import search_books_by_title_under_year as search_books_by_title_under_year_impl

logger = logging.getLogger(__name__)


@dataclass
class FlowContext:
    page: Page
    perf_helper: Optional[PerformanceHelper] = None
    randomize_reading_status: bool = Config.RANDOMIZE_READING_STATUS


_flow_context: ContextVar[Optional[FlowContext]] = ContextVar("openlibrary_flow_context", default=None)


def configure_flow_context(
    page: Page,
    perf_helper: Optional[PerformanceHelper] = None,
    randomize_reading_status: bool = Config.RANDOMIZE_READING_STATUS,
) -> None:
    """Configure a per-task context used by the spec-facing functions."""
    _flow_context.set(
        FlowContext(
            page=page,
            perf_helper=perf_helper,
            randomize_reading_status=randomize_reading_status,
        )
    )


def clear_flow_context() -> None:
    """Clear the context after a run/test to avoid context leaks."""
    _flow_context.set(None)


def _require_context() -> FlowContext:
    context = _flow_context.get()
    if context is None:
        raise RuntimeError(
            "Flow context is not configured. Call configure_flow_context(page, ...) before using flow API functions."
        )
    return context


def _infer_page_type(url: str) -> str:
    normalized = url.lower()
    if "search" in normalized:
        return "search_page"
    if "/account/books" in normalized:
        return "reading_list"
    return "book_page"


async def search_books_by_title_under_year(query: str, max_year: int, limit: int = 5) -> list[str]:
    """Search books and collect URLs where publication year is <= max_year."""
    context = _require_context()
    home_page = HomePage(context.page)
    return await search_books_by_title_under_year_impl(
        home_page=home_page,
        query=query,
        max_year=max_year,
        limit=limit,
    )


async def add_books_to_reading_list(urls: list[str]) -> None:
    """Add books to reading list using random status selection as configured."""
    context = _require_context()
    details_page = BookDetailsPage(context.page)
    screenshot_paths = await details_page.add_books_to_reading_list(
        urls,
        randomize_status=context.randomize_reading_status,
    )
    if context.perf_helper and screenshot_paths:
        existing_screenshots = context.perf_helper.run_context.get("screenshots", [])
        if not isinstance(existing_screenshots, list):
            existing_screenshots = []
        context.perf_helper.set_run_context(
            screenshots=[*existing_screenshots, *screenshot_paths],
        )


async def prepare_authenticated_session() -> None:
    """Log in using configured credentials for the active flow context."""
    context = _require_context()
    login_page = LoginPage(context.page)
    await login_page.open_login()
    await login_page.login(Config.EMAIL_INPUT, Config.PASSWORD_INPUT)


async def reset_reading_lists() -> None:
    """Clear existing reading lists before running the scenario."""
    context = _require_context()
    user_books_page = UserBooksPage(context.page)
    await user_books_page.clear_reading_lists()


async def assert_reading_list_count(expected_count: int) -> None:
    """Assert that the combined reading list count equals expected_count."""
    context = _require_context()
    user_books_page = UserBooksPage(context.page)
    await user_books_page.open()
    actual_count = await user_books_page.get_reading_list_total()
    if context.perf_helper:
        context.perf_helper.set_run_context(
            expected_count=expected_count,
            actual_count=actual_count,
        )
    await assert_reading_lists_count(
        user_books_page=user_books_page,
        expected_count=expected_count,
    )


async def measure_page_performance(page: Page, url: str, threshold_ms: int) -> dict:
    """Measure page timing metrics and warn when they exceed threshold_ms."""
    context = _flow_context.get()
    helper = context.perf_helper if context and context.perf_helper else PerformanceHelper()

    await page.wait_for_load_state("load")

    metrics = {
        "first_paint_ms": helper.normalize_metric_value(await helper.get_first_paint_time(page)),
        "dom_content_loaded_ms": helper.normalize_metric_value(
            await helper.get_dom_content_loaded_time(page)
        ),
        "load_time_ms": helper.normalize_metric_value(await helper.get_load_time(page)),
    }

    for metric_name, value in metrics.items():
        if value is not None and value > threshold_ms:
            logger.warning(
                "Performance threshold exceeded for %s on %s: %sms > %sms",
                metric_name,
                url,
                value,
                threshold_ms,
            )

    if context and context.perf_helper:
        page_type = _infer_page_type(url)
        for metric_name, value in metrics.items():
            full_metric_name = f"{page_type}_{metric_name}"
            context.perf_helper.record_test_metric(page_type, full_metric_name, value)

    return metrics
