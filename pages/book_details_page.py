# pages/book_details_page.py
import random

from pages.base_page import BasePage
from utils.helpers import take_screenshot

class BookDetailsPage(BasePage):

    BOOK_BUTTON = "button.book-progress-btn"
    DROPDOWN_TRIGGER = "a.generic-dropper__dropclick"
    READ_STATUS_ITEM = "div.read-statuses button.nostyle-btn"

    async def add_books_to_reading_list(self, urls: list) -> None:
        statuses = ["Want to Read", "Already Read"]

        for url in urls:
            chosen = random.choice(statuses)
            self.logger.info(f"Choosing status: {chosen}")

            await self.goto(url)
            self.logger.info(f"Opened: {url}")

            try:
                btn = self.page.locator(self.BOOK_BUTTON).first
                await btn.wait_for(state="visible", timeout=10000)

                # Open the status dropdown menu
                dropdown = self.page.locator(self.DROPDOWN_TRIGGER).first
                await dropdown.wait_for(state="visible", timeout=10000)
                await dropdown.click()
                await self.page.wait_for_timeout(500)  # דרופדאון צריך זמן להיפתח

                status_button = self.page.locator(f"{self.READ_STATUS_ITEM}:has-text(\"{chosen}\")").first
                
                # Remove hidden class בדרך הישירה
                await status_button.evaluate("el => el.classList.remove('hidden')")
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
                await take_screenshot(self.page, f"book_{book_id}")
                self.logger.info(f"Finished interaction for: {url}")

            except Exception as e:
                self.logger.error(f"Failed to update reading status: {e}")
                raise