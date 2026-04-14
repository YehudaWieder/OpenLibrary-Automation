#pages/user_books_page.py
import re
from pages.base_page import BasePage
from config import Config

class UserBooksPage(BasePage):
    # Selectors based on your input
    WANT_TO_READ_BUTTON = "a[data-ol-link-track='BookCarousel|HeaderClick|want-to-read']"
    ALREADY_READ_BUTTON = "a[data-ol-link-track='BookCarousel|HeaderClick|already-read']"
    BOOK_ITEM = ".searchResultItem"
    BOOK_TOGGLE_BUTTON = "button.book-progress-btn"

    async def open(self):
        """Navigate to the user's books overview page."""
        await self.goto(f"{Config.BASE_URL}/account/books")
        self.logger.info("Opened User Books overview page")

    async def _extract_count(self, locator: str) -> int:
        """Extract numeric count from a list widget label."""
        # Check if locator exists first
        if await self.page.locator(locator).count() == 0:
            self.logger.info(f"Locator not found: {locator}")
            return 0
    
        text = await self.get_text(locator)
        match = re.search(r"\((\d+)\)", text)
        return int(match.group(1)) if match else 0

    async def get_want_to_read_count(self) -> int:
        """Return the 'Want to Read' count."""
        return await self._extract_count(self.WANT_TO_READ_BUTTON)

    async def get_already_read_count(self) -> int:
        """Return the 'Already Read' count."""
        return await self._extract_count(self.ALREADY_READ_BUTTON)

    async def get_reading_list_total(self) -> int:
        """Return the combined total of both reading list categories."""
        want = await self.get_want_to_read_count()
        already = await self.get_already_read_count()
        total = want + already
        self.logger.info(f"Reading list totals: Want={want}, Already={already}, Total={total}")
        return total

    async def clear_list(self, list_button: str) -> None:
        # Check if the list button exists before clicking
        if await self.page.locator(list_button).count() == 0:
            self.logger.info(f"List button not found: {list_button}")
            return
        
        await self.click(list_button)
        await self.page.wait_for_load_state("networkidle")
        
        while True:
            items = self.page.locator(self.BOOK_ITEM)
            count = await items.count()
            
            if count == 0:
                break
            
            btn = items.first.locator(self.BOOK_TOGGLE_BUTTON)
            await btn.click()
            await self.page.wait_for_load_state("networkidle")
            await self.page.reload()

    async def clear_reading_lists(self) -> None:
        """Clear all books from both Want to Read and Already Read lists."""
        await self.open()
        await self.clear_list(self.WANT_TO_READ_BUTTON)
        await self.page.wait_for_load_state("networkidle")
        
        await self.open()
        await self.clear_list(self.ALREADY_READ_BUTTON)
        self.logger.info("Cleared all reading lists")
