import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class ProfilePage(BasePage):
    """Page object for user profile (/profile/{id})."""

    path = "/profile"

    PROFILE_TABS = (
        "Employee Info",
        "Address Info",
        "Contact Info",
        "Qualifications",
        "Experience",
        "Certification",
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._user_profile_button = page.get_by_role("button", name="User Profile")
        self._my_profile_menuitem = page.get_by_role("menuitem", name="My Profile")
        self._logout_menuitem = page.get_by_role("menuitem", name="Logout")
        self._employee_info_panel = page.get_by_role("tabpanel", name="Employee Info")
        self._nav_dashboard = page.get_by_role("link", name="Dashboard", exact=True)
        self._nav_worklogs = page.get_by_role("link", name="Worklogs", exact=True)
        self._nav_my_projects = page.get_by_role("link", name="My Projects", exact=True)
        self._save_changes_button = page.get_by_role("button", name="Save Changes")
        self._cancel_button = page.get_by_role("button", name="Cancel")

    def open_from_dashboard(self) -> None:
        self.page.goto("/dashboard", wait_until="domcontentloaded")
        self._user_profile_button.click()
        self._my_profile_menuitem.click()
        self.page.wait_for_load_state("domcontentloaded")

    def open_profile_menu(self) -> None:
        self._user_profile_button.click()

    def click_my_profile(self) -> None:
        self._my_profile_menuitem.click()
        self.page.wait_for_load_state("domcontentloaded")

    def click_logout(self) -> None:
        self._logout_menuitem.click()
        self.page.wait_for_load_state("domcontentloaded")

    def click_tab(self, tab_name: str) -> None:
        self.page.get_by_role("tab", name=tab_name).click()

    def click_nav_dashboard(self) -> None:
        self._nav_dashboard.click()

    def assert_on_profile_page(self) -> None:
        expect(self.page).to_have_url(re.compile(r"/profile/\d+"), timeout=self.timeout)

    def assert_profile_menu_visible(self) -> None:
        expect(self._my_profile_menuitem).to_be_visible()
        expect(self._logout_menuitem).to_be_visible()

    def assert_profile_header_visible(self) -> None:
        expect(self.page.get_by_role("heading", level=3)).to_be_visible()
        expect(self.page.get_by_role("tab", name="Employee Info")).to_be_visible()

    def assert_profile_tabs_visible(self) -> None:
        self.assert_profile_section_menu_items()

    def assert_profile_section_menu_items(self) -> None:
        """Profile section tab bar must include all menu items (see PROFILE_TABS)."""
        tablist = self.page.get_by_role("tablist")
        expect(tablist).to_be_visible(timeout=self.timeout)

        tabs = tablist.get_by_role("tab")
        expect(tabs).to_have_count(len(self.PROFILE_TABS))

        for index, tab_name in enumerate(self.PROFILE_TABS):
            tab = tabs.nth(index)
            expect(tab).to_be_visible()
            expect(tab).to_have_text(tab_name)

        expect(
            self.page.get_by_role("tab", name="Employee Info", selected=True)
        ).to_be_visible()

    def assert_employee_info_form_visible(self, email: str) -> None:
        expect(self._employee_info_panel.get_by_role("heading", name="Personal Info")).to_be_visible()
        expect(self._employee_info_panel.get_by_role("textbox", name="Email")).to_have_value(email)
        expect(self._employee_info_panel.get_by_role("textbox", name="First Name")).to_be_visible()
        expect(self._employee_info_panel.get_by_role("textbox", name="Last Name")).to_be_visible()
        expect(self._employee_info_panel.get_by_text("Department", exact=True)).to_be_visible()
        expect(self._employee_info_panel.get_by_text("Designation", exact=True)).to_be_visible()

    def assert_profile_actions_visible(self) -> None:
        expect(self._save_changes_button).to_be_visible()
        expect(self._cancel_button).to_be_visible()

    def assert_navigation_visible(self) -> None:
        expect(self._nav_dashboard).to_be_visible()
        expect(self._nav_worklogs).to_be_visible()
        expect(self._nav_my_projects).to_be_visible()

    def assert_profile_loaded(self, email: str) -> None:
        self.assert_on_profile_page()
        self.assert_profile_header_visible()
        self.assert_profile_tabs_visible()
        self.assert_employee_info_form_visible(email)
        self.assert_profile_actions_visible()
        self.assert_navigation_visible()

    def assert_tab_selected(self, tab_name: str) -> None:
        expect(self.page.get_by_role("tab", name=tab_name, selected=True)).to_be_visible()
