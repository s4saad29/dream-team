from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class WorklogsPage(BasePage):
    """Page object for https://team.addo.ai/worklogs"""

    path = "/worklogs"

    def assert_on_worklogs(self) -> None:
        self.expect_url_contains("/worklogs")
        expect(self.page.get_by_role("heading", name="Worklogs")).to_be_visible(
            timeout=self.timeout
        )
        expect(self.page.get_by_text("Record effort by day against")).to_be_visible()
