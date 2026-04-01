# Energy Post Integration

## Über diese Integration

Die Energy Post Integration erstellt Instagram-Story-taugliche Bilder mit Energie-Statistiken aus Ihrem Home Assistant Energy Dashboard.

## 🎯 Hauptfunktion

**Energie-Bild generieren** - Erstellt auf Abruf ein professionell gestaltetes Bild (1080x1920) mit:
- PV-Ertrag
- Netzbezug & Einspeisung
- Gesamtverbrauch
- Einzelne Geräte (z.B. Wärmepumpe, Wallbox)
- Zeitreihen-Diagramme
- Moderne, dunkle Optik

## Features

- 📸 **Instagram Story Format**: Perfekte Größe für Social Media (1080x1920)
- 📊 **Energy Dashboard Daten**: Nutzt vorhandene HA Energie-Sensoren
- ⚡ **Umfassende Statistiken**: PV, Netz, Verbrauch, einzelne Geräte
- 🎨 **Modernes Design**: Dunkles Theme mit farbigen Akzenten
- 📈 **Diagramme**: Visualisierung der Energieflüsse über Zeit
- 🔄 **Flexible Zeiträume**: Tag, Woche oder Monat
- 🌐 **Mehrsprachig**: Deutsch & Englisch

## Service: generate_image

### Parameter

- **period**: `day`, `week`, oder `month` (Standard: `day`)
- **devices**: Liste von Energie-Sensor-Entities (optional)
- **title**: Benutzerdefinierter Titel (optional)
- **filename**: Dateiname im `www` Ordner (Standard: `energy_stats.png`)

### Beispiel-Aufruf

```yaml
service: energy_post.generate_image
data:
  period: day
  devices:
    - sensor.warmepumpe_energy
    - sensor.wallbox_energy
  title: "Meine Energie heute"
  filename: energie_heute.png
```

## Verwendung

1. **Manuell**: Rufen Sie den Service über Entwicklerwerkzeuge → Dienste auf
2. **Automation**: Erstellen Sie tägliche/wöchentliche Automationen
3. **Button**: Fügen Sie Buttons in Lovelace hinzu
4. **Script**: Erstellen Sie wiederverwendbare Scripts

## Zugriff auf Bilder

Generierte Bilder werden im `www` Ordner gespeichert:
```
http://YOUR_HA_URL:8123/local/FILENAME.png
```

## Anpassung

### Eigene Energie-Sensoren verwenden

Bearbeiten Sie `custom_components/energy_post/image_generator.py` und passen Sie die `entity_mapping` an:

```python
entity_mapping = {
    "pv_production": "sensor.YOUR_SOLAR_SENSOR",
    "grid_import": "sensor.YOUR_GRID_IMPORT_SENSOR",
    "grid_export": "sensor.YOUR_GRID_EXPORT_SENSOR",
    "consumption": "sensor.YOUR_CONSUMPTION_SENSOR",
}
```

### Design anpassen

Ändern Sie die Farben in `image_generator.py`:

```python
COLOR_PALETTE = {
    "pv_production": "#ffd700",  # Gold für PV
    "grid_import": "#ff6b6b",    # Rot für Netzbezug
    "grid_export": "#4ecdc4",    # Türkis für Einspeisung
    "consumption": "#95e1d3",    # Grün für Verbrauch
}
```

## Beispiele

Weitere Beispiele finden Sie im `examples/` Ordner:
- `automation.yaml` - Verschiedene Automation-Beispiele
- `script.yaml` - Wiederverwendbare Scripts
- `lovelace_card.yaml` - Dashboard-Karten

## Tipps

- Verwenden Sie Automationen für tägliche/wöchentliche Berichte
- Kombinieren Sie mit Telegram/WhatsApp für automatische Benachrichtigungen
- Nutzen Sie verschiedene Dateinamen für historische Archivierung
- Fügen Sie nur relevante Geräte hinzu für übersichtliche Bilder
