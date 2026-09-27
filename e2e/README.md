# E2E-Tests (Home Assistant in Docker + Playwright)

Lokale End-to-End-Tests: ein echtes Home Assistant läuft im Docker-Container,
die `energy_post`-Integration wird über die UI eingerichtet und der
`generate_image`-Service wird UI- und API-seitig verifiziert.

## Voraussetzungen

- Docker Desktop (Compose v2)
- Python 3.11+
- Einmalig: `pip install -r e2e/requirements.txt` und `playwright install chromium`

## Ausführen

```powershell
# aus dem Repo-Root
pip install -r e2e/requirements.txt
playwright install chromium
pytest e2e -v
```

Optionen:

- `--teardown`: Container nach dem Lauf stoppen (`docker compose down`). Ohne
  Flag bleibt der Container laufen → Wiederholungsläufe sind deutlich schneller
  (kein Re-Onboarding).
- `HA_PORT=8124 pytest e2e` für einen anderen Port.
- `HA_IMAGE=ghcr.io/home-assistant/home-assistant:2025.1.0` zum Pinnen der
  HA-Version (Default: `latest`).
- `HEADLESS=0 pytest e2e` für sichtbaren Browser.

## Was getestet wird

| Test | Art | Inhalt |
| ---- | --- | ------ |
| `test_01_onboarding` | Playwright | Onboarding-Flow / Login, Dashboard erreichbar, API-Token gültig |
| `test_02_add_integration` | Playwright | Integration über den UI-Config-Flow hinzufügen |
| `test_03_ui_generate_image` | Playwright | `generate_image` über Dev-Tools → Aktionen aufrufen, Event + `/local/*.png` prüfen |
| `test_04_service_file` | REST + WS | Service-Response, Datei unter `/local/`, `energy_post_image_generated`-Event |
| `test_05_service_download` | REST | `download: true` → base64-PNG in der Response |
| `test_06_devices` | REST | Device-Sensor-State → `devices`-Parameter verändert das Bild |
| `test_07_energy_stats` | WS + REST | `recorder/import_statistics` → Statistiken landen im Bild (Regressionstest für das unified Energy-Prefs-Format) |

## Reset

Der Container-State liegt in `e2e/ha-config/` (DB, onboarding state, generierte
Bilder). Für ein frisches Setup:

```powershell
docker compose -f e2e/docker-compose.yaml down -v
Remove-Item -Recurse -Force e2e\ha-config
git checkout e2e/ha-config
Remove-Item e2e\.auth.json
```

## Troubleshooting

- Bei UI-Timeouts liegen Screenshots in `e2e/test-output/` (automatisch bei
  Fehlschlag).
- HA-Logs: `docker logs ha-energy-post-e2e` oder `GET /api/error_log`.
- `hassfest`-kompatibel: alles unter `e2e/` ist kein Teil der Integration.
