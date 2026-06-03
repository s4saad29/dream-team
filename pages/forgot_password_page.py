from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage


class ForgotPasswordPage(BasePage):
    """Page object for https://team.addo.ai/forgot-password"""

    path = "/forgot-password"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._email_input = page.locator('input[name="email"]')
        self._send_reset_button = page.get_by_role("button", name="Send Reset Link")
        self._goto_login_link = page.get_by_role("link", name="Goto Login")

    @property
    def email_input(self) -> Locator:
        return self._email_input

    def fill_email(self, email: str) -> None:
        self._email_input.fill(email)

    def click_send_reset_link(self) -> None:
        self._send_reset_button.click()

    def click_goto_login(self) -> None:
        self._goto_login_link.click()

    def request_password_reset(self, email: str) -> None:
        self.fill_email(email)
        self.click_send_reset_link()

    def assert_on_forgot_password_page(self) -> None:
        self.expect_url_contains("/forgot-password")
        expect(self._email_input).to_be_visible(timeout=self.timeout)
        expect(self._send_reset_button).to_be_visible(timeout=self.timeout)
