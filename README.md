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

| Parameter  | Typ     | Erforderlich | Standard           | Beschreibung                                                                    |
| ---------- | ------- | ------------ | ------------------ | ------------------------------------------------------------------------------- |
| `period`   | string  | Nein         | `day`              | Zeitraum: `day`, `week`, oder `month`                                           |
| `devices`  | list    | Nein         | `[]`               | Liste von Energie-Sensor-Entities (max. 2 werden dargestellt)                   |
| `title`    | string  | Nein         | Auto               | Benutzerdefinierter Titel                                                       |
| `filename` | string  | Nein         | `energy_stats.png` | Dateiname im `www` Ordner                                                       |
| `download` | boolean | Nein         | `false`            | `true`: Bild wird als Service-Response (base64) zurückgegeben statt gespeichert |

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

## 📊 Datenquellen

Die Integration liest PV-Produktion, Netzbezug und Einspeisung **automatisch aus der Energy-Dashboard-Konfiguration** – es ist keine manuelle Entity-Zuordnung nötig.

**Voraussetzungen**:

- **Energy Dashboard konfiguriert**: Einstellungen → Dashboards → Energie (Solar- und Netz-Quellen hinzufügen)
- **Recorder aktiv**: die Statistiken kommen aus der Langzeit-Statistik des Recorders

**Einzelne Geräte** (z.B. Wärmepumpe, Wallbox) werden über den Service-Parameter `devices` übergeben – aktuell werden maximal 2 Geräte im Bild dargestellt.

**Gesamtverbrauch** wird berechnet als: `PV-Ertrag + Netzbezug − Einspeisung`

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
git clone https://github.com/mikeungers/ha-energy-post.git
cd ha-energy-post

# Linux/macOS: In Home Assistant custom_components Verzeichnis verlinken
ln -s $(pwd)/custom_components/energy_post ~/.homeassistant/custom_components/

# Windows: Ordner in das HA-config-Verzeichnis kopieren (Symlinks brauchen Admin-Rechte)
xcopy /E /I custom_components\energy_post <HA-config>\custom_components\energy_post
```

## 🧪 Testen

### Lokaler Bildtest (ohne Home Assistant)

Der Renderer lässt sich ohne laufendes Home Assistant testen – ideal zum Anpassen von Positionen, Schriftgrößen und Farben in `custom_components/energy_post/template_renderer.py`:

```bash
pip install "pillow>=10.0.0"
python test_template_overlay.py
```

Das Skript erzeugt `test_template_result.png` im Projektverzeichnis und nutzt denselben `TemplateRenderer` wie die produktive Integration. Die Testwerte können über `MOCK_ENERGY_DATA` im Skript angepasst werden (Werte < 100 werden mit einer Nachkommastelle formatiert, Werte ≥ 100 ohne).

### Service in Home Assistant testen

1. **Voraussetzung prüfen**: Energy Dashboard konfiguriert (Einstellungen → Dashboards → Energie) und Recorder aktiv – sonst enthält das Bild nur Nullen
2. **Entwicklerwerkzeuge** → **Aktionen** → `energy_post.generate_image` aufrufen
3. Ergebnis prüfen unter `http://<HA>:8123/local/energy_stats.png` – oder `download: true` setzen, um das Bild direkt als Service-Response zu erhalten
4. Das Event `energy_post_image_generated` lässt sich unter **Entwicklerwerkzeuge** → **Ereignisse** beobachten

### End-to-End-Test (Docker + Playwright)

Im Ordner `e2e/` liegt eine komplette E2E-Suite: ein echter Home-Assistant-Container mit vorkonfiguriertem Energy Dashboard (`e2e/ha-config/.storage/energy`) plus pytest/Playwright-Tests für Onboarding, Config Flow und `generate_image` mit echten Recorder-Statistiken.

**Voraussetzungen**: Docker Desktop (Compose v2), Python 3.11+

```powershell
# aus dem Repo-Root
python -m pip install -r e2e/requirements.txt
python -m playwright install chromium   # einmalig

python -m pytest e2e -v                 # startet den HA-Container automatisch
```

> **Hinweis**: Falls `pytest`/`playwright` als Befehle nicht gefunden werden (`Scripts`-Ordner nicht im PATH), immer die `python -m`-Form verwenden.

Der Container startet über ein pytest-Fixture automatisch (`docker compose up -d`); beim ersten Lauf läuft das Onboarding per Playwright durch (Token in `e2e/.auth.json`). Nützliche Optionen:

- `python -m pytest e2e --teardown`: Container nach dem Lauf stoppen (ohne Flag bleibt er an → schnellere Wiederholung)
- `$env:HA_PORT=8124; python -m pytest e2e`: anderer Port
- `$env:HA_IMAGE="ghcr.io/home-assistant/home-assistant:2025.1.0"; python -m pytest e2e`: HA-Version pinnen
- `$env:HEADLESS=0; python -m pytest e2e`: Browser sichtbar

Getestet wird u.a.: UI-Onboarding & Config Flow, Service-Aufruf (UI/REST/`download`), `devices`-Parameter, und `recorder/import_statistics` → Werte im Bild (Regressionstest für die Energy-Prefs-Formate).

**Ergebnisse**: Generierte Bilder landen nach jedem Lauf in `test-results/` (gitignored) – zum manuellen Prüfen des Renderings. Fehlschlag-Screenshots liegen in `e2e/test-output/`.

**Reset**: `docker compose -f e2e/docker-compose.yaml down -v`, dann `e2e/ha-config` leeren (`configuration.yaml`, `.storage/energy`, `www/.gitkeep` behalten) und `e2e/.auth.json` löschen.

Details: [e2e/README.md](e2e/README.md)

### Fehlersuche

- **Logs**: Einstellungen → System → Protokolle → nach `energy_post` filtern. Die Integration loggt gefundene Sensoren und berechnete Werte. Ausführlichere Logs über `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.energy_post: debug
```

- **Alle Werte 0,0?** Prüfen Sie: Energy Dashboard konfiguriert? Recorder läuft? Haben die Sensoren Statistiken (Entwicklerwerkzeuge → Statistiken)?

### CI-Validierung

Bei jedem Push und Pull Request laufen [hassfest](https://github.com/home-assistant/actions) und die [HACS-Action](https://github.com/hacs/action) (`.github/workflows/validate.yml`).

## Support

Bei Problemen oder Fragen erstellen Sie bitte ein [Issue](https://github.com/mikeungers/ha-energy-post/issues).

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei für Details.
