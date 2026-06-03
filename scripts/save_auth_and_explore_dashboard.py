"""
Run with HEADLESS=false. Complete MFA in the browser when prompted.
Saves auth state and writes dashboard DOM hints to auth/dashboard_explore.txt
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from config.settings import settings
from utils.auth_helper import (
    STORAGE_STATE_PATH,
    login_via_microsoft,
    save_authenticated_session,
)

load_dotenv(ROOT / ".env")
AUTH_DIR = ROOT / "auth"
AUTH_DIR.mkdir(exist_ok=True)
EXPLORE_PATH = AUTH_DIR / "dashboard_explore.txt"


def explore_page(page, label: str, lines: list) -> None:
    lines.append(f"\n=== {label} ===")
    lines.append(f"URL: {page.url}")
    lines.append(f"Title: {page.title()}")
    for tag in ("h1", "h2", "h3", "nav", "aside", "header"):
        count = page.locator(tag).count()
        if count:
            lines.append(f"{tag}: {count}")
    for i in range(min(page.locator("h1, h2, h3").count(), 15)):
        text = page.locator("h1, h2, h3").nth(i).inner_text().strip()
        if text:
            lines.append(f"  heading: {text[:100]}")
    for i in range(min(page.locator("nav a, aside a, header a").count(), 40)):
        link = page.locator("nav a, aside a, header a").nth(i)
        text = (link.inner_text() or "").strip()
        href = link.get_attribute("href") or ""
        if text:
            lines.append(f"  link: {text[:60]!r} -> {href[:80]}")
    for i in range(min(page.get_by_role("button").count(), 25)):
        btn = page.get_by_role("button").nth(i)
        text = (btn.inner_text() or "").strip()
        if text:
            lines.append(f"  button: {text[:60]!r}")
    lines.append(f"body preview: {page.locator('body').inner_text()[:500].replace(chr(10), ' | ')}")


def main() -> None:
    if not settings.has_credentials:
        raise SystemExit("Set TEST_USER_EMAIL and TEST_USER_PASSWORD in .env")

    lines: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            base_url=settings.base_url,
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()
        page.set_default_timeout(300000)

        print("\n>>> Complete MFA in the browser if prompted.")
        print(">>> Waiting up to 5 minutes for redirect back to team.addo.ai ...\n")

        login_via_microsoft(page)
        save_authenticated_session(page)
        lines.append(f"Storage saved: {STORAGE_STATE_PATH}")

        for path in ("/dashboard", "/home", "/projects", "/tasks", "/settings"):
            page.goto(path, wait_until="networkidle", timeout=120000)
            explore_page(page, path, lines)

        EXPLORE_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nExplore output: {EXPLORE_PATH}")
        print("Press Enter to close the browser...")
        input()
        browser.close()


if __name__ == "__main__":
    main()
