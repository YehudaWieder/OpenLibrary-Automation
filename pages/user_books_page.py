#pages/user_books_page.py
import re

from pages.base_page import BasePage
from config import Config

class UserBooksPage(BasePage):
    # Direct list URLs are more stable than analytics-based sidebar selectors.
    WANT_TO_READ_PATH = "/account/books/want-to-read"
    ALREADY_READ_PATH = "/account/books/already-read"
    WANT_TO_READ_SIDEBAR_COUNT = "a[data-ol-link-track='MyBooksSidebar|WantToRead'] .li-count"
    ALREADY_READ_SIDEBAR_COUNT = "a[data-ol-link-track='MyBooksSidebar|AlreadyRead'] .li-count"
    BOOK_ITEM = ".searchResultItem"
    BOOK_TOGGLE_BUTTON = "button.book-progress-btn"
    MAX_ATTEMPTS_FOR_CLEARING = 10
    ITEMS_CLEAR_PER_RELOAD = 25

    async def open(self):
        """Navigate to the user's books overview page."""
        await self.goto(f"{Config.BASE_URL}/account/books")
        self.logger.info("Opened User Books overview page")

    async def _open_list(self, list_path: str) -> None:
        """Open a specific reading list page by path."""
        await self.goto(f"{Config.BASE_URL}{list_path}")
        await self.page.wait_for_load_state("networkidle")

    async def _count_books_in_list(self, list_path: str) -> int:
        """Count books directly from a list page result cards."""
        await self._open_list(list_path)
        return await self.page.locator(self.BOOK_ITEM).count()

    async def _extract_sidebar_count(self, count_locator: str) -> int | None:
        """Read numeric list count from My Books sidebar when available."""
        locator = self.page.locator(count_locator).first
        if await locator.count() == 0:
            return None

        text = (await locator.inner_text()).strip()
        match = re.search(r"\d+", text)
        return int(match.group(0)) if match else None

    async def get_want_to_read_count(self) -> int:
        """Return the 'Want to Read' count."""
        await self.open()
        sidebar_count = await self._extract_sidebar_count(self.WANT_TO_READ_SIDEBAR_COUNT)
        if sidebar_count is not None:
            return sidebar_count
        self.logger.warning("Sidebar count for Want to Read not found. Falling back to list page count.")
        return await self._count_books_in_list(self.WANT_TO_READ_PATH)

    async def get_already_read_count(self) -> int:
        """Return the 'Already Read' count."""
        await self.open()
        sidebar_count = await self._extract_sidebar_count(self.ALREADY_READ_SIDEBAR_COUNT)
        if sidebar_count is not None:
            return sidebar_count
        self.logger.warning("Sidebar count for Already Read not found. Falling back to list page count.")
        return await self._count_books_in_list(self.ALREADY_READ_PATH)

    async def get_reading_list_total(self) -> int:
        """Return the combined total of both reading list categories."""
        await self.open()
        want_sidebar = await self._extract_sidebar_count(self.WANT_TO_READ_SIDEBAR_COUNT)
        already_sidebar = await self._extract_sidebar_count(self.ALREADY_READ_SIDEBAR_COUNT)

        if want_sidebar is not None and already_sidebar is not None:
            want = want_sidebar
            already = already_sidebar
        else:
            self.logger.warning("Sidebar counters unavailable. Falling back to direct list item counting.")
            want = await self._count_books_in_list(self.WANT_TO_READ_PATH)
            already = await self._count_books_in_list(self.ALREADY_READ_PATH)

        total = want + already
        self.logger.info(f"Reading list totals: Want={want}, Already={already}, Total={total}")
        return total

    async def clear_list(self, list_path: str) -> None:
        """Clear all books from a specific reading list.

        Since items only disappear after a full page reload, we click multiple
        toggle buttons before triggering a reload.
        """
        await self._open_list(list_path)

        for attempt in range(self.MAX_ATTEMPTS_FOR_CLEARING):
            toggle_buttons = self.page.locator(self.BOOK_ITEM).locator(self.BOOK_TOGGLE_BUTTON)
            count = await toggle_buttons.count()

            if count == 0:
                self.logger.info("List cleared successfully.")
                break

            self.logger.debug(f"Attempt {attempt + 1}: Found {count} items to remove.")

            # Click up to ITEMS_CLEAR_PER_RELOAD buttons before reload
            buttons_to_click = min(count, self.ITEMS_CLEAR_PER_RELOAD)

            for i in range(buttons_to_click):
                try:
                    btn = toggle_buttons.nth(i)
                    await btn.click()
                    await self.page.wait_for_timeout(300)
                except Exception as e:
                    self.logger.warning(f"Failed to click toggle button {i}: {e}")
                    break

            # Reload to make changes take effect
            await self.page.wait_for_load_state("networkidle")
            await self.page.reload()
            await self.page.wait_for_load_state("networkidle")

        else:
            self.logger.warning(f"Reached max attempts ({self.MAX_ATTEMPTS_FOR_CLEARING}) while clearing list.")
            
    async def clear_reading_lists(self) -> None:
        """Clear all books from both Want to Read and Already Read lists."""
        await self.clear_list(self.WANT_TO_READ_PATH)
        await self.page.wait_for_load_state("networkidle")

        await self.clear_list(self.ALREADY_READ_PATH)
        self.logger.info("Cleared all reading lists")
