"""Pytest fixtures for the energy_post e2e tests (HA in Docker + Playwright)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest
import requests
import websocket
from playwright.sync_api import Page, sync_playwright

E2E_DIR = Path(__file__).parent
CONFIG_DIR = E2E_DIR / "ha-config"
AUTH_FILE = E2E_DIR / ".auth.json"
OUTPUT_DIR = E2E_DIR / "test-output"
COMPOSE_FILE = E2E_DIR / "docker-compose.yaml"

HA_PORT = os.environ.get("HA_PORT", "8123")
HA_URL = f"http://localhost:{HA_PORT}"
WS_URL = f"ws://localhost:{HA_PORT}/api/websocket"
TEMPLATE_PATH = E2E_DIR.parent / "custom_components" / "energy_post" / "template_post.png"

# Credentials used for the onboarding account. They only live in the
# throwaway container config, never anywhere else. Keep them in sync with
# e2e/test_energy_post.py which onboards via the REST API.
E2E_NAME = "e2e"
E2E_USER = "e2e"
E2E_PASS = "e2e-test-password"

HEADLESS = os.environ.get("HEADLESS", "1") != "0"
BOOT_TIMEOUT = 300  # first HA boot in the container can take a while

# Onboarding step buttons in click-priority order (German + English labels).
_STEP_BUTTONS = [
    re.compile(r"mein smarthome erstellen|create my smart ?home", re.I),
    re.compile(r"create account|konto erstellen|erstellen", re.I),
    re.compile(r"detect|erkennen", re.I),
    re.compile(r"next|weiter", re.I),
    re.compile(r"finish|fertig|abschlie", re.I),
    re.compile(r"log ?in|anmelden", re.I),
]


def _compose(*args: str) -> None:
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],
        check=True,
        cwd=E2E_DIR,
    )


def _wait_for_ha(timeout: int = BOOT_TIMEOUT) -> None:
    """Poll the HA frontend until it serves requests."""
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            r = requests.get(f"{HA_URL}/manifest.json", timeout=5)
            if r.status_code == 200:
                return
        except requests.RequestException as err:  # noqa: PERF203
            last_err = err
        time.sleep(2)
    raise TimeoutError(
        f"Home Assistant did not come up within {timeout}s (last error: {last_err})"
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--teardown",
        action="store_true",
        help="stop the Home Assistant container after the test run",
    )


@pytest.fixture(scope="session")
def ha_url(request: pytest.FixtureRequest) -> str:
    """Start the HA container and wait until it is reachable."""
    _compose("up", "-d")
    _wait_for_ha()

    def _maybe_teardown() -> None:
        # Persist file-based results (download=false writes to /config/www,
        # which is bind-mounted to e2e/ha-config/www) into test-results/.
        results_dir = E2E_DIR.parent / "test-results"
        www = CONFIG_DIR / "www"
        if www.is_dir():
            results_dir.mkdir(exist_ok=True)
            for png in www.glob("*.png"):
                (results_dir / png.name).write_bytes(png.read_bytes())
        if request.config.getoption("--teardown"):
            _compose("down")

    request.addfinalizer(_maybe_teardown)
    return HA_URL


def _fill_if_visible(page: Page, selector: str, value: str) -> None:
    loc = page.locator(selector)
    if loc.count() and loc.first.is_visible():
        loc.first.fill(value)


def _extract_hass_tokens(page: Page) -> dict[str, Any]:
    tokens = page.evaluate("() => localStorage.getItem('hassTokens')")
    if not tokens:
        raise RuntimeError("localStorage.hassTokens missing after login/onboarding")
    return json.loads(tokens)


def _login(page: Page) -> None:
    """Log in on an already-onboarded instance."""
    page.goto(HA_URL)
    page.wait_for_selector("input[name='username']", timeout=60_000)
    page.fill("input[name='username']", E2E_USER)
    page.fill("input[name='password']", E2E_PASS)
    page.get_by_role("button", name=re.compile(r"log ?in|next", re.I)).first.click()
    page.wait_for_function(
        "() => localStorage.getItem('hassTokens') !== null", timeout=60_000
    )


def _onboard(page: Page) -> None:
    """Walk through the HA onboarding flow (fresh install).

    The step order/shape varies across HA versions, so this loops until the
    app hands out tokens: fill any visible credential inputs, then click the
    first matching step button (welcome -> account -> location -> units ->
    analytics -> finish). A login form is handled the same way.
    """
    page.goto(HA_URL)
    deadline = time.monotonic() + 240  # frontend bundle load can be slow
    idle = 0

    while time.monotonic() < deadline:
        has_tokens = page.evaluate(
            "() => localStorage.getItem('hassTokens') !== null"
        )
        # Done once the app navigated away from onboarding with valid tokens.
        if has_tokens and "/onboarding" not in page.url:
            return
        # If tokens already exist but no further button matches, remaining
        # steps are completed via the API afterwards (see _obtain_auth).
        if has_tokens and idle >= 3:
            return

        _fill_if_visible(page, "input[name='name']", E2E_NAME)
        _fill_if_visible(page, "input[name='username']", E2E_USER)
        _fill_if_visible(page, "input[name='password']", E2E_PASS)
        _fill_if_visible(page, "input[name='password_confirm']", E2E_PASS)

        clicked = False
        for pattern in _STEP_BUTTONS:
            btn = page.get_by_role("button", name=pattern)
            if btn.count() and btn.first.is_visible():
                btn.first.click()
                clicked = True
                break
        idle = 0 if clicked else idle + 1
        page.wait_for_timeout(1500)

    raise RuntimeError(
        "Onboarding flow did not finish - check screenshots in "
        f"{OUTPUT_DIR} and the selectors in _onboard()"
    )


def _request_llat(token: str) -> str:
    """Exchange the short-lived onboarding token for a long-lived token."""
    ws = websocket.create_connection(WS_URL, timeout=30)
    try:
        ws.recv()  # auth_required
        ws.send(json.dumps({"type": "auth", "access_token": token}))
        reply = json.loads(ws.recv())
        if reply.get("type") != "auth_ok":
            raise RuntimeError(f"WS auth failed: {reply}")
        ws.send(
            json.dumps(
                {
                    "id": 1,
                    "type": "auth/long_lived_access_token",
                    "client_name": "playwright-e2e",
                    "lifespan": 3650,
                }
            )
        )
        reply = json.loads(ws.recv())
        if not reply.get("success"):
            raise RuntimeError(f"long_lived_access_token failed: {reply}")
        return reply["result"]
    finally:
        ws.close()


def _complete_onboarding_steps(token: str) -> None:
    """Finish any remaining onboarding steps via the REST API (idempotent)."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{HA_URL}/api/onboarding", timeout=10)
    except requests.RequestException:
        return
    if r.status_code != 200:
        return
    steps = r.json()
    if isinstance(steps, dict):
        steps = steps.get("steps", [])
    for step in steps:
        name = step.get("step") if isinstance(step, dict) else step
        done = step.get("done") if isinstance(step, dict) else False
        if done or name == "user":
            continue
        requests.post(
            f"{HA_URL}/api/onboarding/{name}",
            headers=headers,
            json={},
            timeout=10,
        )


