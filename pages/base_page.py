import re

from playwright.sync_api import Locator, Page, expect

from config.settings import settings


class BasePage:
    """Base class for all page objects."""

    path: str = "/"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.timeout = settings.default_timeout

    @property
    def url(self) -> str:
        return f"{settings.base_url}{self.path}"

    def navigate(self) -> None:
        self.page.goto(self.path, wait_until="domcontentloaded")

    def wait_for_loaded(self) -> None:
        self.page.wait_for_load_state("networkidle")

    def locator(self, selector: str) -> Locator:
        return self.page.locator(selector)

    def expect_title_contains(self, text: str) -> None:
        expect(self.page).to_have_title(text, timeout=self.timeout)

    def expect_url_contains(self, fragment: str) -> None:
        pattern = re.compile(rf"{re.escape(fragment)}")
        expect(self.page).to_have_url(pattern, timeout=self.timeout)

    def take_screenshot(self, name: str) -> None:
        settings.screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = settings.screenshot_dir / f"{name}.png"
        self.page.screenshot(path=str(path), full_page=True)
