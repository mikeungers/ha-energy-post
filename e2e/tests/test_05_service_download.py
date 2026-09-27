"""Service test: download=true returns the PNG as base64 in the response."""
from __future__ import annotations

from helpers import assert_valid_png, call_generate_image
import base64


def test_download_response(ha_url, auth, api, ensure_integration):
    resp = call_generate_image(
        api, ha_url, download=True, filename="e2e_download.png", period="week"
    )
    assert resp["filename"] == "e2e_download.png"
    assert resp["mime_type"] == "image/png"

    png = base64.b64decode(resp["content"])
    assert_valid_png(png)

    # download=true must not write to www
    r = api.get(f"{ha_url}/local/e2e_download.png", timeout=10)
    assert r.status_code == 404
