import pytest

from pages.login_page import LoginFailedError, LoginPage


class FakeLocator:
    def __init__(self, page, selector: str, *, visible: bool = False, text: str = "", on_click=None) -> None:
        self.page = page
        self.selector = selector
        self.visible = visible
        self.text = text
        self.on_click = on_click
        self.filled_values: list[str] = []

    @property
    def first(self):
        return self

    async def wait_for(self, state: str = "visible", timeout: int = 0) -> None:
        if state == "visible" and not self.visible:
            raise AssertionError(f"Locator {self.selector} is not visible")

    async def fill(self, value: str) -> None:
        self.filled_values.append(value)

    async def click(self) -> None:
        if self.on_click is not None:
            self.on_click()

    async def is_visible(self) -> bool:
        return self.visible

    async def inner_text(self) -> str:
        return self.text


class FakePage:
    def __init__(self, url: str, locators: dict[str, FakeLocator], validation_message: str | None = None) -> None:
        self.url = url
        self._locators = locators
        self.validation_message = validation_message

    def locator(self, selector: str) -> FakeLocator:
        return self._locators.setdefault(selector, FakeLocator(self, selector, visible=False))

    async def wait_for_load_state(self, state: str) -> None:
        return None

    async def wait_for_timeout(self, timeout: int) -> None:
        return None

    async def evaluate(self, script: str, arg=None) -> object:
        return self.validation_message


@pytest.mark.asyncio
async def test_ensure_logged_in_raises_when_still_on_login_page() -> None:
    page = FakePage(
        "https://openlibrary.org/account/login",
        {
            "#username": FakeLocator(None, "#username", visible=True),
            "#register > div.formElement.bottom > button": FakeLocator(None, "#register > div.formElement.bottom > button", visible=True),
            "[role='alert']": FakeLocator(None, "[role='alert']", visible=True, text="Invalid username or password"),
        },
    )
    for locator in page._locators.values():
        locator.page = page

    login_page = LoginPage(page)

    with pytest.raises(LoginFailedError, match="Invalid username or password"):
        await login_page.ensure_logged_in()


@pytest.mark.asyncio
async def test_login_succeeds_when_redirected_and_form_hidden() -> None:
    def on_login_click() -> None:
        page.url = "https://openlibrary.org/people/test-user/books"
        page.locator("#username").visible = False
        page.locator("#register > div.formElement.bottom > button").visible = False

    page = FakePage(
        "https://openlibrary.org/account/login",
        {
            "#username": FakeLocator(None, "#username", visible=True),
            "#password": FakeLocator(None, "#password", visible=True),
            "#register > div.formElement.bottom > button": FakeLocator(
                None,
                "#register > div.formElement.bottom > button",
                visible=True,
                on_click=on_login_click,
            ),
        },
    )
    for locator in page._locators.values():
        locator.page = page

    login_page = LoginPage(page)

    await login_page.login("user@example.com", "secret")

    assert page.url.endswith("/books")


@pytest.mark.asyncio
async def test_login_raises_when_authentication_fails() -> None:
    page = FakePage(
        "https://openlibrary.org/account/login",
        {
            "#username": FakeLocator(None, "#username", visible=True),
            "#password": FakeLocator(None, "#password", visible=True),
            "#register > div.formElement.bottom > button": FakeLocator(None, "#register > div.formElement.bottom > button", visible=True),
            ".note.error": FakeLocator(None, ".note.error", visible=True, text="Login failed"),
        },
    )
    for locator in page._locators.values():
        locator.page = page

    login_page = LoginPage(page)

    with pytest.raises(LoginFailedError, match="Login failed"):
        await login_page.login("user@example.com", "wrong-password")


@pytest.mark.asyncio
async def test_ensure_logged_in_raises_with_browser_validation_message() -> None:
    page = FakePage(
        "https://openlibrary.org/account/login",
        {
            "#username": FakeLocator(None, "#username", visible=True),
            "#register > div.formElement.bottom > button": FakeLocator(None, "#register > div.formElement.bottom > button", visible=True),
        },
        validation_message="email: Please fill out this field.",
    )
    for locator in page._locators.values():
        locator.page = page

    login_page = LoginPage(page)

    with pytest.raises(LoginFailedError, match="Validation: email"):
        await login_page.ensure_logged_in()


@pytest.mark.asyncio
async def test_login_raises_fast_when_credentials_missing() -> None:
    page = FakePage(
        "https://openlibrary.org/account/login",
        {
            "#username": FakeLocator(None, "#username", visible=True),
            "#password": FakeLocator(None, "#password", visible=True),
            "#register > div.formElement.bottom > button": FakeLocator(None, "#register > div.formElement.bottom > button", visible=True),
        },
    )
    for locator in page._locators.values():
        locator.page = page

    login_page = LoginPage(page)

    with pytest.raises(LoginFailedError, match="required"):
        await login_page.login("", "")