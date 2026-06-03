import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class MicrosoftLoginPage(BasePage):
    """Page object for Microsoft Entra / Azure AD sign-in."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._email_input = page.locator('input[name="loginfmt"]')
        self._password_input = page.locator('input[name="passwd"]')
        self._next_button = page.locator("#idSIButton9")
        self._stay_signed_in_yes = page.get_by_role("button", name="Yes")

    def wait_for_microsoft_login(self) -> None:
        expect(self.page).to_have_url(
            re.compile(r"login\.microsoftonline\.com"), timeout=self.timeout
        )

    def fill_email(self, email: str) -> None:
        self._email_input.fill(email)

    def fill_password(self, password: str) -> None:
        self._password_input.fill(password)

    def click_next(self) -> None:
        self._next_button.click()

    def accept_stay_signed_in_if_prompted(self) -> None:
        if self._stay_signed_in_yes.count() and self._stay_signed_in_yes.is_visible():
            self._stay_signed_in_yes.click()

    def login_with_credentials(self, email: str, password: str) -> None:
        """Complete the Microsoft sign-in form (email + password)."""
        self.wait_for_microsoft_login()
        self.fill_email(email)
        self.click_next()
        self._password_input.wait_for(state="visible", timeout=self.timeout)
        self.fill_password(password)
        self.click_next()

    def assert_microsoft_sign_in_page(self) -> None:
        self.wait_for_microsoft_login()
        expect(self.page).to_have_title("Sign in to your account", timeout=self.timeout)
