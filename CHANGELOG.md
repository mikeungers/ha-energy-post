# Changelog

## [1.4.2] - 2026-04-01

### Fixed
- 🐛 **Robuste Energy Dashboard Integration**: Korrekte Verwendung von `async_get_manager()`
- ✅ **Statistik-Berechnung korrigiert**: Differenz zwischen erstem und letztem Wert wird berechnet
- 🔍 **Ausführliches Logging**: Zeigt alle gefundenen Sensoren und berechnete Werte
- 🛡️ **Besseres Error Handling**: ImportError und Exception werden separat behandelt

### Changed
- 📊 Neue Hilfsmethode `_get_statistic_sum()` für saubere Statistik-Abfragen
- 🔧 Unterstützt mehrere Grid Import/Export Flows (werden addiert)
- 📝 Debug-Logs zeigen Energy Dashboard Preferences komplett

### Technical
- Import: `from homeassistant.components.energy.data import async_get_manager`
- API: `energy_manager = await async_get_manager(hass)` (await hinzugefügt!)
- Statistik: Berechnet Differenz zwischen `first_sum` und `last_sum`
- Logging: `exc_info=True` für vollständige Stacktraces

## [1.4.1] - 2026-04-01

### Fixed
- 🐛 **Energy Manager API korrigiert**: Verwendet jetzt `data.async_get_manager()` statt direkten Zugriff
- ✅ Fehler "'EnergyManager' object has no attribute 'async_get_preferences'" behoben
- 🔧 Korrekte Import-Struktur für Energy Component

### Technical
- Import: `from homeassistant.components.energy import data`
- API: `energy_manager = data.async_get_manager(hass)`

## [1.4.0] - 2026-04-01

### Changed
- 🔌 **Energy Dashboard Integration**: Daten werden jetzt direkt aus dem Energy Dashboard geladen
- ✅ **Keine hardcoded Entity-IDs mehr**: Nutzt automatisch die im Energy Dashboard konfigurierten Sensoren
- 📊 **Automatische Berechnung**: Verbrauch wird aus PV + Netzbezug - Einspeisung berechnet
- 🔍 **Besseres Logging**: Debug-Logs zeigen welche Entities gefunden und verwendet werden

### Fixed
- 🐛 **Werte waren immer 0**: Integration liest jetzt korrekt aus dem Energy Dashboard
- ✅ **Energy Manager Integration**: Nutzt `energy_manager` aus Home Assistant Core

### Technical
- Verwendet `energy_manager.async_get_preferences()` für Energy Dashboard Konfiguration
- Liest `stat_energy_from` und `stat_energy_to` aus Energy Sources
- Nutzt `statistics_during_period()` für historische Daten
- Unterstützt Solar, Grid Import/Export automatisch

### Requirements
- ⚠️ **Energy Dashboard muss konfiguriert sein** in Home Assistant
- Einstellungen → Dashboards → Energie → Konfiguration

## [1.3.1] - 2026-04-01

### Fixed
- 🐛 **Download-Funktion korrigiert**: Image bytes werden jetzt base64-encoded zurückgegeben
- ✅ Service Response Format für Home Assistant kompatibel gemacht
- 🔧 "Invalid JSON in response" Fehler behoben

### Changed
- 📦 Base64-Encoding für Download-Response implementiert

## [1.3.0] - 2026-04-01

### Changed
- 🔥 **Fallback-Modus entfernt**: Nur noch Template-basierte Bildgenerierung
- ✅ **Keine Duplikation mehr**: Alle Grafik-Logik in `template_renderer.py`
- 🎨 **Konsistentes Design**: Immer das professionelle 3D-Template
- 📦 **Kleinere Dependencies**: matplotlib nicht mehr benötigt

### Removed
- ❌ `use_template` Parameter aus `generate_story_image()`
- ❌ `_draw_stat_card()` und alle Icon-Zeichnungs-Methoden
- ❌ `_create_chart()` Methode
- ❌ matplotlib Dependency
- ❌ Alte Fallback-Bildgenerierung (Zeilen 59-430)

### Technical
- Code reduziert von ~530 auf ~90 Zeilen
- Nur noch `_fetch_energy_data()` und `_get_period_title()` in `image_generator.py`
- Alle Rendering-Logik in `template_renderer.py`

## [1.2.1] - 2026-04-01

