import logging
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(self.__class__.__name__)

    async def goto(self, url: str, timeout: int = 30000) -> None:
        try:
            self.logger.info(f"Navigating to: {url}")
            await self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        except PlaywrightTimeoutError:
            self.logger.error(f"Timeout while navigating to {url}")
            raise

    async def fill_input(self, locator: str, value: str, timeout: int = 10000) -> None:
        try:
            self.logger.info(f"Filling input: {locator}")
            element = self.page.locator(locator)
            await element.wait_for(state="visible", timeout=timeout)
            await element.fill(value)
        except Exception as e:
            self.logger.error(f"Failed to fill input {locator}: {e}")
            raise

    async def click(self, locator: str, timeout: int = 10000) -> None:
        try:
            self.logger.info(f"Clicking: {locator}")
            element = self.page.locator(locator)
            await element.wait_for(state="visible", timeout=timeout)
            await element.click()
        except Exception as e:
            self.logger.error(f"Click failed on {locator}: {e}")
            raise
        
    async def get_text(self, locator: str, timeout: int = 10000) -> str:
        """
        Retrieves and cleans text from an element.
        Waits for element to be attached (not necessarily visible).
        """
        try:
            self.logger.info(f"Getting text from: {locator}")

            element = self.page.locator(locator)

            # IMPORTANT: use attached instead of visible
            await element.wait_for(state="attached", timeout=timeout)

            text = await element.inner_text()
            return text.strip()

        except Exception as e:
            self.logger.error(f"Failed to get text from {locator}: {e}")
            raise

    async def safe_wait(self, selector: str, timeout: int = 10000) -> bool:
        try:
            await self.page.locator(selector).wait_for(timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            self.logger.warning(f"Element not found: {selector}")
            return False