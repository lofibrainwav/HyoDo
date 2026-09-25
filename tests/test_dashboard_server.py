"""Regression tests for the local dashboard HTTP server contract.

PR #75 verified these behaviours only through a manual smoke test; this file
seals the headers, routes, CSP hash, and HEAD support against regressions.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from socket import socket
from threading import Event, Thread
from time import sleep

import pytest

from hyodo.cli.main import DASHBOARD_CSP, DashboardState, app, make_dashboard_handler
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
    "safety": {"risk_score": 5, "source": "git diff HEAD", "findings": []},
}


@pytest.fixture
def dashboard_server():
    state = DashboardState(dict(EVIDENCE))
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_dashboard_handler(state))
    # serve_forever() checks for shutdown every poll_interval (default 0.5s), so
    # shutdown() on exit blocked each test for up to half a second. Requests are
    # still served on socket readiness; only the shutdown check gets faster.
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
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


def _request_with_origin(
    port: int, path: str, origin: str | None
) -> tuple[int, dict[str, str], bytes]:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        headers = {"Origin": origin} if origin is not None else {}
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        conn.close()


@contextmanager
def _running_server(allow_origins: tuple[str, ...] = ()):
    """Start a throwaway dashboard server with a given CORS allow-list."""
    state = DashboardState(dict(EVIDENCE))
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), make_dashboard_handler(state, allow_origins=allow_origins)
    )
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


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


def test_dashboard_listener_serves_unobserved_status_while_initial_collection_is_blocked(
    tmp_path, monkeypatch
):
    """Startup status is reachable before the first real evidence snapshot exists."""
    from http.server import ThreadingHTTPServer as RealServer

    from typer.testing import CliRunner

    import hyodo.cli.main as cli_main

    (tmp_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
    (tmp_path / "hyodo").mkdir()
    with socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    entered = Event()
    release = Event()
    server_holder = []

    def blocked_collection(_root):
        entered.set()
        assert release.wait(timeout=5)
        measured = dict(EVIDENCE)
        measured["schema_version"] = "hyodo.dashboard-evidence/v2"
        return measured

    def capture_server(*args, **kwargs):
        server = RealServer(*args, **kwargs)
        server_holder.append(server)
        return server

    monkeypatch.setattr(cli_main, "collect_dashboard_evidence", blocked_collection)
    monkeypatch.setattr(cli_main, "write_runtime_identity", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli_main, "ThreadingHTTPServer", capture_server)
    result_holder = []
    runner = CliRunner()
    command = Thread(
        target=lambda: result_holder.append(
            runner.invoke(app, ["dashboard", str(tmp_path), "--port", str(port)])
        ),
        daemon=True,
    )
    command.start()
    try:
        assert entered.wait(timeout=5)
        import time

        deadline = time.monotonic() + 5
        while True:
            try:
                status_code, _, status_body = _request(port, "GET", "/api/status")
                break
            except OSError:
                assert time.monotonic() < deadline, "listener did not bind"
                sleep(0.01)
        assert status_code == 200
        assert json.loads(status_body)["readiness"] == "starting"
        evidence_status, _, evidence_body = _request(port, "GET", "/api/evidence")
        assert evidence_status == 200
        initial = json.loads(evidence_body)
        assert "startup_status" not in initial
        assert initial["measured_at"] is None
        assert all(gate["status"] == "UNOBSERVED" for gate in initial["gates"].values())
        assert initial["safety"]["risk_score_state"] == "not_executed"
        release.set()
        deadline = time.monotonic() + 5
        while True:
            _, _, status_body = _request(port, "GET", "/api/status")
            if json.loads(status_body)["readiness"] == "ready":
                break
            assert time.monotonic() < deadline, "real evidence was not installed"
            sleep(0.01)
        _, _, evidence_body = _request(port, "GET", "/api/evidence")
        observed = json.loads(evidence_body)
        assert "startup_status" not in observed
        assert observed["schema_version"] == "hyodo.dashboard-evidence/v2"
        assert observed["measured_at"] == EVIDENCE["measured_at"]
        assert observed["gates"]["tests"]["status"] == "PASS"
    finally:
        release.set()
        if server_holder:
            server_holder[0].shutdown()
        command.join(timeout=5)
    assert result_holder
    assert result_holder[0].exit_code == 0


def test_dashboard_remains_reachable_with_unobserved_evidence_when_initial_collection_raises(
    tmp_path, monkeypatch
):
    """A failed initial measurement keeps the listener up without inventing evidence."""
    from http.server import ThreadingHTTPServer as RealServer

    from typer.testing import CliRunner

    import hyodo.cli.main as cli_main

    (tmp_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
    (tmp_path / "hyodo").mkdir()
    with socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    server_holder = []

    def failed_collection(_root):
        raise RuntimeError("initial measurement failed")

    def capture_server(*args, **kwargs):
        server = RealServer(*args, **kwargs)
        server_holder.append(server)
        return server

    monkeypatch.setattr(cli_main, "collect_dashboard_evidence", failed_collection)
    monkeypatch.setattr(cli_main, "write_runtime_identity", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli_main, "ThreadingHTTPServer", capture_server)
    result_holder = []
    runner = CliRunner()
    command = Thread(
        target=lambda: result_holder.append(
            runner.invoke(app, ["dashboard", str(tmp_path), "--port", str(port)])
        ),
        daemon=True,
    )
    command.start()
    try:
        import time

        deadline = time.monotonic() + 5
        while True:
            try:
                status_code, _, status_body = _request(port, "GET", "/api/status")
                status_payload = json.loads(status_body)
                if status_code == 200 and status_payload["readiness"] == "failed":
                    break
            except OSError:
                pass
            assert time.monotonic() < deadline, "failed startup status was not reachable"
            sleep(0.01)

        evidence_status, _, evidence_body = _request(port, "GET", "/api/evidence")
        assert evidence_status == 200
        evidence = json.loads(evidence_body)
        assert "startup_status" not in evidence
        assert evidence["schema_version"] == "hyodo.dashboard-evidence/v2"
        assert evidence["measured_at"] is None
        assert all(gate["status"] == "UNOBSERVED" for gate in evidence["gates"].values())
        assert evidence["safety"]["risk_score_state"] == "not_executed"
    finally:
        if server_holder:
            server_holder[0].shutdown()
        command.join(timeout=5)
    assert result_holder
    assert result_holder[0].exit_code == 0


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
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
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
        status_payload = json.loads(body)
        assert status_payload["refreshing"] is True
        assert (
            status_payload["message"]
            == "Measurement running. This page will update when it finishes."
        )
        assert status_payload["started_at"]
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
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
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
            "started_at": None,
            "readiness": "ready",
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
    assert "Safety scan scope" in html
    assert "git diff HEAD" in html


def test_dashboard_exposes_live_measurement_status_and_disables_running_button():
    html = render_dashboard_html(
        dict(EVIDENCE),
        refresh_token="issued-token",
        refreshing=True,
        refresh_message="Measurement running.",
        refresh_started_at="2026-07-21T05:00:00+00:00",
    )
    assert 'id="measurement-status"' in html
    assert 'aria-live="polite"' in html
    assert "Measurement running since 2026-07-21T05:00:00+00:00." in html
    assert "Gates can take several minutes." in html
    assert '<button type="submit" disabled>Measurement running</button>' in html


def test_cors_header_reflects_exact_allowed_origin_on_evidence_and_status():
    with _running_server(allow_origins=("http://localhost:5173",)) as port:
        for path in ("/api/evidence", "/api/status"):
            status, headers, _body = _request_with_origin(port, path, "http://localhost:5173")
            assert status == 200
            assert headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
            assert headers["Vary"] == "Origin"


def test_cors_header_absent_for_origin_not_on_allowlist():
    with _running_server(allow_origins=("http://localhost:5173",)) as port:
        status, headers, _body = _request_with_origin(port, "/api/evidence", "http://evil.example")
        assert status == 200
        assert "Access-Control-Allow-Origin" not in headers
        assert "Vary" not in headers


def test_cors_header_requires_exact_match_not_prefix_or_suffix():
    with _running_server(allow_origins=("http://localhost:5173",)) as port:
        for sneaky_origin in (
            "http://localhost:5173.evil.example",
            "evil-http://localhost:5173",
            "http://localhost:51730",
        ):
            status, headers, _body = _request_with_origin(port, "/api/evidence", sneaky_origin)
            assert status == 200
            assert "Access-Control-Allow-Origin" not in headers


def test_cors_header_absent_when_no_origin_header_sent():
    with _running_server(allow_origins=("http://localhost:5173",)) as port:
        status, headers, _body = _request_with_origin(port, "/api/evidence", None)
        assert status == 200
        assert "Access-Control-Allow-Origin" not in headers


def test_cors_header_absent_by_default_when_allow_origins_not_configured(server_port):
    # server_port fixture builds the handler via make_dashboard_handler(state) with no
    # allow_origins argument at all — the default must keep existing behaviour unchanged.
    status, headers, _body = _request_with_origin(
        server_port, "/api/evidence", "http://localhost:5173"
    )
    assert status == 200
    assert "Access-Control-Allow-Origin" not in headers
    assert "Vary" not in headers


def test_cors_header_never_added_to_html_root_even_with_matching_origin():
    with _running_server(allow_origins=("http://localhost:5173",)) as port:
        status, headers, _body = _request_with_origin(port, "/", "http://localhost:5173")
        assert status == 200
        assert "Access-Control-Allow-Origin" not in headers
        assert "Vary" not in headers


def test_cors_header_present_on_head_requests_too():
    with _running_server(allow_origins=("http://localhost:5173",)) as port:
        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            conn.request("HEAD", "/api/status", headers={"Origin": "http://localhost:5173"})
            response = conn.getresponse()
            headers = dict(response.getheaders())
            response.read()
        finally:
            conn.close()
        assert headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
        assert headers["Vary"] == "Origin"


def test_card_headings_are_trilingual_hanja_korean_english():
    html = render_dashboard_html(dict(EVIDENCE))
    for heading in (
        "眞 진</span> Truth",
        "善 선</span> Good",
        "美 미</span> Beauty",
        "仁 인</span> Humanity",
        "孝 효</span> Hyo",
        "永 영</span> Longevity",
    ):
        assert heading in html


def test_dashboard_marks_missing_measurement_time_as_not_measured():
    evidence = dict(EVIDENCE)
    evidence["measured_at"] = None
    html = render_dashboard_html(evidence)
    assert 'data-measured="Not measured"' in html
    assert 'data-measured="None"' not in html


def test_runtime_receipt_is_published_before_initial_measurement(tmp_path, monkeypatch):
    """The receipt names this runtime before the first measurement finishes.

    Observed 2026-09-16: the dashboard published its identity receipt only
    after initial evidence collection, which takes a minute or more on a real
    checkout. Until then the receipt on disk still described the *previous*
    runtime, so a consumer reading it was told, confidently, about a process
    that had already been replaced.

    The receipt does not depend on measurement — it reports the checkout, the
    tool, and the listening endpoint — so it is published as soon as the
    server is serving. This test blocks collection and reads the file from
    inside that window, which is exactly where the stale answer used to live.
    """
    import time
    from threading import Thread

    from typer.testing import CliRunner

    import hyodo.cli.main as cli_main

    (tmp_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
    (tmp_path / "hyodo").mkdir()
    receipt = tmp_path / "runtime-receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema_version": "hyodo.runtime-identity/v1",
                "target": {"root_realpath": "/gone/previous-runtime"},
                "runtime": {"pid": 1, "started_at": "2026-01-01T00:00:00+00:00"},
            }
        ),
        encoding="utf-8",
    )
    with socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    entered = Event()
    release = Event()
    server_holder = []
    seen: dict[str, object] = {}

    def blocked_collection(_root):
        # What a consumer reading the receipt would get right now.
        seen["receipt"] = receipt.read_text(encoding="utf-8")
        entered.set()
        assert release.wait(timeout=5)
        return dict(EVIDENCE)

    def capture_server(*args, **kwargs):
        server = ThreadingHTTPServer(*args, **kwargs)
        server_holder.append(server)
        return server

    monkeypatch.setattr(cli_main, "collect_dashboard_evidence", blocked_collection)
    monkeypatch.setattr(cli_main, "ThreadingHTTPServer", capture_server)
    runner = CliRunner()
    command = Thread(
        target=lambda: runner.invoke(
            app,
            [
                "dashboard",
                str(tmp_path),
                "--port",
                str(port),
                "--runtime-identity",
                str(receipt),
            ],
        ),
        daemon=True,
    )
    command.start()
    try:
        assert entered.wait(timeout=5)
        payload = json.loads(str(seen["receipt"]))
        assert payload["runtime"]["pid"] == os.getpid(), (
            "receipt still described the previous runtime while this one was serving"
        )
        assert payload["target"]["root_realpath"] == str(tmp_path.resolve())
        assert payload["service"]["endpoint"] == f"127.0.0.1:{port}"
        release.set()
        deadline = time.monotonic() + 5
        while True:
            _, _, status_body = _request(port, "GET", "/api/status")
            if json.loads(status_body)["readiness"] == "ready":
                break
            assert time.monotonic() < deadline, "real evidence was not installed"
            sleep(0.01)
    finally:
        release.set()
        if server_holder:
            server_holder[0].shutdown()
        command.join(timeout=5)
