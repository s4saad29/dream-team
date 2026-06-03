import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from utils.auth_helper import STORAGE_STATE_PATH

out_lines: list[str] = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        storage_state=str(STORAGE_STATE_PATH),
        base_url="https://team.addo.ai",
    )
    page = context.new_page()
    page.goto("/dashboard", wait_until="networkidle")
    page.get_by_role("button", name="User Profile").click()
    page.get_by_role("menuitem", name="My Profile").click()
    page.wait_for_load_state("networkidle")

    out_lines.append(f"url: {page.url}")
    out_lines.append(f"title: {page.title()}")

    for role in ("heading", "button", "link", "menuitem", "textbox"):
        loc = page.get_by_role(role)
        for i in range(min(loc.count(), 30)):
            el = loc.nth(i)
            name = (el.inner_text() or el.get_attribute("aria-label") or "").strip()
            if name:
                out_lines.append(f"{role}: {name[:80]}")

    out_lines.append("--- body ---")
    out_lines.append(page.locator("body").inner_text())

    out_path = Path(__file__).resolve().parent.parent / "auth" / "profile_detail.txt"
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    context.close()
    browser.close()
