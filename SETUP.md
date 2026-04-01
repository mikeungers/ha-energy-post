# Energy Post - Setup-Anleitung

Diese Anleitung hilft Ihnen, die Energy Post Integration einzurichten und zu konfigurieren.

## 📋 Voraussetzungen

- Home Assistant 2023.1.0 oder höher
- Python 3.11 oder höher
- Energie-Sensoren in Home Assistant konfiguriert

## 🚀 Installation

### Option 1: HACS (empfohlen)

1. Öffnen Sie HACS in Home Assistant
2. Klicken Sie auf **Integrations**
3. Klicken Sie auf die **drei Punkte** oben rechts
4. Wählen Sie **Custom repositories**
5. Fügen Sie die Repository-URL hinzu: `https://github.com/yourusername/ha-energy-post`
6. Wählen Sie **Integration** als Kategorie
7. Klicken Sie auf **Add**
8. Suchen Sie nach "Energy Post"
9. Klicken Sie auf **Download**
10. **Starten Sie Home Assistant neu**

### Option 2: Manuelle Installation

1. Laden Sie die neueste Version herunter
2. Entpacken Sie das Archiv
3. Kopieren Sie den Ordner `custom_components/energy_post` nach `config/custom_components/`
4. Starten Sie Home Assistant neu

## ⚙️ Konfiguration

### Schritt 1: Integration hinzufügen

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
2. Klicken Sie auf **+ Integration hinzufügen**
3. Suchen Sie nach "Energy Post"
4. Geben Sie einen Namen ein (z.B. "Energy Post")
5. Wählen Sie das Update-Intervall (Standard: 60 Sekunden)
6. Klicken Sie auf **Absenden**

### Schritt 2: Energie-Sensoren anpassen

Bearbeiten Sie `custom_components/energy_post/image_generator.py` und passen Sie die Entity-IDs an Ihre Sensoren an:

```python
entity_mapping = {
    "pv_production": "sensor.solar_production",      # Ihre PV-Sensor-ID
    "grid_import": "sensor.grid_import",             # Ihre Netzbezug-Sensor-ID
    "grid_export": "sensor.grid_export",             # Ihre Einspeisung-Sensor-ID
    "consumption": "sensor.total_consumption",       # Ihre Verbrauch-Sensor-ID
}
```

**Wichtig**: Ersetzen Sie die Sensor-IDs mit Ihren tatsächlichen Entity-IDs aus Home Assistant.

### Schritt 3: Testen Sie den Service

1. Gehen Sie zu **Entwicklerwerkzeuge** → **Dienste**
2. Wählen Sie `energy_post.generate_image`
3. Fügen Sie folgende Test-Daten ein:

```yaml
service: energy_post.generate_image
data:
  period: day
  filename: test_image.png
```

4. Klicken Sie auf **Dienst aufrufen**
5. Überprüfen Sie, ob das Bild erstellt wurde: `http://YOUR_HA_URL:8123/local/test_image.png`

## 📊 Ihre Energie-Sensoren finden

### Methode 1: Entwicklerwerkzeuge

1. Gehen Sie zu **Entwicklerwerkzeuge** → **Zustände**
2. Suchen Sie nach Sensoren mit `device_class: energy`
3. Notieren Sie die Entity-IDs

### Methode 2: Energy Dashboard

1. Gehen Sie zu **Energie** Dashboard
2. Klicken Sie auf **Einstellungen** (Zahnrad-Symbol)
3. Sehen Sie sich die konfigurierten Sensoren an
4. Notieren Sie die Entity-IDs

### Typische Sensor-Namen

- **PV-Produktion**: `sensor.solar_*`, `sensor.pv_*`, `sensor.inverter_*`
- **Netzbezug**: `sensor.grid_import*`, `sensor.power_import*`
- **Einspeisung**: `sensor.grid_export*`, `sensor.power_export*`
- **Verbrauch**: `sensor.total_consumption*`, `sensor.home_consumption*`

## 🔧 Erweiterte Konfiguration

### Geräte-Sensoren hinzufügen

Finden Sie die Entity-IDs Ihrer Geräte:

