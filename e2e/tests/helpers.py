"""Shared helpers for the e2e tests."""
from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

import requests
from PIL import Image

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
TEMPLATE_PATH = (
    Path(__file__).parents[2] / "custom_components" / "energy_post" / "template_post.png"
)
# Collected result images for manual inspection (repo root /test-results).
RESULTS_DIR = Path(__file__).parents[2] / "test-results"


def assert_valid_png(data: bytes, check_template_size: bool = True) -> Image.Image:
    """Assert the bytes are a valid PNG; optionally compare to template size."""
    assert data[:8] == PNG_MAGIC, "response is not a PNG"
    img = Image.open(io.BytesIO(data))
    img.verify()
    if check_template_size:
        with Image.open(TEMPLATE_PATH) as tpl:
            img = Image.open(io.BytesIO(data))
            assert img.size == tpl.size, (
                f"image size {img.size} != template size {tpl.size}"
            )
    return Image.open(io.BytesIO(data))


def call_generate_image(
    api: requests.Session, ha_url: str, timeout: int = 90, **data: Any
) -> dict[str, Any]:
    """Call energy_post.generate_image via REST and return the service response."""
    r = api.post(
        f"{ha_url}/api/services/energy_post/generate_image?return_response",
        json=data,
        timeout=timeout,
    )
    assert r.status_code == 200, f"service call failed: {r.status_code} {r.text[:500]}"
    payload = r.json()
    # HA has wrapped service responses differently across versions:
    # {"response": ...}, {"service_response": ...} or the bare dict.
    if isinstance(payload, dict):
        for key in ("response", "service_response"):
            if isinstance(payload.get(key), dict) and (
                "filename" in payload[key] or "content" in payload[key]
            ):
                return payload[key]
        if "filename" in payload or "content" in payload:
            return payload
    raise AssertionError(f"unexpected service response shape: {payload!r}")


def generate_png_bytes(
    api: requests.Session, ha_url: str, **data: Any
) -> bytes:
    """Call the service with download=true and return decoded PNG bytes.

    The image is also written to <repo>/test-results/<filename> so generated
    artifacts stay available for manual inspection after the run.
    """
    resp = call_generate_image(api, ha_url, download=True, **data)
    png = base64.b64decode(resp["content"])
    RESULTS_DIR.mkdir(exist_ok=True)
    name = data.get("filename") or resp.get("filename") or "generated.png"
    (RESULTS_DIR / Path(name).name).write_bytes(png)
    return png
