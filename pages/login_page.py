from pages.base_page import BasePage
from config import Config

class LoginPage(BasePage):
    # Selectors provided by you
    _USERNAME_INPUT = "#username"
    _PASSWORD_INPUT = "#password"
    _REMEMBER_ME_CHECKBOX = "#remember"
    _LOGIN_BUTTON = "#register > div.formElement.bottom > button"

    async def open_login(self):
        """Navigate to the login page [cite: 5]"""
        url = f"{Config.BASE_URL}/account/login"
        await self.goto(url)
        self.logger.info(f"Opened login page: {url}")

    async def login(self, email: str, password: str, remember_me: bool = False):
        """
        Perform login using provided credentials.
        Includes optional 'Remember Me' toggle.
        """
        self.logger.info(f"Attempting login for user: {email}")

        await self.fill_input(self._USERNAME_INPUT, email)
        await self.page.wait_for_timeout(500) # Small delay for stability
        await self.fill_input(self._PASSWORD_INPUT, password)

        if remember_me:
            await self.click(self._REMEMBER_ME_CHECKBOX)

        await self.click(self._LOGIN_BUTTON)

        # Wait for navigation to complete after login
        await self.page.wait_for_load_state("networkidle")
        
        # Verify login success (Optional: check for profile element or URL change)
        if "login" not in self.page.url:
            self.logger.info("Login completed successfully")
        else:
            self.logger.error("Login might have failed - still on login page")