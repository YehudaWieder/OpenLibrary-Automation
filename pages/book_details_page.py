# pages/book_details_page.py
import random
from typing import List

from pages.base_page import BasePage
from utils.helpers import take_screenshot

class BookDetailsPage(BasePage):

    BOOK_BUTTON = "button.book-progress-btn"
    DROPDOWN_TRIGGER = "a.generic-dropper__dropclick"
    READ_STATUS_VISIBLE_ITEM = "div.read-statuses button.nostyle-btn:not(.hidden)"
    WANT_TO_READ = "Want to Read"
    ALREADY_READ = "Already Read"
    ALLOWED_STATUSES = {WANT_TO_READ, ALREADY_READ}

    async def add_books_to_reading_list(self, urls: list) -> List[str]:
        screenshot_paths: List[str] = []

        for url in urls:
            await self.goto(url)
            self.logger.info(f"Opened: {url}")

            try:
                btn = self.page.locator(self.BOOK_BUTTON).first
                await btn.wait_for(state="visible", timeout=10000)

                chosen = random.choice([self.WANT_TO_READ, self.ALREADY_READ])
                self.logger.info(f"Choosing status: {chosen}")

                if chosen == self.WANT_TO_READ:
                    # "Want to Read" is a standalone visible button on the page.
                    want_btn = self.page.locator(f"button:has-text('{self.WANT_TO_READ}')").first
                    await want_btn.wait_for(state="visible", timeout=10000)
                    await want_btn.click()
                else:
                    # "Already Read" must be selected from the dropdown menu.
                    dropdown = self.page.locator(self.DROPDOWN_TRIGGER).first
                    await dropdown.wait_for(state="visible", timeout=10000)
                    await dropdown.click()
                    await self.page.wait_for_timeout(300)

                    status_button = self.page.locator(
                        f"{self.READ_STATUS_VISIBLE_ITEM}:has-text(\"{self.ALREADY_READ}\")"
                    ).first
                    await status_button.click()

                await self.page.wait_for_function(
                    """(selector) => {
                        const el = document.querySelector(selector);
                        return el && !el.innerText.includes('saving');
                    }""",
                    arg=self.BOOK_BUTTON,
                )

                text = await btn.inner_text()
                self.logger.info(f"Button state after choosing status: {text}")

                book_id = url.split("/")[-1]
                screenshot_path = await take_screenshot(self.page, f"book_{book_id}")
                if screenshot_path:
                    screenshot_paths.append(screenshot_path)
                self.logger.info(f"Finished interaction for: {url}")

            except Exception as e:
                self.logger.error(f"Failed to update reading status: {e}")
                raise

        return screenshot_paths