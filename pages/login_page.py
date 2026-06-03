import re

from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    """Page object for https://team.addo.ai/login"""

    path = "/login"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._email_input = page.locator('input[name="email"]')
        self._password_input = page.locator('input[name="password"]')
        self._login_button = page.get_by_role("button", name="Log In", exact=True)
        self._microsoft_login_button = page.get_by_role(
            "button", name="Log In with Microsoft"
        )
        self._support_button = page.get_by_role("button", name="Need Support?")
        self._forgot_password_link = page.get_by_role("link", name="Forgot Password ?")

    @property
    def email_input(self) -> Locator:
        return self._email_input

    @property
    def password_input(self) -> Locator:
        return self._password_input

    def fill_email(self, email: str) -> None:
        self._email_input.fill(email)

    def fill_password(self, password: str) -> None:
        self._password_input.fill(password)

    def click_login(self) -> None:
        self._login_button.click()

    def click_microsoft_login(self) -> None:
        self._microsoft_login_button.click()

    def click_forgot_password(self) -> None:
        self._forgot_password_link.click()

    def login(self, email: str, password: str) -> None:
        self.fill_email(email)
        self.fill_password(password)
        self.click_login()

    def assert_on_login_page(self) -> None:
        self.expect_url_contains("/login")
        expect(self._email_input).to_be_visible(timeout=self.timeout)
        expect(self._password_input).to_be_visible(timeout=self.timeout)
        expect(self._login_button).to_be_visible(timeout=self.timeout)

    def assert_login_form_visible(self) -> None:
        expect(self._email_input).to_be_visible()
        expect(self._password_input).to_be_visible()
        expect(self._forgot_password_link).to_be_visible()
        expect(self._login_button).to_be_visible()
        expect(self._microsoft_login_button).to_be_visible()

    def assert_left_login_page(self) -> None:
        expect(self.page).not_to_have_url(re.compile(r"/login$"), timeout=self.timeout)
