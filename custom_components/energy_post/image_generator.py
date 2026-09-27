"""Image generator for energy statistics."""
from __future__ import annotations

from datetime import datetime, timedelta
import inspect
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
            "battery_charge": 0.0,
            "battery_discharge": 0.0,
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
        
        if self._recorder_available():
            try:
                energy_data = await self._fetch_from_recorder(
                    start_time, end_time
                )
            except Exception:
                _LOGGER.exception("Error fetching energy data from recorder")
        else:
            _LOGGER.warning(
                "Recorder is not running - energy statistics are unavailable"
            )
        
        # Device values come from current states and work without the recorder
        if devices:
            self._collect_device_states(energy_data, devices)
        
        if not energy_data["devices"] and not any(
            energy_data[key]
            for key in (
                "pv_production",
                "grid_import",
                "grid_export",
                "consumption",
            )
        ):
            _LOGGER.warning(
                "No energy data available - the generated image will only "
                "contain zeros. Check that the Energy Dashboard is configured "
                "(Settings -> Dashboards -> Energy) and the recorder is running."
            )
        
        return energy_data
    
    def _recorder_available(self) -> bool:
        """Return True if a recorder instance is running."""
        try:
            from homeassistant.components.recorder import get_instance
        except ImportError:
            # Fallback for HA versions without the public helper
            return self.hass.data.get("recorder_instance") is not None
        try:
            return get_instance(self.hass) is not None
        except KeyError:
            return False
    
    def _collect_device_states(
        self, energy_data: dict[str, Any], devices: list[str]
    ) -> None:
        """Read current energy values of the given device entities."""
        for device_entity in devices:
            state = self.hass.states.get(device_entity)
            if not state:
                _LOGGER.warning("Device entity %s not found", device_entity)
                continue
            if state.state in ("unknown", "unavailable"):
                _LOGGER.warning(
                    "Device entity %s has no usable state", device_entity
                )
                continue
            try:
                device_name = state.attributes.get(
                    "friendly_name", device_entity
                )
                energy_data["devices"][device_name] = float(state.state)
                _LOGGER.debug(
                    "Device %s: %.2f kWh",
                    device_name,
                    energy_data["devices"][device_name],
                )
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Could not convert state for %s", device_entity
                )

    async def _fetch_from_recorder(
        self, start_time: datetime, end_time: datetime
    ) -> dict[str, Any]:
        """Fetch data from the recorder using Energy Dashboard configuration."""
        from homeassistant.components.recorder.statistics import (
            statistics_during_period,
        )
        from homeassistant.components.energy.data import async_get_manager
        
        energy_data = {
            "pv_production": 0.0,
            "grid_import": 0.0,
            "grid_export": 0.0,
            "battery_charge": 0.0,
            "battery_discharge": 0.0,
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
        
        # Versuche Energy Dashboard Konfiguration zu laden
        try:
            manager_result = async_get_manager(self.hass)
            # async_get_manager is awaitable in recent HA versions
            energy_manager = (
                await manager_result
                if inspect.isawaitable(manager_result)
                else manager_result
            )
            if not energy_manager:
                _LOGGER.warning("Energy Manager not available")
                return energy_data
            
            # EnergyManager stores the dashboard configuration in .data;
            # some HA versions expose async_get_preferences() instead.
            if hasattr(energy_manager, "async_get_preferences"):
                energy_prefs = await energy_manager.async_get_preferences()
            else:
                energy_prefs = energy_manager.data
            if not energy_prefs:
                _LOGGER.warning("Energy Dashboard not configured")
                return energy_data
                
            _LOGGER.debug("Energy Dashboard preferences loaded: %s", energy_prefs)
                
            # Solar Production
            energy_sources = energy_prefs.get("energy_sources", [])
            _LOGGER.debug("Found %d energy sources", len(energy_sources))
            
            for source in energy_sources:
                source_type = source.get("type")
                _LOGGER.debug("Processing source type: %s", source_type)
                
                if source_type == "solar":
                    stat_id = source.get("stat_energy_from")
                    if stat_id:
                        _LOGGER.info("Found solar sensor: %s", stat_id)
                        value = await self._get_statistic_sum(
                            stat_id, start_time, end_time, statistics_during_period
                        )
                        if value is not None:
                            # Accumulate - several solar sources (e.g. two
                            # inverters) may be configured.
                            energy_data["pv_production"] += value
                            _LOGGER.info("PV Production: %.2f kWh", value)
                    else:
                        _LOGGER.warning(
                            "Solar source without stat_energy_from - skipped"
                        )
                
                elif source_type == "battery":
                    # Battery sources use stat_energy_from (discharge) and
                    # stat_energy_to (charge) directly - no flow lists.
                    discharge_id = source.get("stat_energy_from")
                    if discharge_id:
                        _LOGGER.info("Found battery discharge sensor: %s", discharge_id)
                        value = await self._get_statistic_sum(
                            discharge_id, start_time, end_time, statistics_during_period
                        )
                        if value is not None:
                            energy_data["battery_discharge"] += value
                            _LOGGER.info("Battery discharge: %.2f kWh", value)
                    charge_id = source.get("stat_energy_to")
                    if charge_id:
                        _LOGGER.info("Found battery charge sensor: %s", charge_id)
                        value = await self._get_statistic_sum(
                            charge_id, start_time, end_time, statistics_during_period
                        )
                        if value is not None:
                            energy_data["battery_charge"] += value
                            _LOGGER.info("Battery charge: %.2f kWh", value)
                
                elif source_type == "grid":
                    # Support both the unified format (stat_energy_from /
                    # stat_energy_to directly on the source, current HA
                    # versions) and the legacy format (flow_from / flow_to
                    # lists) used before the energy prefs migration.
                    import_stats = [
                        flow.get("stat_energy_from")
                        for flow in source.get("flow_from", [])
                    ]
                    if source.get("stat_energy_from"):
                        import_stats.insert(0, source["stat_energy_from"])

                    export_stats = [
                        flow.get("stat_energy_to")
                        for flow in source.get("flow_to", [])
                    ]
                    if source.get("stat_energy_to"):
                        export_stats.insert(0, source["stat_energy_to"])

                    # Grid Import
                    for stat_id in filter(None, import_stats):
                        _LOGGER.info("Found grid import sensor: %s", stat_id)
                        value = await self._get_statistic_sum(
                            stat_id, start_time, end_time, statistics_during_period
                        )
                        if value is not None:
                            energy_data["grid_import"] += value
                            _LOGGER.info("Grid Import: %.2f kWh", value)

                    # Grid Export
                    for stat_id in filter(None, export_stats):
                        _LOGGER.info("Found grid export sensor: %s", stat_id)
                        value = await self._get_statistic_sum(
                            stat_id, start_time, end_time, statistics_during_period
                        )
                        if value is not None:
                            energy_data["grid_export"] += value
                            _LOGGER.info("Grid Export: %.2f kWh", value)
                
            # Consumption = PV + grid import + battery discharge
            #               - grid export - battery charge
            # (same balance the HA energy dashboard uses; without the battery
            # terms the result goes wrong for systems with storage)
            energy_data["consumption"] = (
                energy_data["pv_production"]
                + energy_data["grid_import"]
                + energy_data["battery_discharge"]
                - energy_data["grid_export"]
                - energy_data["battery_charge"]
            )
            _LOGGER.info("Total Consumption: %.2f kWh", energy_data["consumption"])
                
        except ImportError:
            _LOGGER.error("Energy component not available - please configure Energy Dashboard")
        except Exception:
            _LOGGER.exception("Error loading energy dashboard data")
        
        return energy_data

    async def _get_statistic_sum(
        self,
        stat_id: str,
        start_time: datetime,
        end_time: datetime,
        statistics_during_period,
    ) -> float | None:
        """Get the sum of a statistic for a given period."""
        try:
            # Ask for both "change" (per-bucket delta - what the energy
            # dashboard sums) and "sum" (cumulative, fallback anchor).
            stats = await self.hass.async_add_executor_job(
                statistics_during_period,
                self.hass,
                start_time,
                end_time,
                {stat_id},
                "hour",
                None,
                {"sum", "change"},
            )
            
            if stats and stat_id in stats:
                stat_list = stats[stat_id]
                # Preferred: sum the per-bucket "change" values, same as the
                # energy dashboard. Each bucket already carries its own delta,
                # so no boundary anchor or missing-sum pitfalls.
                changes = [
                    row["change"]
                    for row in stat_list
                    if row.get("change") is not None
                ]
                if changes and len(changes) == len(stat_list):
                    total = sum(changes)
                    _LOGGER.debug(
                        "Statistic %s: %d bucket changes -> %.2f kWh",
                        stat_id, len(changes), total,
                    )
                    return total
                # Fallback (e.g. imported stats without stored change):
                # diff of cumulative sums, ignoring buckets without a sum.
                sums = [
                    row["sum"] for row in stat_list if row.get("sum") is not None
                ]
                if len(sums) >= 2:
                    first_sum, last_sum = sums[0], sums[-1]
                    diff = last_sum - first_sum
                    _LOGGER.debug(
                        "Statistic %s: first=%.2f, last=%.2f, diff=%.2f "
                        "(%d buckets)",
                        stat_id, first_sum, last_sum, diff, len(sums)
                    )
                    if diff < -0.001:
                        _LOGGER.warning(
                            "Negative statistic diff for %s (%.2f -> %.2f) - "
                            "the statistic may not be cumulative",
                            stat_id, first_sum, last_sum,
                        )
                    return diff
                _LOGGER.warning(
                    "Not enough statistic rows with sum for %s (%d rows)",
                    stat_id, len(stat_list),
                )
                return None
            
            _LOGGER.warning("No statistics found for %s", stat_id)
            return None
            
        except Exception:
            _LOGGER.exception("Error fetching statistic %s", stat_id)
            return None

    def _get_period_title(self, period: str) -> str:
        """Get the title for the period."""
        titles = {
            "day": "Energie Heute",
            "week": "Energie diese Woche",
            "month": "Energie diesen Monat",
        }
        return titles.get(period, "Energie Statistik")
