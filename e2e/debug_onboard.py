"""Manual debug helper: run the onboarding loop once against the live container."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import conftest  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(locale="en-US")
    ctx.grant_permissions(["geolocation"])
    ctx.set_geolocation({"latitude": 52.52, "longitude": 13.405})
    pg = ctx.new_page()
    try:
        conftest._onboard(pg)
        print("ONBOARDED OK, url:", pg.url)
        print(
            "tokens set:",
            pg.evaluate("() => localStorage.getItem('hassTokens') !== null"),
        )
    except Exception as e:  # noqa: BLE001
        print("FAILED:", e)
        conftest.OUTPUT_DIR.mkdir(exist_ok=True)
        pg.screenshot(
            path=str(conftest.OUTPUT_DIR / "onboard_fail.png"), full_page=True
        )
        print("URL:", pg.url)
        print(pg.locator("body").inner_text()[:800])
    b.close()
