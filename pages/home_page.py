# pages/home_page.py
import re
from pages.base_page import BasePage
from config import Config  # Assuming BASE_URL is in your config

class HomePage(BasePage):
    # Locators
    _SEARCH_INPUT = "input[name='q']"
    _RESULT_ITEMS = ".searchResultItem"
    _BOOK_LINK = "h3.booktitle a"
    _NEXT_PAGE = "a[aria-label='Go to next page']"

    async def open(self):
        """Navigate to the base URL."""
        await self.goto(Config.BASE_URL)

    async def submit_search(self, query: str) -> None:
        """Enter a search query and submit the search form."""
        self.logger.info(f"Submitting search query: {query}")
        await self.fill_input(self._SEARCH_INPUT, query)
        await self.page.keyboard.press("Enter")

    async def get_result_items(self):
        """Return all current search result items."""
        await self.page.locator(self._RESULT_ITEMS).first.wait_for(state="visible")
        return await self.page.locator(self._RESULT_ITEMS).all()

    async def extract_book_year(self, item) -> int:
        """Extract the publication year from a search result item."""
        text = await item.inner_text()
        match = re.search(r"First published in (\d{4})", text)
        return int(match.group(1)) if match else 0

    async def extract_book_url(self, item) -> str:
        """Extract the book details URL from a search result item."""
        href = await item.locator(self._BOOK_LINK).get_attribute("href")
        return f"{Config.BASE_URL}{href}" if href else ""

    async def has_next_page(self) -> bool:
        """Return whether the next search page button is visible."""
        next_btn = self.page.locator(self._NEXT_PAGE).first
        return await next_btn.is_visible()

    async def go_to_next_page(self) -> None:
        """Click the next search page button and wait for navigation."""
        self.logger.info("Navigating to next page of results")
        next_btn = self.page.locator(self._NEXT_PAGE).first
        await next_btn.click()
        await self.page.wait_for_load_state("networkidle")
