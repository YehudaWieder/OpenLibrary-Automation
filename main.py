# main.py
import asyncio
import logging

from playwright.async_api import async_playwright

# Imports from your pages
from pages.login_page import LoginFailedError
from utils.data_loader import load_test_data
from utils.openlibrary_flow_api import (
    add_books_to_reading_list,
    assert_reading_list_count,
    clear_flow_context,
    configure_flow_context,
    measure_page_performance,
    prepare_authenticated_session,
    reset_reading_lists,
    search_books_by_title_under_year,
)
from utils.performance.performance_repository import PerformanceRepository
from utils.performance.performance_html_report import PerformanceHtmlReportBuilder
from utils.performance.report_opener import ReportOpener
from utils.performance.performance_helper import PerformanceHelper
from utils.performance.run_lifecycle import (
    create_run_state,
    finalize_run_context,
    mark_run_success,
    mark_run_failed,
    persist_and_publish_report,
)
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
    run_state = create_run_state()
    
    async with async_playwright() as p:
        # Setup Browser
        logger.info(f"Launching {Config.BROWSER}...")
        
        browser_launcher = getattr(p, Config.BROWSER)
        browser = await browser_launcher.launch(headless=Config.HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()
        
        configure_flow_context(
            page=page,
            perf_helper=perf_helper,
            randomize_reading_status=Config.RANDOMIZE_READING_STATUS,
        )

        try:
            perf_helper.set_run_context(run_status="PASSED", failure_details="")

            # Login Phase
            await prepare_authenticated_session()

            # Clear existing reading lists to prevent toggle issues
            await reset_reading_lists()

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
            book_urls = await search_books_by_title_under_year(
                query=search_query,
                max_year=max_year,
                limit=limit,
            )
            await measure_page_performance(
                page=page,
                url=f"{Config.BASE_URL}/search?q={search_query}",
                threshold_ms=3000,
            )

            if not book_urls:
                raise RuntimeError("No books found matching criteria")

            # Action Phase: Add to Reading List
            for url in book_urls:
                await add_books_to_reading_list([url])
                await measure_page_performance(
                    page=page,
                    url=url,
                    threshold_ms=2500,
                )

            perf_helper.set_run_context(
                added_book_urls=book_urls,
                added_books_count=len(book_urls),
            )

            # Assertion Phase
            await assert_reading_list_count(expected_count=len(book_urls))
            await measure_page_performance(
                page=page,
                url=f"{Config.BASE_URL}/account/books",
                threshold_ms=2000,
            )

            mark_run_success(run_state)
            logger.info("TEST PASSED: Books successfully added to reading list.")

        except asyncio.CancelledError:
            mark_run_failed(run_state, perf_helper, "Run cancelled (asyncio.CancelledError)")
            logger.warning("Run cancelled (asyncio.CancelledError)")
            raise

        except KeyboardInterrupt:
            mark_run_failed(run_state, perf_helper, "Run interrupted by user (KeyboardInterrupt)")
            logger.warning("Run interrupted by user (KeyboardInterrupt)")
            raise

        except LoginFailedError as e:
            mark_run_failed(run_state, perf_helper, f"Login failed: {e}")
            logger.error("Login failed: %s", e)

        except Exception as e:
            mark_run_failed(run_state, perf_helper, str(e))
            logger.error(f"An error occurred during execution: {e}")
        
        finally:
            finalize_run_context(run_state, perf_helper)
            persist_and_publish_report(
                perf_helper,
                performance_repo,
                html_report_builder,
                report_opener,
            )
            logger.info("Closing browser.")
            clear_flow_context()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())