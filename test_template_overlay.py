"""Test script for template-based image generation - uses TemplateRenderer."""
import sys
import os
from importlib import util

# Direkter Import von template_renderer.py ohne HomeAssistant Dependencies
spec = util.spec_from_file_location(
    "template_renderer",
    os.path.join(os.path.dirname(__file__), "custom_components", "energy_post", "template_renderer.py")
)
template_renderer = util.module_from_spec(spec)
sys.modules['template_renderer'] = template_renderer
spec.loader.exec_module(template_renderer)

TemplateRenderer = template_renderer.TemplateRenderer


# Mock-Daten für den Test
# Verschiedene Wertebereiche zum Testen der Formatierung:
# - Werte < 100: mit einer Nachkommastelle (z.B. 42.5)
# - Werte >= 100: ohne Nachkommastelle (z.B. 125)
MOCK_ENERGY_DATA = {
    "pv_production": 42.5,      # < 100: zeigt 42,5 (oder 42.5 je nach Locale)
    "grid_import": 8.7,         # < 100: zeigt 8,7
    "grid_export": 13.0,        # < 100: zeigt 13,0
    "consumption": 138.2,       # >= 100: zeigt 138 (ohne Nachkommastelle)
    "devices": {
        "Wärmepumpe": 115.3,    # >= 100: zeigt 115
        "E-Auto": 12.8,         # < 100: zeigt 12,8
    }
}


def generate_test_image():
    """Generate test image using TemplateRenderer with mock data."""
    template_path = os.path.join("custom_components", "energy_post", "template_post.png")
    
    # Nutze TemplateRenderer - die gleiche Logik wie in der Produktiv-Version!
    renderer = TemplateRenderer(template_path)
    
    # Bild generieren
    image_bytes = renderer.render_energy_data(
        energy_data=MOCK_ENERGY_DATA,
        title="Energie Heute"
    )
    
    # Bild speichern
    output_path = "test_template_result.png"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    
    print(f"Template overlay generated: {output_path}")
    print(f"Using TemplateRenderer from template_renderer.py")
    print(f"\nPositionsanpassungen in custom_components/energy_post/template_renderer.py vornehmen!")
    return output_path


if __name__ == "__main__":
    generate_test_image()
