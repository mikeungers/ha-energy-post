"""Service test: generate_image writes a file to www and fires an event."""
from __future__ import annotations

from helpers import assert_valid_png, call_generate_image


def test_service_writes_file(ha_url, auth, api, ws, ensure_integration):
    ws.cmd("subscribe_events", event_type="energy_post_image_generated")

    resp = call_generate_image(api, ha_url, filename="e2e_stats.png", period="day")
    assert resp["filename"] == "e2e_stats.png"
    assert resp["url"] == "/local/e2e_stats.png"

    event = ws.recv_event(timeout=60)
    assert event["event_type"] == "energy_post_image_generated"
    assert event["data"]["filename"] == "e2e_stats.png"
    assert event["data"]["url"] == "/local/e2e_stats.png"

    r = api.get(f"{ha_url}/local/e2e_stats.png", timeout=10)
    assert r.status_code == 200
    assert_valid_png(r.content)