def _obtain_auth() -> dict[str, Any]:
    """Run onboarding (or login) once and persist tokens in .auth.json."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            locale="en-US",
            viewport={"width": 1280, "height": 900},
        )
        context.grant_permissions(["geolocation"])
        context.set_geolocation({"latitude": 52.52, "longitude": 13.405})
        page = context.new_page()
        try:
            try:
                _onboard(page)
            except RuntimeError:
                # Already onboarded previously? Fall back to normal login.
                _login(page)
            hass_tokens = _extract_hass_tokens(page)
        finally:
            browser.close()

    # Make sure remaining onboarding steps are completed via the API - the UI
    # loop can stop early once hassTokens exist (they are set right after the
    # account step, before location/analytics steps finish).
    _complete_onboarding_steps(hass_tokens["access_token"])

    data = {
        "hassTokens": hass_tokens,
        "llat": _request_llat(hass_tokens["access_token"]),
    }
    AUTH_FILE.write_text(json.dumps(data))
    # Also feed the pre-existing REST-based test (e2e/test_energy_post.py)
    # which reads its token from .e2e-token.
    (E2E_DIR / ".e2e-token").write_text(data["llat"])
    return data


@pytest.fixture(scope="session")
def auth(ha_url: str) -> dict[str, Any]:
    """Return auth info; run the UI onboarding once if needed."""
    if AUTH_FILE.exists():
        data = json.loads(AUTH_FILE.read_text())
        r = requests.get(
            f"{HA_URL}/api/",
            headers={"Authorization": f"Bearer {data['llat']}"},
            timeout=10,
        )
        if r.status_code == 200:
            _complete_onboarding_steps(data["llat"])
            return data
    return _obtain_auth()


@pytest.fixture(scope="session")
def api(auth: dict[str, Any]) -> requests.Session:
    """Requests session authenticated with the long-lived token."""
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {auth['llat']}"})
    return s


class HAWebsocket:
    """Minimal websocket API client."""

    def __init__(self, url: str, token: str) -> None:
        self._ws = websocket.create_connection(url, timeout=30)
        self._id = 0
        self._ws.recv()  # auth_required
        self._ws.send(json.dumps({"type": "auth", "access_token": token}))
        reply = json.loads(self._ws.recv())
        if reply.get("type") != "auth_ok":
            raise RuntimeError(f"WS auth failed: {reply}")

    def cmd(self, type_: str, timeout: float = 30, **payload: Any) -> Any:
        self._id += 1
        self._ws.send(json.dumps({"id": self._id, "type": type_, **payload}))
        self._ws.settimeout(timeout)
        while True:
            msg = json.loads(self._ws.recv())
            if msg.get("id") != self._id:
                continue
            if not msg.get("success"):
                raise RuntimeError(f"WS command {type_} failed: {msg.get('error')}")
            return msg.get("result")

    def recv_event(self, timeout: float = 30) -> dict[str, Any]:
        """Receive the next event message (after subscribe_events)."""
        self._ws.settimeout(timeout)
        while True:
            msg = json.loads(self._ws.recv())
            if msg.get("type") == "event":
                return msg["event"]

    def close(self) -> None:
        self._ws.close()


@pytest.fixture()
def ws(auth: dict[str, Any]):
    client = HAWebsocket(WS_URL, auth["llat"])
    yield client
    client.close()


@pytest.fixture()
def ensure_integration(api: requests.Session) -> None:
    """Create the energy_post config entry via REST if not present yet.

    UI-based creation is covered by test_02; this fixture only guarantees the
    entry exists so the service tests can run standalone.
    """
    entries = api.get(f"{HA_URL}/api/config/config_entries/entry", timeout=10)
    entries.raise_for_status()
    if any(e["domain"] == "energy_post" for e in entries.json()):
        return

    r = api.post(
        f"{HA_URL}/api/config/config_entries/flow",
        json={"handler": "energy_post", "show_errors": True},
        timeout=30,
    )
    r.raise_for_status()
    flow = r.json()
    if flow.get("type") == "form":
        r = api.post(
            f"{HA_URL}/api/config/config_entries/flow/{flow['flow_id']}",
            json={"name": "Energy Post", "update_interval": 60},
            timeout=30,
        )
        r.raise_for_status()

    entries = api.get(f"{HA_URL}/api/config/config_entries/entry", timeout=10)
    assert any(
        e["domain"] == "energy_post" for e in entries.json()
    ), "energy_post config entry was not created"


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    rep = yield
    setattr(item, f"rep_{rep.when}", rep)
    return rep


@pytest.fixture()
def page(request: pytest.FixtureRequest, auth: dict[str, Any]):
    """Playwright page logged in via injected hassTokens."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            locale="en-US", viewport={"width": 1280, "height": 900}
        )
        context.add_init_script(
            "localStorage.setItem('hassTokens', "
            f"{json.dumps(json.dumps(auth['hassTokens']))})"
        )
        page = context.new_page()
        yield page
        rep = getattr(request.node, "rep_call", None)
        if rep is not None and rep.failed:
            page.screenshot(
                path=str(OUTPUT_DIR / f"{request.node.name}.png"),
                full_page=True,
            )
        browser.close()
