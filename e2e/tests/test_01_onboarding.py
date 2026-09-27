"""Smoke test: Home Assistant is up and onboarding/login succeeded."""
from __future__ import annotations


def test_dashboard_reachable(ha_url, auth, page):
    """The session auth fixture ran onboarding (or login) via the UI.

    Here we verify the logged-in page actually reaches the HA dashboard.
    """
    page.goto(ha_url)
    page.wait_for_selector("home-assistant", timeout=60_000)
    page.wait_for_selector("ha-sidebar", timeout=60_000)
    assert "onboarding" not in page.url


def test_api_authenticated(ha_url, auth, api):
    """The long-lived token works against the REST API."""
    r = api.get(f"{ha_url}/api/", timeout=10)
    assert r.status_code == 200
    assert r.json()["message"] == "API running."
