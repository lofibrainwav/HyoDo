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
    assert 'class="orb-grid"' in html
    assert 'data-decision="ALLOW"' in html
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
    assert 'class="orb-grid"' in html
    assert 'data-decision="UNOBSERVED"' in html


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


# --- Local viewer second pass: one grid, edges, labels, orb grid, questions --


def test_grid_places_each_tile_in_its_own_row_and_column_cell(tmp_path: Path) -> None:
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
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    assert re.search(
        r'<div class="grid-cell" data-row-key="agent:t1" data-column="jin">'
        r'(?:(?!</div>).)*data-event-id="t1"',
        html,
    ), "the tool_call tile must render inside its own row's Truth column cell"
    # The mission's own prompt now maps to Hyo (brief finding 3) and sits in
    # the human row's own Hyo cell, not off-grid.
    assert re.search(
        r'<div class="grid-cell" data-row-key="human" data-column="hyo">'
        r'(?:(?!</div>).)*data-event-id="m1"',
        html,
    )


def test_column_cell_tiles_are_ordered_oldest_to_newest(tmp_path: Path) -> None:
    # t2 is written to the ledger before t1 but has the later step_index and
    # chains onto t1 (same agent lineage row) — the cell must still render
    # oldest-first, following step_index/ts rather than file write order.
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="t2",
                kind="tool_call",
                actor="agent",
                step_index=2,
                ts="2026-09-06T00:00:02+00:00",
                parent_event_id="t1",
                tool={"name": "ruff check"},
            ),
            _event(
                event_id="t1",
                kind="tool_call",
                actor="agent",
                step_index=1,
                ts="2026-09-06T00:00:01+00:00",
                parent_event_id="m1",
                tool={"name": "pyright"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    # Both tool calls are Truth events sharing one lineage row (t1 is t2's
    # agent-actor parent), so they land in the same cell; row order must
    # follow step_index/ts (t1 first) regardless of ledger write order.
    cell_match = re.search(
        r'<div class="grid-cell" data-row-key="agent:t1" data-column="jin">(.*?)</div>', html
    )
    assert cell_match is not None
    ids_in_order = re.findall(r'data-event-id="([^"]+)"', cell_match.group(1))
    assert ids_in_order == ["t1", "t2"]


def test_edge_overlay_draws_parent_and_evidence_ref_edges(tmp_path: Path) -> None:
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
                evidence_refs=["t1"],
                policy={"decision": "ALLOW", "rule_id": None, "evaluated_by": "hyodo.policy/v1"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    svg_tag = re.search(r"<svg id=\"edge-overlay\"[^>]*>", html)
    assert svg_tag is not None
    assert 'data-parent-edges="2"' in svg_tag.group(0)  # m1->t1, t1->d1
    assert 'data-evidence-edges="1"' in svg_tag.group(0)  # d1 cites t1
    assert 'class="edge edge-parent"' in html
    assert 'class="edge edge-evidence"' in html


def test_edge_overlay_draws_a_broken_stub_for_an_unresolved_ref(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="d1",
                kind="decision",
                actor="hyodo",
                step_index=1,
                parent_event_id="m1",
                evidence_refs=["does-not-exist"],
                policy={"decision": "ALLOW", "rule_id": None, "evaluated_by": "hyodo.policy/v1"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    svg_tag = re.search(r"<svg id=\"edge-overlay\"[^>]*>", html)
    assert svg_tag is not None
    assert int(re.search(r'data-broken-edges="(\d+)"', svg_tag.group(0)).group(1)) >= 1
    assert 'class="edge edge-broken"' in html


def test_lineage_agent_row_label_is_short_lineage_id_not_the_tool_name(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="a-very-long-lineage-event-id",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="m1",
                tool={"name": "pyright"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    assert ">agent a-very-l<" in html  # first 8 chars of the lineage id
    assert ">agent:pyright<" not in html


def test_actor_id_row_label_stays_agent_and_the_actor_id(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="t1",
                kind="tool_call",
                actor="agent",
                actor_id="seat-alpha",
                step_index=1,
                parent_event_id="m1",
                tool={"name": "pyright"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    assert ">agent seat-alpha<" in html


def test_orb_lit_square_count_equals_the_run_observed_count(tmp_path: Path) -> None:
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

    lit_match = re.search(r'data-lit-count="(\d+)"', html)
    assert lit_match is not None
    lit_count = int(lit_match.group(1))
    assert lit_count > 0
    assert html.count('class="orb-cell orb-cell-lit"') == lit_count
    assert "%" not in re.search(r'<div class="orb-grid".*?</div>', html, re.DOTALL).group(0)


def test_orb_grid_has_a_reduced_motion_guard() -> None:
    from hyodo.dashboard import render_graph_html

    html = render_graph_html({"status": "READY", "nodes": [], "edges": []})
    assert "prefers-reduced-motion" in html
    assert ".orb-grid { animation:none }" in html.replace("{{ ", "{ ").replace(" }}", " }")


def test_empty_column_shows_its_fixed_question(tmp_path: Path) -> None:
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
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    seon_header = re.search(
        r'<div class="grid-colhead" data-column="seon">(.*?)</div>\s*<div', html, re.DOTALL
    )
    assert seon_header is not None
    assert "Which policy decision governed this action?" in seon_header.group(1)


def test_nested_child_row_is_indented_with_a_collapse_toggle(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="h1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="parent-call",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="h1",
                tool={"name": "dispatch"},
            ),
            _event(
                event_id="child-call",
                kind="tool_call",
                actor="agent",
                actor_id="sub-agent",
                step_index=2,
                parent_event_id="parent-call",
                tool={"name": "pyright"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    child_row = re.search(
        r'<div class="grid-row" data-row-key="agent:sub-agent" data-parent-row="([^"]+)" '
        r'data-depth="(\d+)"',
        html,
    )
    assert child_row is not None
    assert child_row.group(1) != ""
    assert int(child_row.group(2)) >= 1
    assert 'class="row-toggle" data-row-toggle="agent:parent-call"' in html
    assert re.search(r"padding-left:(?!0px)\d+px", html)


# --- Fix round 1 (coordinator, live-screenshot review) ---------------------


def test_tile_label_is_tool_name_or_kind_and_title_carries_the_full_pairing(
    tmp_path: Path,
) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="w1",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="m1",
                tool={"name": "write_file", "paths": ["a.txt"]},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    assert ">write_file<" in html
    assert "tool_call..." not in html
    assert 'title="tool_call: write_file"' in html
    assert ">prompt<" in html  # the mission tile shows the bare kind, no tool name


def test_edge_coordinates_stay_within_grid_bounds_and_skip_offgrid_tiles(
    tmp_path: Path,
) -> None:
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
            # No output_digest -> assign_columns gives this no column at
            # all (off-grid), per the brief's model_response rule.
            _event(
                event_id="resp1",
                kind="model_response",
                actor="agent",
                step_index=2,
                parent_event_id="t1",
            ),
            _event(
                event_id="d1",
                kind="decision",
                actor="hyodo",
                step_index=3,
                parent_event_id="resp1",
                evidence_refs=["t1"],
                policy={"decision": "ALLOW", "rule_id": None, "evaluated_by": "hyodo.policy/v1"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    svg_tag_match = re.search(r'<svg id="edge-overlay"[^>]*>', html)
    assert svg_tag_match is not None
    svg_tag = svg_tag_match.group(0)
    width = int(re.search(r'width="(\d+)"', svg_tag).group(1))
    height = int(re.search(r'height="(\d+)"', svg_tag).group(1))

    assert 'data-parent-edges="1"' in svg_tag  # m1 -> t1 only; resp1 is off-grid
    assert 'data-evidence-edges="1"' in svg_tag  # d1 cites t1
    assert 'data-broken-edges="0"' in svg_tag  # nothing dangling
    offgrid_match = re.search(r'data-offgrid-edges="(\d+)"', svg_tag)
    assert offgrid_match is not None
    assert int(offgrid_match.group(1)) == 2  # t1->resp1 and resp1->d1

    # No edge is ever drawn to the off-grid model_response tile.
    assert 'data-source="resp1"' not in html
    assert 'data-target="resp1"' not in html

    svg_body_match = re.search(r'<svg id="edge-overlay"[^>]*>(.*?)</svg>', html, re.DOTALL)
    assert svg_body_match is not None
    svg_body = svg_body_match.group(1)
    assert svg_body, "expected at least one drawn edge for this fixture"
    for match in re.finditer(r'[xy][12]="(-?[\d.]+)"', svg_body):
        assert 0 <= float(match.group(1)) <= max(width, height)
    for path_d in re.findall(r'd="([^"]+)"', svg_body):
        for x_str, y_str in re.findall(r"(-?[\d.]+),(-?[\d.]+)", path_d):
            assert 0 <= float(x_str) <= width
            assert 0 <= float(y_str) <= height