```yaml
service: energy_post.generate_image
data:
  period: day
  devices:
    - sensor.warmepumpe_energy        # Wärmepumpe
    - sensor.wallbox_energy           # E-Auto Wallbox
    - sensor.waschmaschine_energy     # Waschmaschine
    - sensor.trockner_energy          # Trockner
  filename: energie_mit_geraeten.png
```

### Automation erstellen

Erstellen Sie eine Automation für tägliche Berichte:

1. Gehen Sie zu **Einstellungen** → **Automationen & Szenen**
2. Klicken Sie auf **+ Automation erstellen**
3. Wählen Sie **Leere Automation erstellen**
4. Fügen Sie folgendes hinzu:

```yaml
alias: Tägliches Energie-Bild
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

### Lovelace Button hinzufügen

Fügen Sie einen Button zu Ihrem Dashboard hinzu:

1. Bearbeiten Sie Ihr Dashboard
2. Fügen Sie eine neue Karte hinzu
3. Wählen Sie **Button**
4. Konfigurieren Sie:

```yaml
type: button
name: Energie-Bild erstellen
icon: mdi:image-plus
tap_action:
  action: call-service
  service: energy_post.generate_image
  service_data:
    period: day
    filename: energie_heute.png
```

## 🎨 Design anpassen

### Farben ändern

Bearbeiten Sie `custom_components/energy_post/image_generator.py`:

```python
COLOR_PALETTE = {
    "pv_production": "#ffd700",   # Gold
    "grid_import": "#ff6b6b",     # Rot
    "grid_export": "#4ecdc4",     # Türkis
    "consumption": "#95e1d3",     # Grün
    "device": "#a8dadc",          # Hellblau
}
```

### Hintergrundfarbe ändern

```python
BACKGROUND_COLOR = "#1a1a2e"  # Dunkelblau
TEXT_COLOR = "#ffffff"        # Weiß
```

## 🐛 Fehlerbehebung

### Bild wird nicht erstellt

1. Überprüfen Sie die Logs: **Einstellungen** → **System** → **Protokolle**
2. Suchen Sie nach Fehlern mit `energy_post`
3. Stellen Sie sicher, dass der `www` Ordner existiert

### Sensoren zeigen keine Daten

1. Überprüfen Sie, ob die Entity-IDs korrekt sind
2. Stellen Sie sicher, dass die Sensoren Daten haben (nicht `unknown` oder `unavailable`)
3. Überprüfen Sie die `entity_mapping` in `image_generator.py`

### Schriftarten fehlen

Falls Schriftarten nicht geladen werden können, verwendet die Integration automatisch Standard-Schriftarten. Dies ist normal und beeinträchtigt die Funktionalität nicht.

## 📱 Integration mit Benachrichtigungen

### Telegram

```yaml
automation:
  - alias: Energie-Bild per Telegram
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: energy_post.generate_image
        data:
          period: day
          filename: energie_heute.png
      - delay: "00:00:05"
      - service: notify.telegram
        data:
          message: "Deine Energie-Statistik"
          data:
            photo:
              - url: "http://YOUR_HA_URL:8123/local/energie_heute.png"
```

### Mobile App

```yaml
action:
  - service: notify.mobile_app_YOUR_PHONE
    data:
      message: "Energie-Bericht"
      data:
        image: "/local/energie_heute.png"
```

## ✅ Checkliste

- [ ] Integration installiert
- [ ] Home Assistant neu gestartet
- [ ] Integration konfiguriert
- [ ] Entity-IDs angepasst
- [ ] Test-Bild erfolgreich erstellt
- [ ] Automation erstellt (optional)
- [ ] Dashboard-Button hinzugefügt (optional)
- [ ] Benachrichtigungen konfiguriert (optional)

## 🆘 Support

Bei Problemen:

1. Überprüfen Sie die Logs
2. Lesen Sie die [FAQ](README.md)
3. Erstellen Sie ein [Issue auf GitHub](https://github.com/yourusername/ha-energy-post/issues)

## 🎉 Fertig!

Ihre Energy Post Integration ist jetzt einsatzbereit. Viel Spaß beim Teilen Ihrer Energie-Statistiken!
