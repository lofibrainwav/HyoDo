"""HTTP contract for `GET /api/verification-view`.

The route is a sibling of `/api/graph`, not a query parameter on it. Two
payload shapes under one path would make that path's CORS eligibility and
cache meaning ambiguous, and the existing routes (`/api/evidence`,
`/api/status`, `/api/graph`, `/api/actor`, `/api/identity`) are already
siblings rather than branches of one handler.

Like `/api/graph`, it reads the ledger live on every request. A case file that
quietly serves a cached answer is worse than no case file, because the reader
cannot tell how old the evidence is.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

from hyodo.cli.main import _CORS_ELIGIBLE_PATHS, DashboardState, make_dashboard_handler
from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
from hyodo.verification_view import VERIFICATION_VIEW_SCHEMA_VERSION

ROUTE = "/api/verification-view"

EVIDENCE: dict[str, object] = {
    "schema_version": "hyodo.dashboard-evidence/v1",
    "target": "/tmp/HyoDo",
    "measured_at": "2026-09-06T00:00:00+00:00",
    "gates": {},
    "safety": {"risk_score": 0, "source": "git diff HEAD", "findings": []},
}


def _event(**overrides: Any) -> str:
    base: dict[str, Any] = {
        "schema_version": "hyodo.agent-event/v1",
        "run_id": "run-1",
        "ts": "2026-09-06T00:00:00+00:00",
        "kind": "prompt",
        "actor": "human",
        "step_index": 0,
        "tool": {},
        "policy": {},
        "evidence_refs": [],
    }
    base.update(overrides)
    return json.dumps(base)


def _write_ledger(root: Path, lines: list[str]) -> None:
    path = root / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _append_event(root: Path, line: str) -> None:
    with (root / AGENT_EVENTS_RELATIVE_PATH).open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


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


def _get(port: int, path: str) -> tuple[int, str | None, bytes]:
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request("GET", path)
    response = connection.getresponse()
    body = response.read()
    content_type = response.getheader("Content-Type")
    connection.close()
    return response.status, content_type, body


def _minimal_run() -> list[str]:
    return [
        _event(event_id="e0", kind="prompt", actor="human", step_index=0),
        _event(
            event_id="e1",
            kind="tool_call",
            actor="agent",
            actor_id="a1",
            step_index=1,
            parent_event_id="e0",
            tool={"name": "pytest", "paths": ["tests/"], "urls": []},
        ),
    ]


def test_route_serves_the_verification_view_schema(tmp_path: Path) -> None:
    _write_ledger(tmp_path, _minimal_run())
    with _running_server(tmp_path) as port:
        status, content_type, body = _get(port, ROUTE)
    assert status == 200
    assert content_type == "application/json"
    payload = json.loads(body)
    assert payload["schema_version"] == VERIFICATION_VIEW_SCHEMA_VERSION
    assert payload["authority"] == "UNOBSERVED"


def test_route_is_404_without_a_configured_evidence_root() -> None:
    with _running_server(None) as port:
        status, _content_type, _body = _get(port, ROUTE)
    assert status == 404


def test_route_reflects_a_live_ledger_write_without_a_manual_refresh(
    tmp_path: Path,
) -> None:
    """A case file that serves a cached answer cannot be trusted as evidence."""
    _write_ledger(tmp_path, _minimal_run())
    with _running_server(tmp_path) as port:
        _status, _content_type, before = _get(port, ROUTE)
        _append_event(
            tmp_path,
            _event(
                event_id="e2",
                kind="tool_result",
                actor="agent",
                actor_id="a1",
                step_index=2,
                parent_event_id="e1",
                io={"output_digest": "abc123"},
            ),
        )
        _status, _content_type, after = _get(port, ROUTE)

    assert set(json.loads(before)["events"]) == {"e0", "e1"}
    assert set(json.loads(after)["events"]) == {"e0", "e1", "e2"}


def test_route_agrees_with_api_graph_on_the_same_ledger(tmp_path: Path) -> None:
    """Both routes read the same producer, so their event sets must match."""
    _write_ledger(tmp_path, _minimal_run())
    with _running_server(tmp_path) as port:
        _status, _content_type, view_body = _get(port, ROUTE)
        _status, _content_type, graph_body = _get(port, "/api/graph")

    view = json.loads(view_body)
    graph = json.loads(graph_body)
    assert set(view["events"]) == {node["id"] for node in graph["nodes"]}
    assert view["status"] == graph["status"]


def test_route_is_cors_eligible_like_the_other_json_routes() -> None:
    assert ROUTE in _CORS_ELIGIBLE_PATHS
    # The HTML pages must never become CORS targets.
    assert "/graph" not in _CORS_ELIGIBLE_PATHS
    assert "/" not in _CORS_ELIGIBLE_PATHS


def test_route_never_serves_a_score_or_an_aggregate(tmp_path: Path) -> None:
    _write_ledger(tmp_path, _minimal_run())
    with _running_server(tmp_path) as port:
        _status, _content_type, body = _get(port, ROUTE)
    payload = json.loads(body)
    assert not {"score", "confidence", "aggregate"} & set(payload)
    assert b"harmony_aggregate" not in body


def test_route_serves_an_empty_ledger_without_inventing_a_case(tmp_path: Path) -> None:
    _write_ledger(tmp_path, [])
    with _running_server(tmp_path) as port:
        status, _content_type, body = _get(port, ROUTE)
    assert status == 200
    payload = json.loads(body)
    assert payload["events"] == {}
    assert payload["lanes"] == []
    assert payload["authority"] == "UNOBSERVED"


def test_acceptance_join_api_and_html_share_canonical_rows(tmp_path):
    import hashlib

    contract = {
        "contract_id": "api-fixture",
        "revision": 1,
        "origin": "HUMAN_RECONSTITUTED",
        "criteria_count": 7,
        "required_criteria": [{"id": f"E{i:02}", "text": "required"} for i in range(1, 8)],
        "governing_invariants": [{"id": f"E{i:02}", "text": "invariant"} for i in range(8, 13)],
    }
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(contract))
    _write_ledger(tmp_path, _minimal_run())
    (tmp_path / ".hyodo/acceptance-contract.json").write_text(
        json.dumps(
            {
                "path": str(path),
                "digest": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    )
    with _running_server(tmp_path) as port:
        status, _, body = _get(port, ROUTE)
        html_status, _, html = _get(port, "/graph")
    assert status == html_status == 200
    join = json.loads(body)["acceptance_join"]
    assert join["status"] == "HOLD"
    assert len(join["criteria"]) == 7
    for row in join["criteria"]:
        assert f"{row['id']}: {row['state']}" in html.decode()
    assert join["contract_digest"] in html.decode()
