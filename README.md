# Energy Post - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Eine Home Assistant Integration zum Erstellen von Instagram-Story-tauglichen Bildern mit Energie-Statistiken aus dem Home Assistant Energy Dashboard.

## ✨ Features

- 📸 **Instagram Story Format**: Generiert Bilder im perfekten Format für Social Media
- 🏠 **3D Hausvisualisierung**: Professionelles Template mit Haus, PV-Modulen, E-Auto, Wärmepumpe
- 📊 **Energy Dashboard Integration**: Nutzt Daten aus dem HA Energy Dashboard
- ⚡ **Umfassende Statistiken**: PV-Ertrag, Netzbezug, Einspeisung, Gesamtverbrauch
- 🔌 **Geräte-Tracking**: Zeigt Verbrauch einzelner Geräte (z.B. Wärmepumpe, Wallbox)
- 🎨 **Professionelles Design**: Hochwertige 3D-Visualisierung mit Werte-Overlays
- 🌐 **Mehrsprachig**: Deutsch & Englisch

## Installation

### HACS (empfohlen)

1. Öffnen Sie HACS in Home Assistant
2. Klicken Sie auf "Integrations"
3. Klicken Sie auf die drei Punkte oben rechts
4. Wählen Sie "Custom repositories"
5. Fügen Sie die URL dieses Repositories hinzu
6. Wählen Sie "Integration" als Kategorie
7. Klicken Sie auf "Add"
8. Suchen Sie nach "Energy Post" und installieren Sie es
9. Starten Sie Home Assistant neu

### Manuelle Installation

1. Kopieren Sie den Ordner `custom_components/energy_post` in Ihr `config/custom_components/` Verzeichnis
2. Starten Sie Home Assistant neu

## Konfiguration

1. Gehen Sie zu "Einstellungen" → "Geräte & Dienste"
2. Klicken Sie auf "+ Integration hinzufügen"
3. Suchen Sie nach "Energy Post"
4. Folgen Sie den Anweisungen zur Konfiguration

### Konfigurationsoptionen

- **Name**: Der Name für Ihre Energy Post Integration (Standard: "Energy Post")
- **Update-Intervall**: Wie oft die Daten aktualisiert werden sollen in Sekunden (Standard: 60)

## 🎯 Nutzung

### Service: `energy_post.generate_image`

Generiert ein Instagram-Story-Bild mit Energie-Statistiken.

#### Parameter

| Parameter | Typ | Erforderlich | Standard | Beschreibung |
|-----------|-----|--------------|----------|--------------|
| `period` | string | Nein | `day` | Zeitraum: `day`, `week`, oder `month` |
| `devices` | list | Nein | `[]` | Liste von Energie-Sensor-Entities |
| `title` | string | Nein | Auto | Benutzerdefinierter Titel |
| `filename` | string | Nein | `energy_stats.png` | Dateiname im `www` Ordner |

#### Beispiel: Service-Aufruf in der UI

1. Gehen Sie zu **Entwicklerwerkzeuge** → **Dienste**
2. Wählen Sie `energy_post.generate_image`
3. Konfigurieren Sie die Parameter:

```yaml
service: energy_post.generate_image
data:
  period: day
  devices:
    - sensor.warmepumpe_energy
    - sensor.wallbox_energy
    - sensor.waschmaschine_energy
  title: "Meine Energie heute"
  filename: energie_heute.png
```

#### Beispiel: Automation

Erstellen Sie täglich um 20 Uhr ein Energie-Bild:

```yaml
automation:
  - alias: "Tägliches Energie-Bild"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: energy_post.generate_image
        data:
          period: day
          devices:
            - sensor.warmepumpe_energy
            - sensor.wallbox_energy
          filename: energie_{{ now().strftime('%Y%m%d') }}.png
```

#### Beispiel: Mit Benachrichtigung

Senden Sie das Bild per Telegram:

```yaml
automation:
  - alias: "Energie-Bild per Telegram"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: energy_post.generate_image
        data:
          period: day
          devices:
            - sensor.warmepumpe_energy
          filename: energie_heute.png
      - delay: "00:00:05"
      - service: notify.telegram
        data:
          message: "Deine Energie-Statistik für heute"
          data:
            photo:
              - url: "http://YOUR_HA_URL:8123/local/energie_heute.png"
                caption: "Energie-Übersicht"
```

### Zugriff auf generierte Bilder

Die Bilder werden im `www` Ordner gespeichert und sind unter folgender URL erreichbar:
```
http://YOUR_HA_URL:8123/local/FILENAME.png
```

## 📊 Datenquellen anpassen

Die Integration sucht standardmäßig nach folgenden Entities:

- **PV-Produktion**: `sensor.solar_production`
- **Netzbezug**: `sensor.grid_import`
- **Einspeisung**: `sensor.grid_export`
- **Gesamtverbrauch**: `sensor.total_consumption`

Um Ihre eigenen Entities zu verwenden, passen Sie die `entity_mapping` in `custom_components/energy_post/image_generator.py` an:

```python
entity_mapping = {
    "pv_production": "sensor.YOUR_SOLAR_SENSOR",
    "grid_import": "sensor.YOUR_GRID_IMPORT_SENSOR",
    "grid_export": "sensor.YOUR_GRID_EXPORT_SENSOR",
    "consumption": "sensor.YOUR_CONSUMPTION_SENSOR",
}
```

## Sensoren

Diese Integration erstellt folgende Sensoren:

- **Power**: Aktuelle Leistung in Watt
- **Energy**: Gesamtenergie in kWh

## Entwicklung

### Voraussetzungen

- Home Assistant 2023.1.0 oder höher
- Python 3.11 oder höher

### Lokale Entwicklung

```bash
# Repository klonen
git clone https://github.com/yourusername/ha-energy-post.git
cd ha-energy-post

# In Home Assistant custom_components Verzeichnis verlinken
ln -s $(pwd)/custom_components/energy_post ~/.homeassistant/custom_components/
```

## Support

Bei Problemen oder Fragen erstellen Sie bitte ein [Issue](https://github.com/yourusername/ha-energy-post/issues).

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei für Details.
