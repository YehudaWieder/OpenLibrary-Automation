# main.py
import asyncio
import logging
from playwright.async_api import async_playwright

# Imports from your pages
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.user_books_page import UserBooksPage
from utils.data_loader import load_test_data
from utils.search_utils import search_books_by_title_under_year
from utils.reading_list_utils import assert_reading_lists_count
from config import Config

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MainRunner")

async def run_test():
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

            home_page = HomePage(page)
            book_urls = await search_books_by_title_under_year(
                home_page=home_page,
                query=search_query,
                max_year=max_year,
                limit=limit,
            )

            if not book_urls:
                logger.error("No books found matching criteria. Stopping test.")
                return

            # 4. Action Phase: Add to Reading List (Task #2)
            # We already have book_urls. Now we visit each one.
            from pages.book_details_page import BookDetailsPage
            details_page = BookDetailsPage(page)
            
            await details_page.add_books_to_reading_list(book_urls)                

            # 5. Assertion Phase (Task #3)
            user_books_page = UserBooksPage(page)
            await user_books_page.open()
            actual_count = await assert_reading_lists_count(
                user_books_page=user_books_page,
                expected_count=len(book_urls),
            )

            logger.info("TEST PASSED: Books successfully added to reading list.")

        except Exception as e:
            logger.error(f"An error occurred during execution: {e}")
        
        finally:
            logger.info("Closing browser.")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())