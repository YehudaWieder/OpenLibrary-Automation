#pages/user_books_page.py
import re
from pages.base_page import BasePage
from config import Config

class UserBooksPage(BasePage):
    # Selectors based on your input
    WANT_TO_READ_BUTTON = "text=Want to Read"
    ALREADY_READ_BUTTON = "text=Already Read"

    async def open(self):
        """Navigate to the user's books overview page."""
        await self.goto(f"{Config.BASE_URL}/people/{Config.USERNAME_INPUT}/books")
        self.logger.info("Opened User Books overview page")

    async def _extract_count(self, locator: str) -> int:
        """Extract numeric count from a list widget label."""
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
