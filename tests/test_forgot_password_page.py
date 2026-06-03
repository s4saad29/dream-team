import pytest

from pages.forgot_password_page import ForgotPasswordPage
from pages.login_page import LoginPage

pytestmark = [pytest.mark.smoke, pytest.mark.login, pytest.mark.regression]


class TestForgotPasswordPage:
    def test_forgot_password_page_displays_form(
        self, forgot_password_page: ForgotPasswordPage
    ):
        forgot_password_page.navigate()
        forgot_password_page.assert_on_forgot_password_page()

    def test_goto_login_returns_to_login(
        self, forgot_password_page: ForgotPasswordPage, login_page: LoginPage
    ):
        forgot_password_page.navigate()
        forgot_password_page.click_goto_login()
        login_page.assert_on_login_page()

    def test_submit_reset_with_email_stays_or_redirects(
        self, forgot_password_page: ForgotPasswordPage
    ):
        forgot_password_page.navigate()
        forgot_password_page.request_password_reset("test.user@example.com")
        forgot_password_page.page.wait_for_load_state("networkidle")
        # App may show confirmation on same page or redirect to login
        url = forgot_password_page.page.url
        assert "/forgot-password" in url or "/login" in url
