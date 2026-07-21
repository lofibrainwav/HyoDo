"""Regression tests for the local dashboard HTTP server contract.

PR #75 verified these behaviours only through a manual smoke test; this file
seals the headers, routes, CSP hash, and HEAD support against regressions.
"""

from __future__ import annotations

import base64
import hashlib
import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Event, Thread
from time import sleep

import pytest

from hyodo.cli.main import DASHBOARD_CSP, DashboardState, make_dashboard_handler
from hyodo.dashboard import POLL_SCRIPT, POLL_SCRIPT_SHA256, render_dashboard_html

EVIDENCE: dict[str, object] = {
    "schema_version": "hyodo.dashboard-evidence/v1",
    "target": "/tmp/HyoDo",
    "measured_at": "2026-07-20T00:00:00+00:00",
    "gates": {
        "typecheck": {"status": "PASS", "message": "0 errors"},
        "lint_format": {"status": "PASS", "message": "passed"},
        "tests": {"status": "PASS", "message": "175 passed in 1.50s"},
        "sbom": {"status": "PASS", "message": "generated"},
    },
    "safety": {"risk_score": 5, "findings": []},
}


@pytest.fixture
def dashboard_server():
    state = DashboardState(dict(EVIDENCE))
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_dashboard_handler(state))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state, server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def server_port(dashboard_server):
    _state, port = dashboard_server
    return port


def _request(port: int, method: str, path: str) -> tuple[int, dict[str, str], bytes]:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(method, path)
        response = conn.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        conn.close()


def _post(port: int, path: str, body: str) -> tuple[int, dict[str, str], bytes]:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(
            "POST",
            path,
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = conn.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        conn.close()


def test_root_serves_html_with_security_headers(server_port):
    status, headers, body = _request(server_port, "GET", "/")
    assert status == 200
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Content-Security-Policy"] == DASHBOARD_CSP
    assert "connect-src 'self'" in headers["Content-Security-Policy"]
    assert b"HyoDo Instrument Panel" in body


def test_api_evidence_round_trips_json(server_port):
    status, headers, body = _request(server_port, "GET", "/api/evidence")
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    payload = json.loads(body)
    assert payload["measured_at"] == EVIDENCE["measured_at"]
    assert payload["gates"]["typecheck"]["status"] == "PASS"


def test_unknown_route_is_404(server_port):
    status, _headers, _body = _request(server_port, "GET", "/nope")
    assert status == 404


def test_head_returns_headers_without_body(server_port):
    get_status, get_headers, get_body = _request(server_port, "GET", "/")
    status, headers, body = _request(server_port, "HEAD", "/")
    assert (get_status, status) == (200, 200)
    assert body == b""
    assert headers["Content-Length"] == get_headers["Content-Length"] == str(len(get_body))


def test_state_update_swaps_served_snapshot(dashboard_server):
    # The refresh loop calls DashboardState.update; the handler must serve the
    # newer measurement so the page poller can detect it and reload.
    state, port = dashboard_server
    _status, _headers, before = _request(port, "GET", "/api/evidence")
    assert json.loads(before)["measured_at"] == EVIDENCE["measured_at"]
    newer = dict(EVIDENCE)
    newer["measured_at"] = "2026-07-20T01:00:00+00:00"
    state.update(newer)
    _status, _headers, after = _request(port, "GET", "/api/evidence")
    assert json.loads(after)["measured_at"] == "2026-07-20T01:00:00+00:00"


def test_manual_refresh_requires_token_and_redirects_after_replacing_snapshot():
    state = DashboardState(dict(EVIDENCE), refresh_token="issued-token", interval=30)
    refreshed = dict(EVIDENCE)
    refreshed["measured_at"] = "2026-07-20T01:00:00+00:00"
    started = Event()
    release = Event()

    def refresh():
        started.set()
        assert release.wait(timeout=2)
        return refreshed

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_dashboard_handler(state, refresh, "issued-token"),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        status, _headers, _body = _post(port, "/api/refresh", "token=wrong")
        assert status == 403
        status, headers, _body = _post(port, "/api/refresh", "token=issued-token")
        assert status == 303
        assert headers["Location"] == "/"
        assert started.wait(timeout=1)
        status, _headers, body = _request(port, "GET", "/api/status")
        assert status == 200
        assert json.loads(body) == {
            "refreshing": True,
            "message": "Measurement running. This page will update when it finishes.",
        }
        release.set()
        for _ in range(20):
            status, _headers, body = _request(port, "GET", "/api/evidence")
            if json.loads(body)["measured_at"] == refreshed["measured_at"]:
                break
            sleep(0.01)
        status, _headers, body = _request(port, "GET", "/api/evidence")
        assert status == 200
        assert json.loads(body)["measured_at"] == refreshed["measured_at"]
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_manual_refresh_failure_keeps_snapshot_and_exposes_failure_status():
    state = DashboardState(dict(EVIDENCE))

    def broken_refresh():
        raise RuntimeError("collector unavailable")

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), make_dashboard_handler(state, broken_refresh, "issued-token")
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, _headers, _body = _post(
            server.server_address[1], "/api/refresh", "token=issued-token"
        )
        assert status == 303
        for _ in range(20):
            status, _headers, body = _request(server.server_address[1], "GET", "/api/status")
            if not json.loads(body)["refreshing"]:
                break
            sleep(0.01)
        assert status == 200
        assert json.loads(body) == {
            "refreshing": False,
            "message": "Measurement failed; the last successful snapshot is still shown.",
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_csp_hash_matches_inline_poll_script():
    digest = base64.b64encode(hashlib.sha256(POLL_SCRIPT.encode("utf-8")).digest()).decode("ascii")
    assert digest == POLL_SCRIPT_SHA256
    assert f"'sha256-{POLL_SCRIPT_SHA256}'" in DASHBOARD_CSP
    html = render_dashboard_html(dict(EVIDENCE))
    assert POLL_SCRIPT in html
    assert 'data-measured="2026-07-20T00:00:00+00:00"' in html


def test_dashboard_declares_light_and_dark_schemes():
    html = render_dashboard_html(dict(EVIDENCE))
    assert "color-scheme: light dark" in html
    assert "@media (prefers-color-scheme: dark)" in html


def test_dashboard_exposes_local_measurement_controls_when_token_is_issued():
    html = render_dashboard_html(dict(EVIDENCE), refresh_token="issued-token", interval=30)
    assert 'href="/api/evidence"' in html
    assert 'action="/api/refresh"' in html
    assert 'name="token" value="issued-token"' in html
    assert "Measure again now" in html
    assert "Auto re-measure every 30s" in html


def test_dashboard_exposes_live_measurement_status_and_disables_running_button():
    html = render_dashboard_html(
        dict(EVIDENCE),
        refresh_token="issued-token",
        refreshing=True,
        refresh_message="Measurement running.",
    )
    assert 'id="measurement-status"' in html
    assert 'aria-live="polite"' in html
    assert "Measurement running." in html
    assert '<button type="submit" disabled>Measurement running</button>' in html


def test_card_headings_are_trilingual_hanja_korean_english():
    html = render_dashboard_html(dict(EVIDENCE))
    for heading in (
        "眞 진</span> Truth",
        "善 선</span> Goodness",
        "美 미</span> Beauty",
        "仁 인</span> Benevolence",
        "孝 효</span> Filial Piety",
        "永 영</span> Eternity",
    ):
        assert heading in html
