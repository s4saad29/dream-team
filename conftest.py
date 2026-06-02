import base64
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page

from config.settings import settings
from pages.dashboard_page import DashboardPage
from pages.profile_page import ProfilePage
from pages.forgot_password_page import ForgotPasswordPage
from pages.login_page import LoginPage
from pages.microsoft_login_page import MicrosoftLoginPage
from utils.auth_helper import STORAGE_STATE_PATH, login_via_microsoft, storage_state_exists


def _resolve_page(item: pytest.Item) -> Page | None:
    """Find the Playwright page from test fixtures or page objects."""
    for name in ("page", "authenticated_page"):
        if name in item.funcargs:
            return item.funcargs[name]
    for value in item.funcargs.values():
        page = getattr(value, "page", None)
        if page is not None:
            return page
    return None


def _save_failure_screenshot(page: Page, nodeid: str) -> str:
    settings.screenshot_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w.-]+", "_", nodeid)
    path = settings.screenshot_dir / f"{safe_name}.png"
    page.screenshot(path=str(path), full_page=True)
    return str(path)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "call" or not report.failed:
        return

    page = _resolve_page(item)
    if page is None:
        return

    try:
        screenshot_path = _save_failure_screenshot(page, item.nodeid)
        pytest_html = item.config.pluginmanager.getplugin("html")
        if pytest_html is not None:
            extras = getattr(report, "extras", [])
            image_data = base64.b64encode(Path(screenshot_path).read_bytes()).decode(
                "ascii"
            )
            extras.append(pytest_html.extras.image(f"data:image/png;base64,{image_data}"))
            report.extras = extras
    except Exception as exc:
        report.sections.append(("Screenshot error", str(exc)))


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {
        **browser_type_launch_args,
        "headless": settings.headless,
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "base_url": settings.base_url,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture(autouse=True)
def set_default_timeout(page: Page):
    page.set_default_timeout(settings.default_timeout)


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    return LoginPage(page)


@pytest.fixture
def forgot_password_page(page: Page) -> ForgotPasswordPage:
    return ForgotPasswordPage(page)


@pytest.fixture
def microsoft_login_page(page: Page) -> MicrosoftLoginPage:
    return MicrosoftLoginPage(page)


@pytest.fixture
def authenticated_page(browser, browser_context_args) -> Page:
    """Fresh browser context with saved auth or Microsoft SSO (not shared with login tests)."""
    if not storage_state_exists() and not settings.has_credentials:
        pytest.skip(
            "No auth/storage_state.json — run scripts/save_auth_and_explore_dashboard.py "
            "or set TEST_USER_EMAIL and TEST_USER_PASSWORD in .env"
        )

    context_args = {**browser_context_args}
    if storage_state_exists():
        context_args["storage_state"] = str(STORAGE_STATE_PATH)

    context = browser.new_context(**context_args)
    page = context.new_page()
    page.set_default_timeout(settings.default_timeout)

    try:
        if storage_state_exists():
            page.goto("/dashboard", wait_until="domcontentloaded", timeout=60000)
        else:
            login_via_microsoft(page)
        yield page
    finally:
        context.close()


@pytest.fixture
def dashboard_page(authenticated_page: Page) -> DashboardPage:
    return DashboardPage(authenticated_page)


@pytest.fixture
def profile_page(authenticated_page: Page) -> ProfilePage:
    return ProfilePage(authenticated_page)
