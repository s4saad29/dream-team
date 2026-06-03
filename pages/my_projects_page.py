from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class MyProjectsPage(BasePage):
    """Page object for https://team.addo.ai/my-projects"""

    path = "/my-projects"

    def assert_on_my_projects(self) -> None:
        self.expect_url_contains("/my-projects")
        expect(
            self.page.get_by_role("link", name="My Projects", exact=True)
        ).to_be_visible(timeout=self.timeout)
