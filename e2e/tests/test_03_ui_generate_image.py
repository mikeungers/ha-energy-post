"""UI test: trigger energy_post.generate_image via Developer tools -> Actions.

The service is invoked with its defaults (filename=energy_stats.png); success
is asserted via the energy_post_image_generated event on the websocket.
"""
from __future__ import annotations

import re


def test_generate_image_via_ui(ha_url, auth, api, ws, ensure_integration, page):
    # Listen for the event before clicking the button.
    ws.cmd("subscribe_events", event_type="energy_post_image_generated")

    page.goto(f"{ha_url}/developer-tools/action")
    page.wait_for_selector(
        "ha-service-picker, ha-action-service-picker", timeout=60_000
    )

    # Pick the service in the combo box: click to focus/open, then type.
    # (fill() on the inner input times out - it is read-only until focused.)
    picker = page.locator(
        "ha-service-picker, ha-action-service-picker"
    ).first
    picker.click()
    page.wait_for_timeout(800)
    page.keyboard.type("energy_post.generate_image")
    page.wait_for_timeout(1000)
    option = page.locator(
        "vaadin-combo-box-item, ha-combo-box-item, mwc-list-item",
        has_text="generate_image",
    )
    if option.count():
        option.first.click()
    else:
        page.keyboard.press("Enter")

    # Fire the action.
    page.get_by_role(
        "button", name=re.compile(r"perform action|call service", re.I)
    ).first.click()

    event = ws.recv_event(timeout=90)
    assert event["data"]["filename"] == "energy_stats.png"

    # The file must be served via /local/.
    r = api.get(f"{ha_url}/local/energy_stats.png", timeout=10)
    assert r.status_code == 200
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"
