import base64
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
from playwright.sync_api import Page

from config.settings import settings
from pages.dashboard_page import DashboardPage
from pages.profile_page import ProfilePage
from pages.forgot_password_page import ForgotPasswordPage
from pages.login_page import LoginPage
from pages.microsoft_login_page import MicrosoftLoginPage
from utils.auth_helper import (
    STORAGE_STATE_PATH,
    ensure_authenticated_context,
    is_authenticated,
    storage_state_exists,
)
from utils.report_dashboard import TestResult, generate_dashboard

_test_results: list[TestResult] = []
_session_started_at: datetime | None = None

# Full-suite execution order (login → forgot password → profile → dashboard → logout)
TEST_MODULE_ORDER = (
    "test_login_page.py",
    "test_forgot_password_page.py",
    "test_profile_page.py",
    "test_dashboard_page.py",
    "test_logout_page.py",
)

# Microsoft SSO login runs last so it refreshes auth/storage_state.json before
# authenticated tests in the same pytest session.
LOGIN_TEST_ORDER = (
    "test_root_redirects_to_login",
    "test_login_page_displays_form_elements",
    "test_forgot_password_navigation",
    "test_login_button_disabled_when_form_empty",
    "test_invalid_credentials_remain_on_login",
    "test_log_in_with_microsoft_redirects_to_microsoft_sso",
)


def _test_function_name(item: pytest.Item) -> str:
    return item.originalname or item.name.split("[")[0]


def pytest_collection_modifyitems(session, config, items):
    module_order = {name: index for index, name in enumerate(TEST_MODULE_ORDER)}
    login_order = {name: index for index, name in enumerate(LOGIN_TEST_ORDER)}

    def sort_key(item: pytest.Item) -> tuple:
        module_name = Path(item.fspath).name
        module_rank = module_order.get(module_name, len(TEST_MODULE_ORDER))
        test_rank = login_order.get(_test_function_name(item), 0)
        if module_name != "test_login_page.py":
            test_rank = 0
        return (module_rank, test_rank, item.nodeid)

    items.sort(key=sort_key)


def pytest_sessionstart(session: pytest.Session) -> None:
    global _session_started_at
    _test_results.clear()
    _session_started_at = datetime.now(timezone.utc)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    started = _session_started_at or datetime.now(timezone.utc)
    duration = (datetime.now(timezone.utc) - started).total_seconds()
    dashboard_path = generate_dashboard(
        _test_results,
        started_at=started,
        duration_seconds=duration,
        exit_status=exitstatus,
    )
    print(f"\nTest dashboard: {dashboard_path}")


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

    if report.when == "call":
        _test_results.append(
            TestResult(
                nodeid=item.nodeid,
                outcome=report.outcome,
                duration=report.duration,
                module=Path(item.fspath).name,
            )
        )

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
def browser_name() -> str:
    return settings.browser


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
def requires_auth():
    """Skip the test when auth storage and credentials are both missing."""
    if not storage_state_exists() and not settings.has_credentials:
        pytest.skip(
            "Run scripts/save_auth_and_explore_dashboard.py once (headed) to create "
            "auth/storage_state.json, or set credentials in .env"
        )


@pytest.fixture(scope="session")
def valid_storage_state(browser, browser_context_args):
    """
    Ensure auth/storage_state.json contains a valid session once per test run.
    Re-authenticates via Microsoft SSO when tokens expired (Session timeout).
    """
    if not storage_state_exists() and not settings.has_credentials:
        pytest.skip(
            "No auth/storage_state.json — run scripts/save_auth_and_explore_dashboard.py "
            "or set TEST_USER_EMAIL and TEST_USER_PASSWORD in .env"
        )

    context_args = {**browser_context_args}
    if storage_state_exists():
        context_args["storage_state"] = str(STORAGE_STATE_PATH)

    context = browser.new_context(**context_args)
    try:
        page = ensure_authenticated_context(context, refresh_storage=True)
        page.close()
    except RuntimeError as exc:
        context.close()
        pytest.skip(str(exc))
    else:
        context.close()

    return STORAGE_STATE_PATH


@pytest.fixture
def authenticated_page(browser, browser_context_args, valid_storage_state) -> Page:
    """Browser page with a valid authenticated session."""
    context_args = {
        **browser_context_args,
        "storage_state": str(valid_storage_state),
    }
    context = browser.new_context(**context_args)
    page = context.new_page()
    page.set_default_timeout(settings.default_timeout)
    page.goto("/dashboard", wait_until="domcontentloaded", timeout=60000)

    if not is_authenticated(page):
        context.close()
        pytest.fail("Authenticated session became invalid during test setup.")

    try:
        yield page
    finally:
        context.close()


@pytest.fixture
def dashboard_page(authenticated_page: Page) -> DashboardPage:
    return DashboardPage(authenticated_page)


@pytest.fixture
def profile_page(authenticated_page: Page) -> ProfilePage:
    return ProfilePage(authenticated_page)
