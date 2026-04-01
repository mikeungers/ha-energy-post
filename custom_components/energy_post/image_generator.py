"""Image generator for energy statistics."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
import os
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .template_renderer import TemplateRenderer

_LOGGER = logging.getLogger(__name__)


class EnergyImageGenerator:
    """Generate images for energy statistics."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the image generator."""
        self.hass = hass

    async def generate_story_image(
        self,
        period: str = "day",
        devices: list[str] | None = None,
        title: str | None = None,
    ) -> bytes:
        """Generate an Instagram story image with energy statistics."""
        energy_data = await self._fetch_energy_data(period, devices)
        
        template_path = os.path.join(os.path.dirname(__file__), "template_post.png")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(
                f"Template image not found at {template_path}. "
                "Please ensure template_post.png exists in the integration folder."
            )
        
        if title is None:
            title = self._get_period_title(period)
        
        # Nutze TemplateRenderer für die Grafik-Logik (keine HA-Dependencies)
        renderer = TemplateRenderer(template_path)
        return renderer.render_energy_data(energy_data, title)

    async def _fetch_energy_data(
        self, period: str, devices: list[str] | None = None
    ) -> dict[str, Any]:
        """Fetch energy data from Home Assistant."""
        end_time = dt_util.now()
        
        if period == "day":
            start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_time = end_time - timedelta(days=7)
        elif period == "month":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=1)
        
        energy_data = {
            "pv_production": 0.0,
            "grid_import": 0.0,
            "grid_export": 0.0,
            "consumption": 0.0,
            "devices": {},
            "chart_data": {
                "timestamps": [],
                "pv_production": [],
                "consumption": [],
                "grid_import": [],
                "grid_export": [],
            }
        }
        
        try:
            recorder = self.hass.data.get("recorder_instance")
            if recorder:
                energy_data = await self._fetch_from_recorder(
                    start_time, end_time, devices
                )
        except Exception as err:
            _LOGGER.error("Error fetching energy data: %s", err)
        
        return energy_data

    async def _fetch_from_recorder(
        self, start_time: datetime, end_time: datetime, devices: list[str] | None
    ) -> dict[str, Any]:
        """Fetch data from the recorder."""
        from homeassistant.components.recorder.statistics import (
            statistics_during_period,
        )
        
        energy_data = {
            "pv_production": 0.0,
            "grid_import": 0.0,
            "grid_export": 0.0,
            "consumption": 0.0,
            "devices": {},
            "chart_data": {
                "timestamps": [],
                "pv_production": [],
                "consumption": [],
                "grid_import": [],
                "grid_export": [],
            }
        }
        
        entity_mapping = {
            "pv_production": "sensor.solar_production",
            "grid_import": "sensor.grid_import",
            "grid_export": "sensor.grid_export",
            "consumption": "sensor.total_consumption",
        }
        
        for key, entity_id in entity_mapping.items():
            state = self.hass.states.get(entity_id)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    energy_data[key] = float(state.state)
                except (ValueError, TypeError):
                    _LOGGER.warning("Could not convert state for %s", entity_id)
        
        if devices:
            for device_entity in devices:
                state = self.hass.states.get(device_entity)
                if state and state.state not in ("unknown", "unavailable"):
                    try:
                        device_name = state.attributes.get("friendly_name", device_entity)
                        energy_data["devices"][device_name] = float(state.state)
                    except (ValueError, TypeError):
                        _LOGGER.warning("Could not convert state for %s", device_entity)
        
        return energy_data

    def _get_period_title(self, period: str) -> str:
        """Get the title for the period."""
        titles = {
            "day": "Energie Heute",
            "week": "Energie diese Woche",
            "month": "Energie diesen Monat",
        }
        return titles.get(period, "Energie Statistik")
