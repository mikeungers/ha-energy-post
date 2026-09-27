"""Service test: device energy sensors passed via the devices parameter."""
from __future__ import annotations

import io

from helpers import assert_valid_png, generate_png_bytes
from PIL import Image, ImageChops

DEVICE = "sensor.e2e_warmepumpe"


def _set_device(api, ha_url, state: float) -> None:
    r = api.post(
        f"{ha_url}/api/states/{DEVICE}",
        json={
            "state": str(state),
            "attributes": {
                "friendly_name": "E2E Wärmepumpe",
                "unit_of_measurement": "kWh",
                "device_class": "energy",
                "state_class": "total_increasing",
            },
        },
        timeout=10,
    )
    assert r.status_code in (200, 201)


def test_devices_in_image(ha_url, auth, api, ensure_integration):
    _set_device(api, ha_url, 12.3)

    png_with = generate_png_bytes(
        api, ha_url, filename="e2e_devices.png", devices=[DEVICE]
    )
    assert_valid_png(png_with)

    # The device bubble should change the rendered image compared to a call
    # without devices.
    png_without = generate_png_bytes(api, ha_url, filename="e2e_nodev.png")
    img_with = Image.open(io.BytesIO(png_with)).convert("RGB")
    img_without = Image.open(io.BytesIO(png_without)).convert("RGB")
    diff = ImageChops.difference(img_with, img_without)
    assert diff.getbbox() is not None, "device values did not change the image"
