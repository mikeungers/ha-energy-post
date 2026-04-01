"""Image generator for energy statistics."""
from __future__ import annotations

from datetime import datetime, timedelta
import io
import logging
import os
from typing import Any

from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .template_renderer import TemplateRenderer

_LOGGER = logging.getLogger(__name__)

INSTAGRAM_STORY_SIZE = (1080, 1920)
BACKGROUND_COLOR = "#1a1a2e"
TEXT_COLOR = "#ffffff"
ACCENT_COLOR = "#00d4ff"

COLOR_PALETTE = {
    "pv_production": "#ffd700",
    "grid_import": "#ff6b6b",
    "grid_export": "#4ecdc4",
    "consumption": "#95e1d3",
    "device": "#a8dadc",
}


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
        use_template: bool = True,
    ) -> bytes:
        """Generate an Instagram story image with energy statistics."""
        
        energy_data = await self._fetch_energy_data(period, devices)
        
        if use_template:
            return await self._generate_template_image(energy_data, period, title, devices)
        
        img = Image.new('RGB', INSTAGRAM_STORY_SIZE, BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 80)
            header_font = ImageFont.truetype("arial.ttf", 50)
            value_font = ImageFont.truetype("arial.ttf", 70)
            unit_font = ImageFont.truetype("arial.ttf", 40)
            label_font = ImageFont.truetype("arial.ttf", 35)
        except OSError:
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
            unit_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        
        y_offset = 100
        
        if title is None:
            title = self._get_period_title(period)
        
        bbox = draw.textbbox((0, 0), title, font=title_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((INSTAGRAM_STORY_SIZE[0] - text_width) // 2, y_offset),
            title,
            fill=TEXT_COLOR,
            font=title_font
        )
        
        y_offset += 150
        
        chart_data = energy_data.get("chart_data", {})
        if chart_data:
            chart_img = await self._create_chart(chart_data, period)
            chart_height = 600
            chart_width = 1000
            chart_img_resized = chart_img.resize((chart_width, chart_height))
            img.paste(chart_img_resized, ((INSTAGRAM_STORY_SIZE[0] - chart_width) // 2, y_offset))
            y_offset += chart_height + 80
        
        stats_y = y_offset
        self._draw_stat_card(
            draw, 100, stats_y, 450, 200,
            "PV Ertrag", energy_data.get("pv_production", 0), "kWh",
            COLOR_PALETTE["pv_production"], value_font, label_font, unit_font
        )
        self._draw_stat_card(
            draw, 580, stats_y, 450, 200,
            "Verbrauch", energy_data.get("consumption", 0), "kWh",
            COLOR_PALETTE["consumption"], value_font, label_font, unit_font
        )
        
        stats_y += 230
        self._draw_stat_card(
            draw, 100, stats_y, 450, 200,
            "Netzbezug", energy_data.get("grid_import", 0), "kWh",
            COLOR_PALETTE["grid_import"], value_font, label_font, unit_font
        )
        self._draw_stat_card(
            draw, 580, stats_y, 450, 200,
            "Einspeisung", energy_data.get("grid_export", 0), "kWh",
            COLOR_PALETTE["grid_export"], value_font, label_font, unit_font
        )
        
        if devices and energy_data.get("devices"):
            stats_y += 280
            bbox = draw.textbbox((0, 0), "Geräte", font=header_font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                ((INSTAGRAM_STORY_SIZE[0] - text_width) // 2, stats_y),
                "Geräte",
                fill=TEXT_COLOR,
                font=header_font
            )
            stats_y += 80
            
            for i, (device_name, device_value) in enumerate(energy_data["devices"].items()):
                if i % 2 == 0:
                    x_pos = 100
                else:
                    x_pos = 580
                
                if i > 0 and i % 2 == 0:
                    stats_y += 230
                
                self._draw_stat_card(
                    draw, x_pos, stats_y, 450, 200,
                    device_name, device_value, "kWh",
                    COLOR_PALETTE["device"], value_font, label_font, unit_font
                )
        
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        bbox = draw.textbbox((0, 0), timestamp, font=label_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((INSTAGRAM_STORY_SIZE[0] - text_width) // 2, INSTAGRAM_STORY_SIZE[1] - 100),
            timestamp,
            fill="#888888",
            font=label_font
        )
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', optimize=True)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()

    async def _generate_template_image(
        self,
        energy_data: dict[str, Any],
        period: str,
        title: str | None,
        devices: list[str] | None,
    ) -> bytes:
        """Generate image using template overlay."""
        template_path = os.path.join(os.path.dirname(__file__), "template_post.png")
        
        if not os.path.exists(template_path):
            _LOGGER.warning("Template not found, falling back to generated image")
            return await self.generate_story_image(period, devices, title, use_template=False)
        
        if title is None:
            title = self._get_period_title(period)
        
        # Nutze TemplateRenderer für die Grafik-Logik (keine HA-Dependencies)
        renderer = TemplateRenderer(template_path)
        return renderer.render_energy_data(energy_data, title)

    def _draw_stat_card(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        value: float,
        unit: str,
        color: str,
        value_font: ImageFont.FreeTypeFont,
        label_font: ImageFont.FreeTypeFont,
        unit_font: ImageFont.FreeTypeFont,
    ) -> None:
        """Draw a statistics card."""
        draw.rounded_rectangle(
            [(x, y), (x + width, y + height)],
            radius=20,
            fill="#2a2a3e",
            outline=color,
            width=3
        )
        
        icon_x = x + 30
        icon_y = y + 20
        self._draw_icon_for_label(draw, label, icon_x, icon_y, color)
        
        bbox = draw.textbbox((0, 0), label, font=label_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            (x + (width - text_width) // 2, y + 20),
            label,
            fill="#cccccc",
            font=label_font
        )
        
        value_text = f"{value:.1f}"
        bbox = draw.textbbox((0, 0), value_text, font=value_font)
        value_width = bbox[2] - bbox[0]
        
        bbox_unit = draw.textbbox((0, 0), unit, font=unit_font)
        unit_width = bbox_unit[2] - bbox_unit[0]
        
        total_width = value_width + unit_width + 10
        start_x = x + (width - total_width) // 2
        
        draw.text(
            (start_x, y + 90),
            value_text,
            fill=color,
            font=value_font
        )
        draw.text(
            (start_x + value_width + 10, y + 110),
            unit,
            fill="#aaaaaa",
            font=unit_font
        )

    def _draw_icon_for_label(self, draw: ImageDraw.ImageDraw, label: str, x: int, y: int, color: str) -> None:
        """Draw an icon based on the label."""
        label_lower = label.lower()
        
        if "pv" in label_lower or "solar" in label_lower or "ertrag" in label_lower:
            self._draw_solar_icon(draw, x, y, color)
        elif "netzbezug" in label_lower or "import" in label_lower or "grid" in label_lower and "import" in label_lower:
            self._draw_power_pole_icon(draw, x, y, color)
        elif "einspeisung" in label_lower or "export" in label_lower:
            self._draw_export_icon(draw, x, y, color)
        elif "verbrauch" in label_lower or "consumption" in label_lower:
            self._draw_home_icon(draw, x, y, color)
        else:
            self._draw_device_icon(draw, x, y, color)

    def _draw_solar_icon(self, draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
        """Draw a solar panel icon."""
        import math
        
        sun_radius = 15
        sun_x = x + 25
        sun_y = y + 15
        draw.ellipse(
            [sun_x - sun_radius, sun_y - sun_radius, sun_x + sun_radius, sun_y + sun_radius],
            fill=color
        )
        
        for i in range(8):
            angle = i * (2 * math.pi / 8)
            start_x = sun_x + int(math.cos(angle) * (sun_radius + 3))
            start_y = sun_y + int(math.sin(angle) * (sun_radius + 3))
            end_x = sun_x + int(math.cos(angle) * (sun_radius + 10))
            end_y = sun_y + int(math.sin(angle) * (sun_radius + 10))
            draw.line([start_x, start_y, end_x, end_y], fill=color, width=3)
        
        panel_y = y + 40
        for i in range(3):
            px = x + i * 18
            draw.rectangle([px, panel_y, px + 15, panel_y + 25], fill=color, outline="#1a1a2e", width=2)
            draw.line([px, panel_y + 8, px + 15, panel_y + 8], fill="#1a1a2e", width=1)
            draw.line([px, panel_y + 17, px + 15, panel_y + 17], fill="#1a1a2e", width=1)

    def _draw_power_pole_icon(self, draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
        """Draw a power pole/transmission tower icon."""
        pole_x = x + 25
        draw.rectangle([pole_x - 3, y + 15, pole_x + 3, y + 65], fill=color)
        
        draw.polygon([
            (pole_x - 20, y + 20),
            (pole_x + 20, y + 20),
            (pole_x + 15, y + 35),
            (pole_x - 15, y + 35)
        ], outline=color, width=2)
        
        draw.line([pole_x - 15, y + 30, pole_x + 15, y + 30], fill=color, width=2)
        
        for i in range(3):
            y_pos = y + 25 + i * 8
            draw.line([pole_x - 12, y_pos, pole_x + 12, y_pos], fill=color, width=2)

    def _draw_export_icon(self, draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
        """Draw an export/grid feed icon (arrow up with grid)."""
        center_x = x + 25
        center_y = y + 35
        
        draw.polygon([
            (center_x, center_y - 20),
            (center_x - 12, center_y - 5),
            (center_x - 5, center_y - 5),
            (center_x - 5, center_y + 15),
            (center_x + 5, center_y + 15),
            (center_x + 5, center_y - 5),
            (center_x + 12, center_y - 5)
        ], fill=color)
        
        for i in range(3):
            y_line = y + 55 + i * 5
            draw.line([x + 10, y_line, x + 40, y_line], fill=color, width=2)

    def _draw_home_icon(self, draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
        """Draw a home/house icon."""
        draw.polygon([
            (x + 25, y + 10),
            (x + 45, y + 30),
            (x + 40, y + 30),
            (x + 40, y + 60),
            (x + 10, y + 60),
            (x + 10, y + 30),
            (x + 5, y + 30)
        ], fill=color)
        
        draw.rectangle([x + 18, y + 45, x + 32, y + 60], fill="#1a1a2e")
        
        draw.rectangle([x + 15, y + 35, x + 22, y + 42], fill="#1a1a2e")
        draw.rectangle([x + 28, y + 35, x + 35, y + 42], fill="#1a1a2e")

    def _draw_device_icon(self, draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
        """Draw a generic device/plug icon."""
        draw.rounded_rectangle(
            [x + 10, y + 20, x + 40, y + 55],
            radius=5,
            fill=color
        )
        
        draw.rectangle([x + 15, y + 25, x + 20, y + 35], fill="#1a1a2e")
        draw.rectangle([x + 30, y + 25, x + 35, y + 35], fill="#1a1a2e")
        
        draw.ellipse([x + 20, y + 40, x + 30, y + 50], fill="#1a1a2e")
        
        draw.rectangle([x + 23, y + 55, x + 27, y + 65], fill=color)

    async def _create_chart(self, chart_data: dict[str, Any], period: str) -> Image.Image:
        """Create a matplotlib chart."""
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=BACKGROUND_COLOR)
        ax.set_facecolor(BACKGROUND_COLOR)
        
        timestamps = chart_data.get("timestamps", [])
        
        if chart_data.get("pv_production"):
            ax.plot(timestamps, chart_data["pv_production"], 
                   label="PV Ertrag", color=COLOR_PALETTE["pv_production"], linewidth=2.5)
        
        if chart_data.get("consumption"):
            ax.plot(timestamps, chart_data["consumption"], 
                   label="Verbrauch", color=COLOR_PALETTE["consumption"], linewidth=2.5)
        
        if chart_data.get("grid_import"):
            ax.plot(timestamps, chart_data["grid_import"], 
                   label="Netzbezug", color=COLOR_PALETTE["grid_import"], linewidth=2.5)
        
        if chart_data.get("grid_export"):
            ax.plot(timestamps, chart_data["grid_export"], 
                   label="Einspeisung", color=COLOR_PALETTE["grid_export"], linewidth=2.5)
        
        ax.set_xlabel("Zeit", color=TEXT_COLOR, fontsize=12)
        ax.set_ylabel("Energie (kWh)", color=TEXT_COLOR, fontsize=12)
        ax.tick_params(colors=TEXT_COLOR)
        ax.spines['bottom'].set_color(TEXT_COLOR)
        ax.spines['left'].set_color(TEXT_COLOR)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        if period == "day":
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        
        plt.xticks(rotation=45)
        ax.legend(loc='upper left', facecolor='#2a2a3e', edgecolor=TEXT_COLOR, 
                 labelcolor=TEXT_COLOR, fontsize=10)
        ax.grid(True, alpha=0.2, color=TEXT_COLOR)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor=BACKGROUND_COLOR, edgecolor='none')
        buf.seek(0)
        plt.close(fig)
        
        return Image.open(buf)

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
