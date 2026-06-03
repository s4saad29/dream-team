import re
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError, expect

from config.settings import settings
from pages.login_page import LoginPage
from pages.microsoft_login_page import MicrosoftLoginPage

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORAGE_STATE_PATH = PROJECT_ROOT / "auth" / "storage_state.json"


def storage_state_exists() -> bool:
    return STORAGE_STATE_PATH.is_file()


def save_storage_state(context: BrowserContext) -> None:
    """Persist cookies/localStorage so the next run can reuse the session."""
    STORAGE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(STORAGE_STATE_PATH))


def save_authenticated_session(page: Page) -> None:
    """Save storage after Microsoft SSO when the app accepted the session."""
    page.wait_for_load_state("networkidle", timeout=120000)
    if not is_authenticated(page):
        raise RuntimeError("Cannot save storage: session is not authenticated.")
    save_storage_state(page.context)


def is_authenticated(page: Page) -> bool:
    """Return True when the app accepted the session (not on login / token errors)."""
    page.wait_for_load_state("domcontentloaded")

    if "/login" in page.url:
        return False

    timeout_messages = (
        "Session timeout",
        "please login again",
        "Given token not valid",
        "token not valid",
    )
    body = page.locator("body")
    for message in timeout_messages:
        if body.get_by_text(message, exact=False).count():
            return False

    # Authenticated app shell: dashboard or profile routes
    if re.search(r"/(dashboard|profile|worklogs|my-projects)", page.url):
        try:
            page.wait_for_url(re.compile(r"/login"), timeout=3000)
            return False
        except PlaywrightTimeoutError:
            return True

    return "/login" not in page.url


def login_via_microsoft(page: Page, *, mfa_timeout_ms: int = 300000) -> None:
    """Sign in through Microsoft SSO; waits for MFA to complete if required."""
    login = LoginPage(page)
    login.navigate()
    login.click_microsoft_login()

    microsoft = MicrosoftLoginPage(page)
    microsoft.login_with_credentials(settings.test_user_email, settings.test_user_password)
    page.wait_for_url(
        lambda url: "team.addo.ai" in url and "/login" not in url,
        timeout=mfa_timeout_ms,
    )
    microsoft.accept_stay_signed_in_if_prompted()
    page.wait_for_load_state("networkidle", timeout=120000)


def ensure_authenticated_context(
    context: BrowserContext,
    *,
    entry_path: str = "/dashboard",
    refresh_storage: bool = True,
) -> Page:
    """
    Open a page using the given context and refresh SSO login if storage is stale.
    Updates auth/storage_state.json after a successful re-login.
    """
    page = context.new_page()
    page.set_default_timeout(settings.default_timeout)
    page.goto(entry_path, wait_until="domcontentloaded", timeout=60000)

    if is_authenticated(page):
        return page

    if not settings.has_credentials:
        page.close()
        raise RuntimeError(
            "Session expired and credentials are missing. "
            "Set TEST_USER_EMAIL and TEST_USER_PASSWORD in .env, or run "
            "scripts/save_auth_and_explore_dashboard.py"
        )

    login_via_microsoft(page)

    if not is_authenticated(page):
        page.close()
        raise RuntimeError("Microsoft login completed but session is still invalid.")

    if refresh_storage:
        save_storage_state(context)

    return page


def assert_on_authenticated_app(page: Page) -> None:
    expect(page).not_to_have_url(re.compile(r"/login"), timeout=settings.default_timeout)
