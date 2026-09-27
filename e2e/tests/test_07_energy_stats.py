"""E2E test for the recorder path: import statistics, verify the rendered
image changes (the seeded energy prefs use the unified grid format -> this is
the regression test for the flow_from/flow_to -> stat_energy_* bugfix).
"""
from __future__ import annotations

import io
import time
from datetime import datetime, timedelta

from helpers import assert_valid_png, generate_png_bytes
from PIL import Image, ImageChops

STAT_IDS = ["e2e:solar", "e2e:grid_import", "e2e:grid_export"]

# External statistics require the metadata source to match the
# statistic_id prefix (e2e:* -> source "e2e").
_METADATA_BASE = {
    "has_mean": False,
    "has_sum": True,
    "name": None,
    "source": "e2e",
    "unit_of_measurement": "kWh",
    "unit_class": "energy",
    "mean_type": 0,
}


def _hourly_stats(rate: float) -> list[dict]:
    """Hourly buckets for the last ~26h with linearly increasing sums."""
    now = datetime.now().astimezone().replace(minute=0, second=0, microsecond=0)
    return [
        {
            "start": (now - timedelta(hours=i)).isoformat(),
            "sum": round((26 - i) * rate, 3),
        }
        for i in range(26, 0, -1)
    ]


def _import_statistics(ws, stat_id: str, rate: float) -> None:
    stats = _hourly_stats(rate)
    try:
        ws.cmd(
            "recorder/import_statistics",
            metadata={**_METADATA_BASE, "statistic_id": stat_id},
            stats=stats,
        )
    except RuntimeError:
        # Older HA versions reject unit_class/mean_type - retry minimal.
        metadata = {k: v for k, v in _METADATA_BASE.items()
                    if k not in ("unit_class", "mean_type")}
        ws.cmd(
            "recorder/import_statistics",
            metadata={**metadata, "statistic_id": stat_id},
            stats=stats,
        )


def test_energy_statistics_affect_image(ha_url, auth, api, ws, ensure_integration):
    # 1. Clean slate -> baseline image with zeros
    ws.cmd("recorder/clear_statistics", statistic_ids=STAT_IDS)
    png_zero = generate_png_bytes(api, ha_url, filename="e2e_zero.png")
    assert_valid_png(png_zero)

    # 2. Import recorder statistics for the seeded energy sources
    _import_statistics(ws, "e2e:solar", rate=2.5)       # ~2.5 kWh/h PV
    _import_statistics(ws, "e2e:grid_import", rate=1.0)  # ~1 kWh/h import
    _import_statistics(ws, "e2e:grid_export", rate=0.4)  # ~0.4 kWh/h export

    # The recorder commits imported statistics asynchronously - poll until
    # they become visible. The ws API shape varies across versions, so a
    # RuntimeError just ends the wait; the pixel diff below is the real check.
    deadline = time.monotonic() + 120
    stats_visible = False
    while time.monotonic() < deadline:
        now = datetime.now().astimezone()
        try:
            result = ws.cmd(
                "recorder/statistics_during_period",
                start_time=(now - timedelta(hours=26)).isoformat(),
                end_time=now.isoformat(),
                statistic_ids=STAT_IDS,
                period="hour",
                types=["sum"],
            )
            if result and any(result.get(s) for s in STAT_IDS):
                stats_visible = True
                break
        except RuntimeError:
            break
        time.sleep(5)
    if not stats_visible:
        print("WARN: imported statistics not yet visible via ws query")

    # 3. Generate again -> the values overlay must differ from the zero image
    png_stats = generate_png_bytes(api, ha_url, filename="e2e_stats_data.png")
    assert_valid_png(png_stats)
    assert png_stats != png_zero

    # RGB diff: getbbox() on an RGBA diff only considers the alpha
    # channel (all-zero here) and would wrongly report no change.
    img_zero = Image.open(io.BytesIO(png_zero)).convert("RGB")
    img_stats = Image.open(io.BytesIO(png_stats)).convert("RGB")
    diff = ImageChops.difference(img_zero, img_stats)
    assert diff.getbbox() is not None, (
        "imported energy statistics did not change the image - "
        "check the energy prefs parsing in image_generator.py"
    )
