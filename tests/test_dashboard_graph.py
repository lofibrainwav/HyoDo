"""HTTP contract for the local evidence-graph viewer (`GET /graph`, `/api/graph`).

Rollout step (b),
`docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`.
Both routes read `.hyodo/agent-events.jsonl` live via
`hyodo.report.build_report_graph` — the same corrupt/unreadable handling as
`hyodo report --format graph` — rather than the cached six-card snapshot.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from hyodo.cli.main import DASHBOARD_CSP, DashboardState, make_dashboard_handler
from hyodo.dashboard import GRAPH_SCRIPT, GRAPH_SCRIPT_SHA256
from hyodo.event_graph import GRAPH_SCHEMA_VERSION
from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
from hyodo.report import render_report

EVIDENCE: dict[str, object] = {
    "schema_version": "hyodo.dashboard-evidence/v1",
    "target": "/tmp/HyoDo",
    "measured_at": "2026-09-06T00:00:00+00:00",
    "gates": {},
    "safety": {"risk_score": 0, "source": "git diff HEAD", "findings": []},
}


def _write_ledger(root: Path, lines: list[str]) -> None:
    path = root / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _event(**overrides: object) -> str:
    base = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "e0",
        "run_id": "run-1",
        "ts": "2026-09-06T00:00:00+00:00",
        "kind": "prompt",
        "actor": "human",
        "step_index": 0,
        "tool": {},
        "policy": {},
    }
    base.update(overrides)
    return json.dumps(base)


@contextmanager
def _running_server(root: Path | None):
    state = DashboardState(dict(EVIDENCE))
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_dashboard_handler(state, root=root))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _request(port: int, method: str, path: str) -> tuple[int, dict[str, str], bytes]:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(method, path)
        response = conn.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        conn.close()


def test_graph_page_has_five_column_headers_in_order_and_the_orb(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="t1",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="m1",
                tool={"name": "pyright"},
            ),
            _event(
                event_id="d1",
                kind="decision",
                actor="hyodo",
                step_index=2,
                parent_event_id="t1",
                policy={"decision": "ALLOW", "rule_id": None, "evaluated_by": "hyodo.policy/v1"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        status, headers, body = _request(port, "GET", "/graph")
        assert status == 200
        assert headers["Content-Type"] == "text/html; charset=utf-8"
        html = body.decode("utf-8")

    column_ids = re.findall(r'<h2 id="col-(\w+)"', html)
    assert column_ids == ["jin", "seon", "mi", "in", "hyo"]
    assert 'class="orb orb-allow' in html
    assert 'role="status">UNOBSERVED' not in html


def test_graph_page_shows_unobserved_notice_for_a_corrupt_ledger(tmp_path: Path) -> None:
    _write_ledger(tmp_path, ["{not valid json"])
    with _running_server(tmp_path) as port:
        status, _headers, body = _request(port, "GET", "/graph")
        assert status == 200
        html = body.decode("utf-8")

    assert 'role="status">UNOBSERVED' in html
    # Columns still render even when the ledger is corrupt — never blank space.
    column_ids = re.findall(r'<h2 id="col-(\w+)"', html)
    assert column_ids == ["jin", "seon", "mi", "in", "hyo"]
    assert 'class="orb orb-unobserved' in html


def test_graph_page_has_no_external_scripts_no_links_and_no_forbidden_words(
    tmp_path: Path,
) -> None:
    _write_ledger(tmp_path, [_event()])
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    assert "<script src" not in html
    assert "<link " not in html
    assert "probability" not in html.lower()
    assert "confidence" not in html.lower()


def test_api_graph_returns_schema_id_and_mirrors_report_format_graph_status(
    tmp_path: Path,
) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1"),
            _event(
                event_id="t1",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="m1",
            ),
        ],
    )
    _content, _digest, report_details = render_report(tmp_path, "graph")

    with _running_server(tmp_path) as port:
        status, headers, body = _request(port, "GET", "/api/graph")
        assert status == 200
        assert headers["Content-Type"] == "application/json"
        payload = json.loads(body)

    assert payload["schema_version"] == GRAPH_SCHEMA_VERSION
    assert payload["status"] == report_details["status"]
    assert payload["summary"]["events"] == report_details["events"]


def test_api_graph_reflects_the_ledger_unreadable_state(tmp_path: Path) -> None:
    _write_ledger(tmp_path, ["not even json {"])
    with _running_server(tmp_path) as port:
        status, _headers, body = _request(port, "GET", "/api/graph")
        assert status == 200
        payload = json.loads(body)

    assert payload["status"] == "UNOBSERVED"
    assert payload["reason"] == "corrupt_event_lines"


def test_graph_routes_404_without_a_configured_root() -> None:
    with _running_server(None) as port:
        status, _headers, _body = _request(port, "GET", "/graph")
        assert status == 404
        status, _headers, _body = _request(port, "GET", "/api/graph")
        assert status == 404


def test_graph_page_reflects_a_live_ledger_write_without_a_manual_refresh(
    tmp_path: Path,
) -> None:
    _write_ledger(tmp_path, [_event()])
    with _running_server(tmp_path) as port:
        _status, _headers, before = _request(port, "GET", "/api/graph")
        assert json.loads(before)["summary"]["events"] == 1

        _write_ledger(tmp_path, [_event(event_id="m1"), _event(event_id="m2", step_index=1)])
        _status, _headers, after = _request(port, "GET", "/api/graph")
        assert json.loads(after)["summary"]["events"] == 2


def test_graph_script_clears_the_panel_and_returns_focus_on_escape() -> None:
    # Judge fix round 1, ruling 2: Escape must clear the detail panel text
    # and return focus to the last focused cell (or the grid's first cell).
    assert 'event.key !== "Escape"' in GRAPH_SCRIPT or '"Escape"' in GRAPH_SCRIPT
    assert "keydown" in GRAPH_SCRIPT
    assert "lastFocusedCell" in GRAPH_SCRIPT
    assert ".focus()" in GRAPH_SCRIPT
    assert "innerHTML" not in GRAPH_SCRIPT


def test_orb_caption_total_is_visibly_derived_from_the_printed_column_pairs(
    tmp_path: Path,
) -> None:
    # Judge fix round 1, ruling 4: the orb's summed observed/expected pair
    # must be visibly traceable to the five column badges it is added from.
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="t1",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="m1",
                tool={"name": "pyright"},
            ),
            _event(
                event_id="d1",
                kind="decision",
                actor="hyodo",
                step_index=2,
                parent_event_id="t1",
                policy={"decision": "ALLOW", "rule_id": None, "evaluated_by": "hyodo.policy/v1"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    caption_total = re.search(r"orb-caption[^>]*>\w+ · (\d+)/(\d+) observed", html)
    breakdown = re.search(r'<p class="orb-breakdown">([^<]*)</p>', html)
    assert caption_total is not None
    assert breakdown is not None
    pairs = re.findall(r"(\d+)/(\d+)", breakdown.group(1))
    assert pairs, "breakdown line has no per-column pairs"
    assert sum(int(observed) for observed, _expected in pairs) == int(caption_total.group(1))
    assert sum(int(expected) for _observed, expected in pairs) == int(caption_total.group(2))


def test_graph_script_sha256_and_csp_hash_match_the_script_text() -> None:
    digest = base64.b64encode(hashlib.sha256(GRAPH_SCRIPT.encode("utf-8")).digest()).decode("ascii")
    assert digest == GRAPH_SCRIPT_SHA256
    assert f"'sha256-{GRAPH_SCRIPT_SHA256}'" in DASHBOARD_CSP
