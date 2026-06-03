import re

from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage


class DashboardPage(BasePage):
    """Page object for https://team.addo.ai/dashboard"""

    path = "/dashboard"

    ATTENDANCE_TABS = (
        "Leave listing",
        "Overtime",
        "Recent attendance",
        "My punch requests",
    )

    LEAVE_LISTING_COLUMNS = (
        "Leave type",
        "Start date",
        "End date",
        "Days",
        "Quota",
        "Status",
        "Notes",
    )

    OVERTIME_COLUMNS = (
        "Milestone",
        "Start date",
        "End date",
        "Days",
        "Day portion",
        "Expires",
        "Expiry status",
        "Status",
        "Notes",
        "Actions",
    )

    RECENT_ATTENDANCE_COLUMNS = (
        "Date",
        "Check in",
        "Check out",
        "Hours",
        "Status",
        "Action",
    )

    PUNCH_REQUESTS_COLUMNS = (
        "Date",
        "Type",
        "Time",
        "Reason",
        "Status",
        "Actions",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._welcome_heading = page.get_by_role("heading", name=re.compile(r"Welcome back"))
        self._weekly_hours_heading = page.get_by_role("heading", name="Weekly Hours")
        self._leave_quota_heading = page.get_by_role("heading", name="Leave Quota")
        self._leave_listing_tab = page.get_by_role("tab", name="Leave listing")
        self._overtime_tab = page.get_by_role("tab", name="Overtime")
        self._recent_attendance_tab = page.get_by_role("tab", name="Recent attendance")
        self._my_punch_requests_tab = page.get_by_role("tab", name="My punch requests")
        self._nav_dashboard = page.get_by_role("link", name="Dashboard", exact=True)
        self._nav_worklogs = page.get_by_role("link", name="Worklogs", exact=True)
        self._nav_my_projects = page.get_by_role("link", name="My Projects", exact=True)
        self._request_leave_button = page.get_by_role("button", name="Request Leave", exact=True)
        self._punch_request_button = page.get_by_role("button", name="Punch request")
        self._view_report_button = page.get_by_role("button", name=re.compile(r"View report"))
        self._view_full_log_button = page.get_by_role("button", name="View full log")

    @property
    def welcome_heading(self) -> Locator:
        return self._welcome_heading

    def click_tab(self, tab_name: str) -> None:
        self.page.get_by_role("tab", name=tab_name).click()

    def click_nav_dashboard(self) -> None:
        self._nav_dashboard.click()

    def click_nav_worklogs(self) -> None:
        self._nav_worklogs.click()

    def click_nav_my_projects(self) -> None:
        self._nav_my_projects.click()

    def click_view_full_log(self) -> None:
        self._view_full_log_button.click()
        self.page.wait_for_load_state("domcontentloaded")

    def assert_on_dashboard(self) -> None:
        self.expect_url_contains("/dashboard")
        expect(self._welcome_heading).to_be_visible(timeout=self.timeout)

    def assert_dashboard_loaded(self) -> None:
        self.assert_on_dashboard()
        expect(self._leave_quota_heading).to_be_visible()
        expect(self._request_leave_button).to_be_visible()
        expect(self._punch_request_button).to_be_visible()
        self.assert_attendance_tabs_visible()

    def assert_navigation_visible(self) -> None:
        expect(self._nav_dashboard).to_be_visible()
        expect(self._nav_worklogs).to_be_visible()
        expect(self._nav_my_projects).to_be_visible()

    def assert_action_buttons_visible(self) -> None:
        expect(self._request_leave_button).to_be_visible()
        expect(self._punch_request_button).to_be_visible()
        expect(self._view_report_button).to_be_visible()
        self.assert_attendance_tabs_visible()

    def assert_attendance_tabs_visible(self) -> None:
        for tab_name in self.ATTENDANCE_TABS:
            expect(self.page.get_by_role("tab", name=tab_name)).to_be_visible()

    def assert_weekly_hours_section_visible(self) -> None:
        expect(self._weekly_hours_heading).to_be_visible()
        expect(self._view_report_button).to_be_visible()
        expect(self.page.get_by_text("Hours logged this week")).to_be_visible()

    def assert_leave_listing_tab_content(self) -> None:
        self.click_tab("Leave listing")
        panel = self.page.get_by_role("tabpanel", name="Leave listing")
        expect(panel.get_by_role("heading", name="Leave listing")).to_be_visible()
        expect(panel.get_by_role("searchbox", name="Search leave requests")).to_be_visible()
        expect(panel.get_by_label("Filter by status")).to_be_visible()
        expect(panel.get_by_label("Filter by leave type")).to_be_visible()
        expect(panel.get_by_role("button", name="Refresh leave requests")).to_be_visible()
        for column in self.LEAVE_LISTING_COLUMNS:
            expect(panel.get_by_role("columnheader", name=column)).to_be_visible()

    def assert_overtime_tab_content(self) -> None:
        self.click_tab("Overtime")
        panel = self.page.get_by_role("tabpanel", name="Overtime")
        expect(panel.get_by_role("heading", name="Overtime")).to_be_visible()
        expect(panel.get_by_text("Logging time on weekends or")).to_be_visible()
        expect(panel.get_by_text("Balance remaining")).to_be_visible()
        expect(panel.get_by_text("Available to request")).to_be_visible()
        expect(panel.get_by_text("Available for leave")).to_be_visible()
        expect(panel.get_by_text("Cycle expires")).to_be_visible()
        expect(
            panel.get_by_role("searchbox", name="Search compensation requests")
        ).to_be_visible()
        expect(panel.get_by_label("Filter by status")).to_be_visible()
        expect(
            panel.get_by_role("button", name="Refresh compensation requests")
        ).to_be_visible()
        for column in self.OVERTIME_COLUMNS:
            if column == "Status":
                expect(
                    panel.get_by_role("columnheader", name="Status", exact=True)
                ).to_be_visible()
            else:
                expect(panel.get_by_role("columnheader", name=column)).to_be_visible()

    def assert_recent_attendance_tab_content(self) -> None:
        self.click_tab("Recent attendance")
        panel = self.page.get_by_role("tabpanel", name="Recent attendance")
        expect(panel.get_by_role("heading", name="Recent attendance")).to_be_visible()
        expect(panel.get_by_role("button", name="View full log")).to_be_visible()
        for column in self.RECENT_ATTENDANCE_COLUMNS:
            expect(panel.get_by_role("columnheader", name=column)).to_be_visible()

    def assert_my_punch_requests_tab_content(self) -> None:
        self.click_tab("My punch requests")
        panel = self.page.get_by_role("tabpanel", name="My punch requests")
        expect(panel.get_by_role("heading", name="My punch requests")).to_be_visible()
        expect(panel.get_by_text("History of punch corrections")).to_be_visible()
        for column in self.PUNCH_REQUESTS_COLUMNS:
            expect(panel.get_by_role("columnheader", name=column)).to_be_visible()

    def assert_user_profile_visible(self, email: str) -> None:
        expect(self.page.get_by_text(email, exact=False)).to_be_visible()
