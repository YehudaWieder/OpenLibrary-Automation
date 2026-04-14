from typing import Optional

from pages.base_page import BasePage
from config import Config


class LoginFailedError(RuntimeError):
    """Raised when login does not establish an authenticated session."""

class LoginPage(BasePage):
    # Selectors provided by you
    _EMAIL_INPUT = "#username"
    _PASSWORD_INPUT = "#password"
    _REMEMBER_ME_CHECKBOX = "#remember"
    _LOGIN_BUTTON = "#register > div.formElement.bottom > button"
    _LOGIN_ERROR_SELECTORS = (
        "[role='alert']",
        ".note.error",
        ".alert-danger",
        ".flash.error",
    )

    async def open_login(self) -> None:
        """Navigate to the login page [cite: 5]"""
        url = f"{Config.BASE_URL}/account/login"
        await self.goto(url)
        self.logger.info(f"Opened login page: {url}")

    async def is_login_form_visible(self) -> bool:
        """Return whether the login form is still visible."""
        return (
            await self.page.locator(self._EMAIL_INPUT).is_visible()
            and await self.page.locator(self._LOGIN_BUTTON).is_visible()
        )

    async def get_login_error_message(self) -> Optional[str]:
        """Return a visible login error message when available."""
        for selector in self._LOGIN_ERROR_SELECTORS:
            locator = self.page.locator(selector).first
            if await locator.is_visible():
                message = (await locator.inner_text()).strip()
                if message:
                    return message
        return None

    async def get_login_validation_message(self) -> Optional[str]:
        """Return browser-side validation message for required/invalid fields."""
        return await self.page.evaluate(
            """(selectors) => {
                const fields = [
                    { key: 'email', selector: selectors.email },
                    { key: 'password', selector: selectors.password },
                ];

                const messages = [];
                for (const field of fields) {
                    const element = document.querySelector(field.selector);
                    if (!element || typeof element.checkValidity !== 'function') {
                        continue;
                    }
                    if (!element.checkValidity()) {
                        const validationMessage = (element.validationMessage || '').trim();
                        if (validationMessage) {
                            messages.push(`${field.key}: ${validationMessage}`);
                        }
                    }
                }

                return messages.length ? messages.join(' | ') : null;
            }""",
            {"email": self._EMAIL_INPUT, "password": self._PASSWORD_INPUT},
        )

    async def ensure_logged_in(self) -> None:
        """Fail fast when login did not produce an authenticated session."""
        on_login_page = "/account/login" in self.page.url.lower()
        login_form_visible = await self.is_login_form_visible()

        if on_login_page or login_form_visible:
            error_message = await self.get_login_error_message()
            validation_message = await self.get_login_validation_message()
            message = "Login failed: still on login page after submit"
            if error_message:
                message = f"{message}. Server message: {error_message}"
            elif validation_message:
                message = f"{message}. Validation: {validation_message}"
            self.logger.error(message)
            raise LoginFailedError(message)

        self.logger.info("Login completed successfully")

    async def login(self, email: str, password: str, remember_me: bool = False) -> None:
        """
        Perform login using provided credentials.
        Includes optional 'Remember Me' toggle.
        """
        if not email.strip() or not password.strip():
            message = "Login failed: email and password are required"
            self.logger.error(message)
            raise LoginFailedError(message)

        self.logger.info(f"Attempting login for user: {email}")

        await self.fill_input(self._EMAIL_INPUT, email)
        await self.page.wait_for_timeout(500) # Small delay for stability
        await self.fill_input(self._PASSWORD_INPUT, password)

        if remember_me:
            await self.click(self._REMEMBER_ME_CHECKBOX)

        await self.click(self._LOGIN_BUTTON)

        # Wait for navigation to complete after login
        await self.page.wait_for_load_state("networkidle")

        await self.ensure_logged_in()