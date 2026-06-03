import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from utils.auth_helper import STORAGE_STATE_PATH

lines: list[str] = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        storage_state=str(STORAGE_STATE_PATH),
        base_url="https://team.addo.ai",
    )
    page = context.new_page()

    for path in ("/profile", "/settings", "/account"):
        page.goto(path, wait_until="networkidle", timeout=60000)
        lines.append(f"=== {path} -> {page.url} ===")
        lines.append(f"Title: {page.title()}")
        headings = page.locator("h1, h2, h3")
        for i in range(min(headings.count(), 10)):
            lines.append(f"  heading: {headings.nth(i).inner_text()[:80]}")
        buttons = page.get_by_role("button")
        for i in range(min(buttons.count(), 20)):
            text = (buttons.nth(i).inner_text() or "").strip()
            if text:
                lines.append(f"  button: {text[:60]}")
        links = page.locator("a[href]")
        for i in range(min(links.count(), 25)):
            link = links.nth(i)
            text = (link.inner_text() or "").strip()
            href = link.get_attribute("href") or ""
            if text and len(text) < 60:
                lines.append(f"  link: {text!r} -> {href[:70]}")
        body = page.locator("body").inner_text()[:600].replace("\n", " | ")
        lines.append(f"body: {body}")
        lines.append("")

    page.goto("/dashboard", wait_until="networkidle")
    profile_btn = page.get_by_role("button", name="User Profile")
    lines.append("=== dashboard User Profile button ===")
    lines.append(f"count: {profile_btn.count()}")
    if profile_btn.count():
        profile_btn.click()
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")
        lines.append(f"after click url: {page.url}")
        lines.append(f"Title: {page.title()}")
        body = page.locator("body").inner_text()[:800].replace("\n", " | ")
        lines.append(f"body: {body}")

    out = Path(__file__).resolve().parent.parent / "auth" / "profile_explore.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    context.close()
    browser.close()
