"""The Energy Post integration for Home Assistant."""
from __future__ import annotations

import base64
import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv

from .image_generator import EnergyImageGenerator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "energy_post"
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_GENERATE_IMAGE = "generate_image"

GENERATE_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Optional("period", default="day"): vol.In(["day", "week", "month"]),
        vol.Optional("devices", default=[]): vol.All(cv.ensure_list, [cv.entity_id]),
        vol.Optional("title"): cv.string,
        vol.Optional("filename", default="energy_stats.png"): cv.string,
        vol.Optional("download", default=False): cv.boolean,
    }
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Energy Post component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Energy Post from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_generate_image(call: ServiceCall) -> ServiceResponse:
        """Handle the generate_image service call."""
        period = call.data.get("period", "day")
        devices = call.data.get("devices", [])
        title = call.data.get("title")
        filename = call.data.get("filename", "energy_stats.png")
        download = call.data.get("download", False)

        _LOGGER.info(
            "Generating energy image for period: %s, devices: %s, download: %s", 
            period, devices, download
        )

        generator = EnergyImageGenerator(hass)
        
        try:
            image_bytes = await generator.generate_story_image(
                period=period,
                devices=devices,
                title=title,
            )

            # Wenn download=True, gebe die Datei direkt zurück
            if download:
                _LOGGER.info("Returning image for download: %s", filename)
                # Base64-Encoding für Home Assistant Service Response
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                return {
                    "filename": filename,
                    "content": image_base64,
                    "mime_type": "image/png",
                }
            
            # Ansonsten speichere im www-Ordner wie bisher
            output_path = hass.config.path("www", filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "wb") as f:
                f.write(image_bytes)

            _LOGGER.info("Energy image saved to: %s", output_path)
            
            hass.bus.async_fire(
                f"{DOMAIN}_image_generated",
                {
                    "filename": filename,
                    "path": output_path,
                    "url": f"/local/{filename}",
                },
            )
            
            return {
                "filename": filename,
                "path": output_path,
                "url": f"/local/{filename}",
            }

        except Exception as err:
            _LOGGER.error("Error generating energy image: %s", err)
            raise

    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE_IMAGE,
        handle_generate_image,
        schema=GENERATE_IMAGE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
