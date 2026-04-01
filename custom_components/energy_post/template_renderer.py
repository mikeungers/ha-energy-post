"""Template renderer for energy statistics - no Home Assistant dependencies."""
from __future__ import annotations

from datetime import datetime
import io
import locale
import os
from typing import Any

from PIL import Image, ImageDraw, ImageFont


COLOR_PALETTE = {
    "pv_production": "#ffd700",
    "grid_import": "#ff6b6b",
    "grid_export": "#4ecdc4",
    "consumption": "#95e1d3",
    "device": "#a8dadc",
}


class TemplateRenderer:
    """Render energy data on template image without HA dependencies."""
    
    def __init__(self, template_path: str):
        """Initialize renderer with template path."""
        self.template_path = template_path
    
    def render_energy_data(
        self,
        energy_data: dict[str, Any],
        title: str = "Energie Heute",
    ) -> bytes:
        """
        Render energy data on template and return PNG bytes.
        
        Args:
            energy_data: Dictionary with keys:
                - pv_production: float
                - grid_import: float
                - grid_export: float
                - consumption: float
                - devices: dict[str, float] (optional)
            title: Title text for the image
            
        Returns:
            PNG image as bytes
        """
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        
        template = Image.open(self.template_path)
        
        if template.mode != 'RGBA':
            template = template.convert('RGBA')
        
        overlay = Image.new('RGBA', template.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # SCHRIFTGRÖSSEN - Hier können Sie die Schriftgrößen anpassen
        # value_font: Größe für die Zahlenwerte (z.B. "42.5")
        # unit_font: Größe für die Einheit (z.B. "kWh")
        # label_font: Größe für die Beschriftung (z.B. "PV Ertrag")
        # title_font: Größe für den Titel oben (z.B. "Energie Heute")
        
        # Font-Pfade für verschiedene Betriebssysteme
        font_paths = [
            "arial.ttf",                                    # Windows (im PATH)
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux (Debian/Ubuntu)
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",          # Linux (andere Distros)
            "/System/Library/Fonts/Helvetica.ttc",             # macOS
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux (Liberation)
        ]
        
        # Versuche verschiedene Fonts zu laden
        value_font = None
        for font_path in font_paths:
            try:
                value_font = ImageFont.truetype(font_path, 75)
                unit_font = ImageFont.truetype(font_path, 50)
                label_font = ImageFont.truetype(font_path, 38)
                title_font = ImageFont.truetype(font_path, 90)
                break
            except (OSError, IOError):
                continue
        
        # Fallback auf Default-Font nur wenn nichts gefunden wurde
        if value_font is None:
            # Default-Font ist sehr klein, daher nutzen wir ihn mehrfach übereinander
            # um größere Schrift zu simulieren (nicht ideal, aber besser als nichts)
            value_font = ImageFont.load_default()
            unit_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        width, height = template.size
        
        # TITEL POSITION - Oben zentriert
        # Y-Position: height * 0.018 (1.8% von oben)
        # Ändern Sie 0.018 um den Titel höher/tiefer zu platzieren
        bbox = draw.textbbox((0, 0), title, font=title_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((width - text_width) // 2, int(height * 0.018)),
            title,
            fill="#ffffff",
            font=title_font,
            stroke_width=3,
            stroke_fill="#000000"
        )
        
        # PV ERTRAG POSITION - Oben rechts bei der Sonne
        # X-Position: width * 0.90 (90% von links = 10% von rechts)
        # Y-Position: height * 0.073 (7.3% von oben)
        pv_x = int(width * 0.68)
        pv_y = int(height * 0.08)
        self._draw_value_bubble(
            draw, pv_x, pv_y, energy_data.get("pv_production", 0), "kWh",
            "PV Ertrag", COLOR_PALETTE["pv_production"], value_font, unit_font, label_font
        )
        
        # NETZBEZUG POSITION - Links oben beim Strommast
        # X-Position: width * 0.078 (7.8% von links)
        # Y-Position: height * 0.091 (9.1% von oben)
        grid_x = int(width * 0.01)
        grid_y = int(height * 0.31)
        self._draw_value_bubble(
            draw, grid_x, grid_y, energy_data.get("grid_import", 0), "kWh",
            "Netzbezug", COLOR_PALETTE["grid_import"], value_font, unit_font, label_font
        )
        
        # EINSPEISUNG POSITION - Links mittig beim Strommast (unter Netzbezug)
        # X-Position: width * 0.078 (7.8% von links)
        # Y-Position: height * 0.145 (14.5% von oben)
        export_x = int(width * 0.01)
        export_y = int(height * 0.37)
        self._draw_value_bubble(
            draw, export_x, export_y, energy_data.get("grid_export", 0), "kWh",
            "Einspeisung", COLOR_PALETTE["grid_export"], value_font, unit_font, label_font
        )
        
        # GERÄTE - Falls vorhanden
        devices = energy_data.get("devices", {})
        if devices:
            device_list = list(devices.items())
            
            if len(device_list) > 0:
                # GERÄT 1 POSITION - Rechts bei der Wärmepumpe (erstes Gerät in der Liste)
                # X-Position: width * 0.91 (91% von links = 9% von rechts)
                # Y-Position: height * 0.236 (23.6% von oben)
                hp_x = int(width * 0.7)
                hp_y = int(height * 0.67)
                device_name, device_value = device_list[0]
                self._draw_value_bubble(
                    draw, hp_x, hp_y, device_value, "kWh",
                    device_name, COLOR_PALETTE["device"], value_font, unit_font, label_font
                )
            
            if len(device_list) > 1:
                # GERÄT 2 POSITION - Links unten beim E-Auto/Wallbox (zweites Gerät in der Liste)
                # X-Position: width * 0.091 (9.1% von links)
                # Y-Position: height * 0.273 (27.3% von oben)
                car_x = int(width * 0.4)
                car_y = int(height * 0.78)
                device_name, device_value = device_list[1]
                self._draw_value_bubble(
                    draw, car_x, car_y, device_value, "kWh",
                    device_name, COLOR_PALETTE["device"], value_font, unit_font, label_font
                )
        
        # GESAMTVERBRAUCH POSITION - Unten zentriert
        # X-Position: width // 2 (horizontal zentriert)
        # Y-Position: height * 0.909 (90.9% von oben = 9.1% von unten)
        consumption_x = int(width * 0.32)
        consumption_y = int(height * 0.45)
        self._draw_value_bubble(
            draw, consumption_x, consumption_y, energy_data.get("consumption", 0), "kWh",
            "Gesamtverbrauch", COLOR_PALETTE["consumption"], value_font, unit_font, label_font
        )
        
        # ZEITSTEMPEL POSITION - Ganz unten zentriert
        # Y-Position: height * 0.971 (97.1% von oben = 2.9% von unten)
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        bbox = draw.textbbox((0, 0), timestamp, font=label_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((width - text_width) // 2, int(height * 0.971)),
            timestamp,
            fill="#ffffff",
            font=label_font,
            stroke_width=2,
            stroke_fill="#000000"
        )
        
        # Composite und konvertieren
        result = Image.alpha_composite(template, overlay)
        result_rgb = result.convert('RGB')
        
        # Als PNG bytes zurückgeben
        img_bytes = io.BytesIO()
        result_rgb.save(img_bytes, format='PNG', optimize=True)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    def _draw_value_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        value: float,
        unit: str,
        label: str,
        color: str,
        value_font: ImageFont.FreeTypeFont,
        unit_font: ImageFont.FreeTypeFont,
        label_font: ImageFont.FreeTypeFont,
    ) -> None:
        """Draw a value in a semi-transparent bubble with dynamic sizing."""
        # Zahlenformatierung: keine Nachkommastelle bei Werten >= 100
        # Verwendet das Dezimaltrennzeichen des Systems (Komma in DE, Punkt in EN)
        if value >= 100:
            # Keine Nachkommastelle bei großen Werten
            value_text = locale.format_string("%.0f", value, grouping=False)
        else:
            # Eine Nachkommastelle bei kleineren Werten
            value_text = locale.format_string("%.1f", value, grouping=False)
        
        # Textgrößen messen
        bbox_value = draw.textbbox((0, 0), value_text, font=value_font)
        value_width = bbox_value[2] - bbox_value[0]
        value_height = bbox_value[3] - bbox_value[1]
        
        bbox_unit = draw.textbbox((0, 0), unit, font=unit_font)
        unit_width = bbox_unit[2] - bbox_unit[0]
        unit_height = bbox_unit[3] - bbox_unit[1]
        
        bbox_label = draw.textbbox((0, 0), label, font=label_font)
        label_width = bbox_label[2] - bbox_label[0]
        label_height = bbox_label[3] - bbox_label[1]
        
        # DYNAMISCHE BUBBLE GRÖSSE - passt sich dem Inhalt an
        # Padding: Abstand zwischen Text und Box-Rand
        padding_x = 20  # Horizontales Padding
        padding_y = 15  # Vertikales Padding
        spacing = 8     # Abstand zwischen Wert und Einheit
        
        # Breite: max(Wert+Einheit, Label) + Padding
        value_unit_width = value_width + spacing + unit_width
        bubble_width = max(value_unit_width, label_width) + (padding_x * 2)
        
        # Höhe: Wert + Label + Padding
        bubble_height = value_height + label_height + (padding_y * 3)
        
        # Mindestgröße sicherstellen
        bubble_width = max(bubble_width, 180)
        bubble_height = max(bubble_height, 150)
        
        # ANKERPUNKT: (x, y) ist die OBERE LINKE ECKE der Bubble (linksbündig)
        # Bubble zeichnen - linksbündig ab Position x, y
        draw.rounded_rectangle(
            [x, y, x + bubble_width, y + bubble_height],
            radius=15,
            fill=(26, 26, 46, 220),
            outline=tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)),
            width=3
        )
        
        # Wert und Einheit linksbündig innerhalb der Bubble zeichnen
        value_x = x + padding_x
        value_y = y + padding_y + 10
        
        draw.text((value_x, value_y), value_text, fill=color, font=value_font)
        draw.text((value_x + value_width + spacing, value_y + 10), unit, fill="#aaaaaa", font=unit_font)
        
        # Label linksbündig innerhalb der Bubble zeichnen
        label_x = x + padding_x
        label_y = value_y + value_height + padding_y
        draw.text((label_x, label_y), label, fill="#cccccc", font=label_font)
