"""UI test: add the energy_post integration via the config flow in the UI."""
from __future__ import annotations

import re


def _entry_exists(api, ha_url) -> bool:
    r = api.get(f"{ha_url}/api/config/config_entries/entry", timeout=10)
    r.raise_for_status()
    return any(e["domain"] == "energy_post" for e in r.json())


def test_add_integration_via_ui(ha_url, auth, api, page):
    if _entry_exists(api, ha_url):
        # Already created (e.g. previous run). Verify it shows up in the UI.
        page.goto(f"{ha_url}/config/integrations")
        page.wait_for_selector("text=Energy Post", timeout=60_000)
        return

    page.goto(f"{ha_url}/config/integrations")
    page.wait_for_selector("ha-fab", timeout=60_000)

    # "Add integration" FAB
    page.locator("ha-fab").first.click()

    # Search field in the add-integration dialog
    search = page.locator("dialog-add-integration")
    search.locator("input").fill("energy post")

    # Click the result row
    page.locator("text=Energy Post").last.click()

    # Config flow form: fields have defaults, submit directly
    submit = page.get_by_role(
        "button", name=re.compile(r"submit|add|create|ok", re.I)
    )
    submit.last.click()

    # Success dialog → close it
    page.get_by_role(
        "button", name=re.compile(r"finish|close|ok", re.I)
    ).last.click(timeout=30_000)

    assert _entry_exists(api, ha_url), "energy_post config entry missing"
