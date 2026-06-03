import pytest

from config.settings import settings
from pages.dashboard_page import DashboardPage
from pages.profile_page import ProfilePage

pytestmark = [pytest.mark.smoke, pytest.mark.profile, pytest.mark.regression]


class TestProfilePage:
    def test_open_profile_from_dashboard_menu(self, profile_page: ProfilePage, requires_auth):
        profile_page.open_from_dashboard()
        profile_page.assert_on_profile_page()

    def test_profile_displays_user_details(self, profile_page: ProfilePage, requires_auth):
        profile_page.open_from_dashboard()
        profile_page.assert_profile_loaded(settings.test_user_email)

    def test_profile_section_contains_all_menu_items(self, profile_page: ProfilePage, requires_auth):
        profile_page.open_from_dashboard()
        profile_page.assert_on_profile_page()
        profile_page.assert_profile_section_menu_items()

    def test_profile_tabs_are_visible(self, profile_page: ProfilePage, requires_auth):
        profile_page.open_from_dashboard()
        profile_page.assert_profile_tabs_visible()

    def test_switch_profile_tab_to_address_info(self, profile_page: ProfilePage, requires_auth):
        profile_page.open_from_dashboard()
        profile_page.click_tab("Address Info")
        profile_page.assert_tab_selected("Address Info")

    def test_profile_menu_shows_my_profile_and_logout(
        self, profile_page: ProfilePage, dashboard_page: DashboardPage, requires_auth
    ):
        dashboard_page.navigate()
        profile_page.open_profile_menu()
        profile_page.assert_profile_menu_visible()

    def test_navigate_to_my_profile_from_menu(
        self, profile_page: ProfilePage, dashboard_page: DashboardPage, requires_auth
    ):
        dashboard_page.navigate()
        profile_page.open_profile_menu()
        profile_page.click_my_profile()
        profile_page.assert_on_profile_page()

    def test_navigate_to_dashboard_from_profile(self, profile_page: ProfilePage, requires_auth):
        profile_page.open_from_dashboard()
        profile_page.click_nav_dashboard()
        DashboardPage(profile_page.page).assert_on_dashboard()