### Fixed
- 🐛 **Font-Konsistenz**: Fallback-Bildgenerierung nutzt jetzt auch Pillow's embedded font
- ✅ Gleiche Font-Fallback-Logik in `image_generator.py` und `template_renderer.py`
- 🔧 Schriftgröße jetzt konsistent in beiden Modi (Template und Fallback)

## [1.2.0] - 2026-04-01

### Added
- 📥 **Download-Funktionalität**: Bilder können jetzt direkt heruntergeladen werden
- 🔧 Neuer Service-Parameter `download: true` für direkten Download
- 📤 Service Response mit Bilddaten wenn `download=true`
- ✅ Weiterhin Speicherung im www-Ordner wenn `download=false` (Standard)

### Technical
- Service unterstützt jetzt `SupportsResponse.OPTIONAL`
- Response enthält `filename`, `content` und `mime_type` bei Download
- Response enthält `filename`, `path` und `url` bei Speicherung

## [1.1.2] - 2026-04-01

### Fixed
- 🐛 **Font-Problem in Home Assistant behoben**: Nutzt Pillow's embedded default font
- ✅ **Keine externe Font-Installation mehr nötig**: Pillow >= 10.0.0 hat embedded TrueType font
- 📝 Mehrere Font-Pfade werden durchprobiert (System-Fonts als erste Wahl)
- 🔧 Fallback auf Pillow's `ImageFont.truetype(size=X)` funktioniert überall
- ⚡ Text wird jetzt auch in Home Assistant in korrekter Größe angezeigt

### Added
- 🔢 **Intelligente Zahlenformatierung**: Keine Nachkommastelle bei Werten ≥ 100
- 🌍 **Locale-basiertes Dezimaltrennzeichen**: Komma (DE) oder Punkt (EN/US)
- 📏 **Dynamische Bubble-Größe**: Passt sich automatisch an Textlänge an
- 📍 **Linksbündiger Ankerpunkt**: Konsistente Positionierung bei dynamischer Größe

## [1.1.1] - 2026-04-01

### Changed
- 🔧 **Code Refactoring**: Grafik-Logik in separates Modul `template_renderer.py` ausgelagert
- ✅ Keine Duplikation mehr zwischen Test-Script und Produktiv-Code
- 📦 `TemplateRenderer` Klasse ohne Home Assistant Dependencies
- 🧪 Test-Script nutzt jetzt die gleiche Logik wie die Produktiv-Version

### Technical
- Neue Datei: `custom_components/energy_post/template_renderer.py`
- `image_generator.py` nutzt jetzt `TemplateRenderer` für Template-Overlay
- `test_template_overlay.py` vereinfacht auf ~45 Zeilen (vorher ~195 Zeilen)
- Single Source of Truth für alle Positionsanpassungen

## [1.1.0] - 2026-04-01

### Added
- 🏠 **Template-basierte Bildgenerierung**: Professionelle 3D-Hausvisualisierung mit PV-Modulen, E-Auto, Wärmepumpe
- Werte werden als Overlays auf hochwertigem Template platziert
- Automatische Positionierung der Energiewerte an den entsprechenden Komponenten
- Fallback auf generierte Bilder wenn Template nicht verfügbar

### Changed
- Standard-Bildgenerierung nutzt jetzt Template (kann mit `use_template=False` deaktiviert werden)
- Verbesserte visuelle Darstellung für Social Media Posts

## [1.0.2] - 2026-04-01

### Added
- ✨ Visuelle Icons für alle Energie-Kategorien
- ☀️ Solar-Icon mit Sonne und PV-Modulen
- ⚡ Strommast-Icon für Netzbezug
- ↗️ Export-Pfeil für Einspeisung
- 🏠 Haus-Icon für Gesamtverbrauch
- 🔌 Geräte-Icon für einzelne Verbraucher

## [1.0.1] - 2026-04-01

### Fixed
- 🐛 Dependency-Versionen für Kompatibilität mit numpy 2.x aktualisiert
- matplotlib auf >=3.9.0 erhöht
- pillow auf >=10.0.0 erhöht

### Changed
- GitHub URLs auf korrekten Benutzernamen aktualisiert

## [1.0.0] - 2026-04-01

### Added
- 🎉 Initiales Release
- Service `energy_post.generate_image` zur Bildgenerierung
- Instagram Story Format (1080x1920)
- Zeitreihen-Diagramme mit matplotlib
- Statistik-Karten für PV, Netz, Verbrauch
- Geräte-Tracking
- HACS-Kompatibilität
- Mehrsprachige Unterstützung (DE/EN)
- Config Flow für einfache Einrichtung
