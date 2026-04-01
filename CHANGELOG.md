# Changelog

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
