import re

import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from pages.profile_page import ProfilePage

pytestmark = [pytest.mark.profile, pytest.mark.regression]


class TestProfilePageLogout:
    def test_logout_redirects_to_login(self, dashboard_page: DashboardPage, requires_auth):
        profile = ProfilePage(dashboard_page.page)
        login = LoginPage(dashboard_page.page)
        dashboard_page.navigate()
        profile.open_profile_menu()
        profile.click_logout()
        login.assert_on_login_page()
        expect(dashboard_page.page).to_have_url(re.compile(r"/login"))
