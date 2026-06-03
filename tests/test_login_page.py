import re

import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.login_page import LoginPage
from utils.auth_helper import login_via_microsoft, save_authenticated_session

pytestmark = [pytest.mark.smoke, pytest.mark.login, pytest.mark.regression]


class TestLoginPage:
    def test_root_redirects_to_login(self, page: Page, login_page: LoginPage):
        page.goto("/")
        login_page.assert_on_login_page()
        login_page.expect_title_contains("Addo | Dream Team")

    def test_login_page_displays_form_elements(self, login_page: LoginPage):
        login_page.navigate()
        login_page.assert_login_form_visible()

    def test_forgot_password_navigation(self, login_page: LoginPage):
        login_page.navigate()
        login_page.click_forgot_password()
        login_page.expect_url_contains("/forgot-password")

    @pytest.mark.skipif(
        not settings.has_credentials,
        reason="Set TEST_USER_EMAIL and TEST_USER_PASSWORD in .env",
    )
    def test_log_in_with_microsoft_redirects_to_microsoft_sso(
        self, login_page: LoginPage
    ):
        login_via_microsoft(login_page.page)
        login_page.assert_left_login_page()
        save_authenticated_session(login_page.page)

    def test_login_button_disabled_when_form_empty(self, login_page: LoginPage):
        login_page.navigate()
        expect(login_page.page.get_by_role("button", name="Log In", exact=True)).to_be_disabled()
        login_page.expect_url_contains("/login")

    def test_invalid_credentials_remain_on_login(self, login_page: LoginPage):
        login_page.navigate()
        login_page.login("invalid@example.com", "wrong-password-123")
        login_page.page.wait_for_load_state("networkidle")
        expect(login_page.page).to_have_url(re.compile(r"/login"))
