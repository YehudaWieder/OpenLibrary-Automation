# pages/book_details_page.py
from pages.base_page import BasePage
from utils.helpers import take_screenshot

class BookDetailsPage(BasePage):

    BOOK_BUTTON = "button.book-progress-btn"

    async def add_books_to_reading_list(self, urls: list) -> None:
        import random

        statuses = ["Want to Read", "Already Read"]
        chosen = random.choice(statuses)

        self.logger.info(f"Choosing status: {chosen}")

        for url in urls:
            await self.goto(url)
            self.logger.info(f"Opened: {url}")

            try:
                btn = self.page.locator(self.BOOK_BUTTON).first
                await btn.wait_for(state="visible", timeout=10000)

                # Click opens / toggles menu state
                await btn.click()

                # wait until saving finishes
                await self.page.wait_for_function(
                    """(selector) => {
                        const el = document.querySelector(selector);
                        return el && !el.innerText.includes('saving');
                    }""",
                    arg=self.BOOK_BUTTON
                    )

                text = await btn.inner_text()

                self.logger.info(f"Button state after click: {text}")

                book_id = url.split("/")[-1]
                await take_screenshot(self.page, f"book_{book_id}")

                self.logger.info(f"Finished interaction for: {url}")

            except Exception as e:
                self.logger.error(f"Failed to update reading status: {e}")
                raise