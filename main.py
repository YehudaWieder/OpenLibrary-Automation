# main.py
import asyncio
import logging
from pathlib import Path
from playwright.async_api import async_playwright

# Imports from your pages
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.user_books_page import UserBooksPage
from utils.data_loader import load_test_data
from utils.search_utils import search_books_by_title_under_year
from utils.reading_list_utils import assert_reading_lists_count
from utils.performance.performance_repository import PerformanceRepository
from utils.performance.performance_html_report import PerformanceHtmlReportBuilder
from utils.performance.report_opener import ReportOpener
from utils.performance.performance_helper import PerformanceHelper
from config import Config

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MainRunner")


def _collect_latest_screenshots_for_urls(urls: list[str]) -> list[str]:
    """Collect the latest screenshot path for each added book URL."""
    screenshots_dir = Path("screenshots")
    if not screenshots_dir.exists():
        return []

    collected: list[str] = []
    for url in urls:
        book_id = url.rstrip("/").split("/")[-1]
        matches = list(screenshots_dir.glob(f"*_book_{book_id}.png"))
        if not matches:
            continue
        latest = max(matches, key=lambda p: p.stat().st_mtime)
        collected.append(str(latest))
    return collected

async def run_test():
    perf_helper = PerformanceHelper()
    performance_repo = PerformanceRepository()
    html_report_builder = PerformanceHtmlReportBuilder()
    report_opener = ReportOpener()
    
    async with async_playwright() as p:
        # 1. Setup Browser
        logger.info(f"Launching {Config.BROWSER}...")
        
        browser_launcher = getattr(p, Config.BROWSER)
        browser = await browser_launcher.launch(headless=Config.HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 2. Login Phase
            login_page = LoginPage(page)
            await login_page.open_login()
            await login_page.login(Config.EMAIL_INPUT, Config.PASSWORD_INPUT)

            # Clear existing reading lists to prevent toggle issues
            user_books_page = UserBooksPage(page)
            await user_books_page.clear_reading_lists()

            # 3. Search Phase (Task #1)
            test_data = load_test_data(Config.TEST_DATA_PATH)
            search_query = test_data.get("search_query")
            max_year = test_data.get("max_year")
            limit = test_data.get("limit")
            perf_helper.set_run_context(
                search_query=search_query,
                max_year=max_year,
                limit=limit,
            )

            home_page = HomePage(page)
            book_urls = await search_books_by_title_under_year(
                home_page=home_page,
                query=search_query,
                max_year=max_year,
                limit=limit,
            )
            await perf_helper.measure_page_performance(page, "search_page")

            if not book_urls:
                logger.error("No books found matching criteria. Stopping test.")
                return

            # 4. Action Phase: Add to Reading List (Task #2)
            # We already have book_urls. Now we visit each one.
            from pages.book_details_page import BookDetailsPage
            details_page = BookDetailsPage(page)
            
            await details_page.add_books_to_reading_list(book_urls)                
            perf_helper.set_run_context(
                added_book_urls=book_urls,
                added_books_count=len(book_urls),
                screenshots=_collect_latest_screenshots_for_urls(book_urls),
            )

            # 5. Assertion Phase (Task #3)
            user_books_page = UserBooksPage(page)
            await user_books_page.open()
            await perf_helper.measure_page_performance(page, "reading_list")
            actual_count = await assert_reading_lists_count(
                user_books_page=user_books_page,
                expected_count=len(book_urls),
            )
            perf_helper.set_run_context(
                expected_count=len(book_urls),
                actual_count=actual_count,
            )

            logger.info("TEST PASSED: Books successfully added to reading list.")

        except Exception as e:
            logger.error(f"An error occurred during execution: {e}")
        
        finally:
            run_entry = perf_helper.build_run_entry(test_name="automation_test")
            report_data = performance_repo.append_run(run_entry, perf_helper.thresholds)
            try:
                html_path = html_report_builder.generate_from_report_data(report_data)
                report_opener.open_file(html_path)
            except Exception as report_error:
                logger.warning("Could not open HTML report automatically: %s", report_error)
            logger.info("Closing browser.")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())