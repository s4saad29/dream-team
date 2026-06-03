import pytest

from config.settings import settings
from pages.dashboard_page import DashboardPage
from pages.my_projects_page import MyProjectsPage
from pages.worklogs_page import WorklogsPage

pytestmark = [pytest.mark.smoke, pytest.mark.dashboard, pytest.mark.regression]


class TestDashboardPage:
    def test_dashboard_loads(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.assert_dashboard_loaded()

    def test_dashboard_displays_navigation(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.assert_navigation_visible()

    def test_dashboard_displays_action_buttons(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.assert_action_buttons_visible()

    def test_dashboard_displays_user_email(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.assert_user_profile_visible(settings.test_user_email)

    def test_dashboard_displays_attendance_tabs(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.assert_attendance_tabs_visible()

    def test_dashboard_weekly_hours_section(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.assert_weekly_hours_section_visible()

    def test_leave_listing_tab_content(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.assert_leave_listing_tab_content()

    def test_overtime_tab_content(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.assert_overtime_tab_content()

    def test_recent_attendance_tab_content(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.assert_recent_attendance_tab_content()

    def test_my_punch_requests_tab_content(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.assert_my_punch_requests_tab_content()

    def test_view_full_log_navigates_to_worklogs(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.click_tab("Recent attendance")
        dashboard_page.click_view_full_log()
        WorklogsPage(dashboard_page.page).assert_on_worklogs()

    def test_navigate_to_worklogs(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.click_nav_worklogs()
        WorklogsPage(dashboard_page.page).assert_on_worklogs()

    def test_navigate_to_my_projects(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.click_nav_my_projects()
        MyProjectsPage(dashboard_page.page).assert_on_my_projects()

    def test_navigate_back_to_dashboard_from_worklogs(self, dashboard_page: DashboardPage, requires_auth):
        dashboard_page.navigate()
        dashboard_page.click_nav_worklogs()
        dashboard_page.click_nav_dashboard()
        dashboard_page.assert_on_dashboard()
