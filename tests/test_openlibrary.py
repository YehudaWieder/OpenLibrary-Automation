"""
Allure-powered end-to-end test for the OpenLibrary automation suite.
Run with:
    pytest tests/ --alluredir=allure-results -v
Then generate/view the report:
    allure serve allure-results
"""
import json

import allure
import pytest

from config import Config
from pages.book_details_page import BookDetailsPage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.user_books_page import UserBooksPage
from utils.performance.performance_repository import PerformanceRepository
from utils.performance.performance_helper import PerformanceHelper
from utils.reading_list_utils import assert_reading_lists_count
from utils.search_utils import search_books_by_title_under_year


@allure.epic("OpenLibrary Automation")
@allure.feature("Reading List Management")
@allure.story("Add books to reading list and verify count")
@pytest.mark.asyncio
async def test_add_books_to_reading_list(browser_context, perf_helper, test_data):
    page = browser_context

    # ── 1. Login ────────────────────────────────────────────────────────────
    with allure.step("Login to OpenLibrary"):
        login_page = LoginPage(page)
        await login_page.open_login()
        await login_page.login(Config.EMAIL_INPUT, Config.PASSWORD_INPUT)

    # ── 2. Clear existing reading lists ─────────────────────────────────────
    with allure.step("Clear existing reading lists"):
        user_books_page = UserBooksPage(page)
        await user_books_page.clear_reading_lists()

    # ── 3. Search ────────────────────────────────────────────────────────────
    search_query = test_data.get("search_query")
    max_year = test_data.get("max_year")
    limit = test_data.get("limit")

    with allure.step(f"Search books: query='{search_query}', max_year={max_year}, limit={limit}"):
        home_page = HomePage(page)
        book_urls = await search_books_by_title_under_year(
            home_page=home_page,
            query=search_query,
            max_year=max_year,
            limit=limit,
        )

        await perf_helper.measure_page_performance(page, "search_page")

        allure.attach(
            "\n".join(book_urls),
            name="Collected book URLs",
            attachment_type=allure.attachment_type.TEXT,
        )

    assert book_urls, "No books found matching the search criteria"

    # ── 4. Add books to reading list ─────────────────────────────────────────
    with allure.step(f"Add {len(book_urls)} books to reading list"):
        details_page = BookDetailsPage(page)
        for i, url in enumerate(book_urls, start=1):
            with allure.step(f"Book {i}: {url}"):
                await details_page.add_books_to_reading_list(
                    [url],
                    randomize_status=Config.RANDOMIZE_READING_STATUS,
                )
                await perf_helper.measure_page_performance(page, "book_page")

    # ── 5. Verify reading list count ─────────────────────────────────────────
    with allure.step("Verify reading list total count"):
        await user_books_page.open()
        await perf_helper.measure_page_performance(page, "reading_list")

        want_count = await user_books_page.get_want_to_read_count()
        already_count = await user_books_page.get_already_read_count()
        total = await user_books_page.get_reading_list_total()

        allure.attach(
            json.dumps(
                {"want_to_read": want_count, "already_read": already_count, "total": total},
                indent=2,
            ),
            name="Reading list counts",
            attachment_type=allure.attachment_type.JSON,
        )

        await assert_reading_lists_count(
            user_books_page=user_books_page,
            expected_count=len(book_urls),
        )

    # ── 6. Attach performance report ─────────────────────────────────────────
    with allure.step("Save and attach performance report"):
        performance_repo = PerformanceRepository()
        run_entry = perf_helper.build_run_entry(test_name="test_add_books_to_reading_list")
        performance_repo.append_run(run_entry, perf_helper.thresholds)

        with open(performance_repo.report_path, "r", encoding="utf-8") as f:
            report_json = f.read()

        allure.attach(
            report_json,
            name="Performance Report",
            attachment_type=allure.attachment_type.JSON,
        )

        _attach_performance_thresholds_status(perf_helper)


def _attach_performance_thresholds_status(perf_helper: PerformanceHelper) -> None:
    """Attach a summary table of threshold results to Allure."""
    rows = []
    for entry in perf_helper.test_results:
        metric = entry["metric_name"]
        value = entry["value"]
        threshold = perf_helper.thresholds.get(metric)
        status_name = entry.get("status") or perf_helper.classify_metric(value, threshold)[0]
        status = perf_helper.format_metric_status(status_name, value, threshold)
        rows.append(f"{metric}: {status}")

    allure.attach(
        "\n".join(rows) if rows else "No metrics recorded",
        name="Performance Threshold Summary",
        attachment_type=allure.attachment_type.TEXT,
    )
