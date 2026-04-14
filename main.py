# main.py
import asyncio
import logging
from playwright.async_api import async_playwright

# Imports from your pages
from pages.login_page import LoginPage, LoginFailedError
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

async def run_test():
    perf_helper = PerformanceHelper()
    performance_repo = PerformanceRepository()
    html_report_builder = PerformanceHtmlReportBuilder()
    report_opener = ReportOpener()
    should_persist_report = False
    
    async with async_playwright() as p:
        # Setup Browser
        logger.info(f"Launching {Config.BROWSER}...")
        
        browser_launcher = getattr(p, Config.BROWSER)
        browser = await browser_launcher.launch(headless=Config.HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Login Phase
            login_page = LoginPage(page)
            await login_page.open_login()
            await login_page.login(Config.EMAIL_INPUT, Config.PASSWORD_INPUT)
            should_persist_report = True

            # Clear existing reading lists to prevent toggle issues
            user_books_page = UserBooksPage(page)
            await user_books_page.clear_reading_lists()

            # Load Test Data Phase
            test_data = load_test_data(Config.TEST_DATA_PATH)
            search_query = test_data.get("search_query")
            max_year = test_data.get("max_year")
            limit = test_data.get("limit")
            perf_helper.set_run_context(
                search_query=search_query,
                max_year=max_year,
                limit=limit,
            )

            # Search Phase
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

            # Action Phase: Add to Reading List
            from pages.book_details_page import BookDetailsPage
            details_page = BookDetailsPage(page)

            screenshots: list[str] = []
            for url in book_urls:
                screenshots.extend(await details_page.add_books_to_reading_list([url]))
                await perf_helper.measure_page_performance(page, "book_page")

            perf_helper.set_run_context(
                added_book_urls=book_urls,
                added_books_count=len(book_urls),
                screenshots=screenshots,
            )

            # Assertion Phase
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

        except LoginFailedError as e:
            logger.error("Login failed, skipping performance collection and report persistence: %s", e)

        except Exception as e:
            logger.error(f"An error occurred during execution: {e}")
        
        finally:
            if should_persist_report:
                run_entry = perf_helper.build_run_entry(test_name="automation_test")
                report_data = performance_repo.append_run(run_entry, perf_helper.thresholds)
                try:
                    html_path = html_report_builder.generate_from_report_data(report_data)
                    report_opener.open_file(html_path)
                except Exception as report_error:
                    logger.warning("Could not open HTML report automatically: %s", report_error)
            else:
                logger.info("Skipping performance report persistence because login did not succeed")
            logger.info("Closing browser.")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())