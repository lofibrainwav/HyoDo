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

import pytest

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


TRUTH_FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "dashboard-truth-cases.json").read_text()
)


def _truth_fixture_events(name: str) -> list[str]:
    common = [
        _event(event_id="intent", kind="prompt", actor="human", step_index=0),
        _event(
            event_id="call",
            kind="tool_call",
            actor="agent",
            step_index=1,
            parent_event_id="intent",
            tool={"name": "pytest"},
        ),
        _event(
            event_id="result",
            kind="tool_result",
            actor="agent",
            step_index=2,
            parent_event_id="call",
            io={"output_digest": "digest-1"},
        ),
    ]
    if name == "normal_close":
        return [
            *common,
            _event(
                event_id="verdict",
                kind="decision",
                actor="hyodo",
                step_index=3,
                parent_event_id="result",
                evidence_refs=["result"],
                policy={"decision": "ALLOW", "evaluated_by": "hyodo"},
            ),
        ]
    if name == "withheld_allow":
        return [
            *common,
            _event(
                event_id="verdict",
                kind="decision",
                actor="hyodo",
                step_index=3,
                parent_event_id="result",
                evidence_refs=["effect-readback"],
                policy={"decision": "ALLOW", "evaluated_by": "hyodo"},
            ),
        ]
    if name == "multi_parent_join":
        return [
            _event(event_id="intent", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="call-a",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="intent",
            ),
            _event(
                event_id="call-b",
                kind="tool_call",
                actor="agent",
                step_index=2,
                parent_event_id="intent",
            ),
            _event(
                event_id="result",
                schema_version="hyodo.agent-event/v2",
                kind="tool_result",
                actor="agent",
                step_index=3,
                parent_event_ids=["call-a", "call-b"],
                io={"output_digest": "digest-join"},
            ),
            _event(
                event_id="verdict",
                kind="decision",
                actor="hyodo",
                step_index=4,
                parent_event_id="result",
                policy={"decision": "ASK", "evaluated_by": "hyodo"},
            ),
        ]
    if name == "missing_result":
        return common[:2]
    if name == "missing_intent":
        return [
            _event(event_id="call", kind="tool_call", actor="agent", step_index=0),
            _event(
                event_id="result",
                kind="tool_result",
                actor="agent",
                step_index=1,
                parent_event_id="call",
                io={"output_digest": "digest-no-intent"},
            ),
        ]
    if name == "broken_evidence":
        return [
            *common,
            _event(
                event_id="verdict",
                kind="decision",
                actor="hyodo",
                step_index=3,
                parent_event_id="result",
                evidence_refs=["missing-receipt"],
                policy={"decision": "DENY", "evaluated_by": "hyodo"},
            ),
        ]
    raise AssertionError(f"unknown truth fixture: {name}")


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
    assert 'id="daw-arrow-parent"' in html
    assert 'id="daw-arrow-evidence"' in html
    assert 'marker-end="url(#daw-arrow-parent)"' in html
    assert 'marker-end="url(#daw-arrow-evidence)"' in html


def test_daw_parallel_events_do_not_merge_distinct_participants(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="parallel-a-call", kind="tool_call", actor="agent", step_index=1),
            _event(event_id="parallel-b-call", kind="tool_call", actor="agent", step_index=1),
            _event(event_id="parallel-a-result", kind="tool_result", actor="agent", step_index=1),
            _event(event_id="parallel-b-result", kind="tool_result", actor="agent", step_index=1),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    assert 'class="daw-cell daw-cluster" data-event-count="4"' not in html
    for event_id in (
        "parallel-a-call",
        "parallel-b-call",
        "parallel-a-result",
        "parallel-b-result",
    ):
        assert f'data-daw-track="agent:{event_id}"' in html
    assert ">A call</button>" in html
    assert ">B call</button>" in html
    assert ">A res</button>" in html
    assert ">B res</button>" in html


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


def test_edge_paths_render_empty_d_with_source_target_kind_and_skip_offgrid_tiles(
    tmp_path: Path,
) -> None:
    # Fix round 2 (coordinator, live-screenshot review): the server no
    # longer computes edge geometry at all (round 1's schematic
    # server-side pixel math drifted once real, variable-height rows
    # differed from the assumed fixed row height). It only classifies and
    # counts edges, emitting an empty `d` for `GRAPH_SCRIPT`'s
    # `layoutEdges()` to fill in client-side from real measured layout.
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
                evidence_refs=["t1", "does-not-exist"],
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
    # No server-computed geometry attributes on the <svg> itself either.
    assert "width=" not in svg_tag
    assert "height=" not in svg_tag
    assert "viewBox=" not in svg_tag

    assert 'data-parent-edges="1"' in svg_tag  # m1 -> t1 only; resp1 is off-grid
    assert 'data-evidence-edges="1"' in svg_tag  # d1 cites t1
    assert 'data-broken-edges="1"' in svg_tag  # d1 cites does-not-exist
    offgrid_match = re.search(r'data-offgrid-edges="(\d+)"', svg_tag)
    assert offgrid_match is not None
    assert int(offgrid_match.group(1)) == 2  # t1->resp1 and resp1->d1

    # No edge is ever drawn to the off-grid model_response tile.
    assert 'data-source="resp1"' not in html
    assert 'data-target="resp1"' not in html

    parent_path = re.search(
        r'<path class="edge edge-parent" data-source="m1" data-target="t1" '
        r'data-kind="parent" d="([^"]*)"',
        html,
    )
    assert parent_path is not None
    assert parent_path.group(1) == ""

    evidence_path = re.search(
        r'<path class="edge edge-evidence" data-source="t1" data-target="d1" '
        r'data-kind="evidence" d="([^"]*)"',
        html,
    )
    assert evidence_path is not None
    assert evidence_path.group(1) == ""

    broken_path = re.search(
        r'<path class="edge edge-broken" data-source="d1" data-kind="broken" d="([^"]*)"',
        html,
    )
    assert broken_path is not None
    assert broken_path.group(1) == ""
    assert "data-target" not in re.search(r'<path class="edge edge-broken"[^>]*>', html).group(0)


def test_graph_script_layout_edges_function_and_csp_hash_match() -> None:
    # Fix round 2, JS-free contract test: GRAPH_SCRIPT must carry the
    # client-side edge-measurement function and wire it to load/resize/
    # collapse-toggle, and its CSP sha256 allowance must still match the
    # (regenerated) script text — no browser required to check either.
    assert "function layoutEdges" in GRAPH_SCRIPT
    assert "getBoundingClientRect" in GRAPH_SCRIPT
    assert 'window.addEventListener("load", layoutEdges)' in GRAPH_SCRIPT
    assert 'window.addEventListener("resize", layoutEdges)' in GRAPH_SCRIPT
    assert "layoutEdges();" in GRAPH_SCRIPT

    digest = base64.b64encode(hashlib.sha256(GRAPH_SCRIPT.encode("utf-8")).digest()).decode("ascii")
    assert digest == GRAPH_SCRIPT_SHA256
    assert f"'sha256-{GRAPH_SCRIPT_SHA256}'" in DASHBOARD_CSP


def _bare_event(event_id: str, tool_name: str, *, output_digest: str | None = None) -> dict:
    """One graph node shaped like the real ledger's shell calls."""
    return {
        "id": event_id,
        "type": "event",
        "run_id": "r1",
        "ts": "2026-09-06T00:00:00+00:00",
        "kind": "tool_call",
        "actor": "agent",
        "actor_id": "zaryong",
        "step_index": 0,
        "decision": None,
        "policy": {"rule_id": None, "reason": None, "evaluated_by": None},
        "tool": {"name": tool_name, "method": None, "paths": [], "urls": []},
        "io": {"output_digest": output_digest},
    }


def test_an_event_with_nothing_recorded_still_gets_a_gutter_of_its_own() -> None:
    # The viewer must never let an event disappear just because there was
    # nothing on it to classify -- "we could not measure this" is itself a
    # finding the operator needs to see.
    from hyodo.dashboard import render_graph_html

    html = render_graph_html(
        {"status": "READY", "nodes": [_bare_event("e1", "ssh-keygen")], "edges": [], "root": "/tmp"}
    )
    assert 'class="gutter"' in html
    assert "Unmeasured" in html


def test_the_two_gutters_render_as_separate_labelled_sections() -> None:
    # A mapping gap and a recording gap are different problems with
    # different fixes, so they must not share one bucket in the UI either.
    from hyodo.dashboard import render_graph_html

    html = render_graph_html(
        {
            "status": "READY",
            "nodes": [
                _bare_event("e1", "ssh-keygen"),
                _bare_event("e2", "git.status", output_digest="dcb01359d6b9"),
            ],
            "edges": [],
            "root": "/tmp",
        }
    )
    assert "Unmeasured" in html
    assert "Unclassified" in html
    assert html.count('class="gutter"') == 2
    assert "ssh-keygen" in html
    assert "git.status" in html


def test_each_gutter_states_how_many_events_it_holds() -> None:
    # The split only pays off if the two counts are readable side by side:
    # "53 unmeasured, 10 unclassified" says fix the recording, while the
    # reverse would say fix the table.
    from hyodo.dashboard import render_graph_html

    html = render_graph_html(
        {
            "status": "READY",
            "nodes": [
                _bare_event("e1", "ssh-keygen"),
                _bare_event("e2", "gh"),
                _bare_event("e3", "git.status", output_digest="dcb01359d6b9"),
            ],
            "edges": [],
            "root": "/tmp",
        }
    )
    assert 'data-gutter-count="2"' in html
    assert 'data-gutter-count="1"' in html


def test_daw_lanes_follow_the_role_the_graph_already_decided(tmp_path: Path) -> None:
    """Two `actor="agent"` events with different roles must not share a lane.

    `build_actor_rows` already reads causal lineage to call one row an
    orchestrator and another a worker, and `build_report_graph` already ships
    that as `graph["rows"]`. Before this, the timeline pooled both into one
    "role unobserved" lane by reading `actor` alone — a viewer disagreeing
    with its own producer about something the producer had measured.
    """
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="lead-call",
                kind="tool_call",
                actor="agent",
                actor_id="lead",
                step_index=1,
                parent_event_id="m1",
                tool={"name": "Task", "paths": [], "urls": []},
            ),
            _event(
                event_id="sub-call",
                kind="tool_call",
                actor="agent",
                actor_id="sub",
                step_index=2,
                parent_event_id="lead-call",
                tool={"name": "Bash", "paths": [], "urls": []},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    from hyodo.dashboard import _daw_track, _role_by_event
    from hyodo.report import build_report_graph

    graph = build_report_graph(tmp_path)
    roles = _role_by_event(graph)
    by_id = {node["id"]: node for node in graph["nodes"]}

    assert roles["lead-call"] == "orchestrator"
    assert roles["sub-call"] == "worker"
    assert _daw_track(by_id["lead-call"], roles) == "planner"
    assert _daw_track(by_id["sub-call"], roles) == "agent"
    # Both are actor="agent", so the old actor-only reading pooled them.
    assert _daw_track(by_id["lead-call"]) == _daw_track(by_id["sub-call"]) == "agent"
    # Once a role is observed, the lane stops claiming it is unobserved.
    assert 'data-daw-track="agent:lead"' in html
    assert 'data-daw-track="agent:sub"' in html
    assert "Agent / worker" not in html


def test_dashboard_header_and_rail_read_verification_view_facts(tmp_path: Path) -> None:
    """The operator surface exposes recorded and presentable facts together."""
    _write_ledger(
        tmp_path,
        [
            _event(
                event_id="intent",
                kind="prompt",
                actor="human",
                step_index=0,
                ts="2026-09-18T18:40:00+00:00",
            ),
            _event(
                event_id="call",
                kind="tool_call",
                actor="agent",
                step_index=1,
                ts="2026-09-18T18:41:00+00:00",
                parent_event_id="intent",
                tool={"name": "pytest"},
            ),
            _event(
                event_id="result",
                kind="tool_result",
                actor="agent",
                step_index=2,
                ts="2026-09-18T18:42:04+00:00",
                parent_event_id="call",
                io={"output_digest": "digest-1"},
            ),
            _event(
                event_id="verdict",
                kind="decision",
                actor="hyodo",
                step_index=3,
                ts="2026-09-18T18:42:37+00:00",
                parent_event_id="result",
                policy={"decision": "ALLOW", "evaluated_by": "hyodo", "reason": "tests passed"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    assert 'aria-label="verification status"' in html
    assert 'data-recorded-decision="ALLOW"' in html
    assert 'data-presentable-decision="ALLOW"' in html
    assert 'aria-label="verification rail"' in html
    assert 'data-stage="intent" data-state="OBSERVED"' in html
    assert 'data-stage="action" data-state="OBSERVED"' in html
    assert 'data-stage="result" data-state="OBSERVED"' in html
    assert 'data-stage="evidence" data-state="UNOBSERVED"' in html
    assert 'data-stage="decision" data-state="ALLOW"' in html
    assert "18:42:37" in html


def test_dashboard_withheld_allow_stays_withheld_in_header_and_rail(tmp_path: Path) -> None:
    """An unresolved graph must never turn its recorded ALLOW green."""
    _write_ledger(
        tmp_path,
        [
            _event(event_id="intent", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="call",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="intent",
                tool={"name": "deploy"},
            ),
            _event(
                event_id="verdict",
                kind="decision",
                actor="hyodo",
                step_index=2,
                parent_event_id="call",
                policy={"decision": "ALLOW", "evaluated_by": "hyodo"},
                evidence_refs=["effect-readback"],
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    assert 'data-recorded-decision="ALLOW"' in html
    assert 'data-presentable-decision="UNOBSERVED"' in html
    assert 'data-stage="decision" data-state="UNOBSERVED"' in html
    assert "recordedDecision" in html
    assert "FIVE-LENS APERTURE" in html
    assert "永 / CONTINUITY" in html
    assert "no independent continuity assessment is supplied by this view" in html
    assert "Chronological placement alone does not establish continuity" in html
    assert "data-run-lens-state" in html
    assert "runCoverage" in html
    assert "prefers-reduced-motion:reduce" in html
    assert "WHAT IS MISSING" in html


def test_the_lane_still_says_unobserved_when_no_role_was_measured() -> None:
    """A payload without `rows` must fall back, not invent a role."""
    from hyodo.dashboard import render_graph_html

    html = render_graph_html(
        {
            "status": "READY",
            "nodes": [_bare_event("e1", "ssh-keygen")],
            "edges": [],
            "root": "/tmp",
        }
    )
    assert "Agent / role unobserved" in html
    assert "Agent / worker" not in html


def test_missing_panel_names_each_gap_and_what_to_fix(tmp_path: Path) -> None:
    """The panel is the point: a reader must not page the ledger to find gaps."""
    _write_ledger(
        tmp_path,
        [
            _event(
                event_id="c1",
                kind="tool_call",
                actor="agent",
                actor_id="a1",
                step_index=0,
                tool={"name": "deploy", "paths": [], "urls": []},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode("utf-8")

    assert 'aria-label="what is missing"' in html
    # A call nothing ever cited as a parent, and a run with no stated intent.
    assert 'data-missing-bucket="calls_without_terminal_outcome" data-missing-count="1"' in html
    assert 'data-missing-bucket="runs_without_intent" data-missing-count="1"' in html
    assert "c1" in html
    # A gap is reported, never scored or ranked.
    assert "A gap is not a failure, and closing one authorizes nothing." in html


def test_missing_panel_separates_a_recording_gap_from_a_mapping_gap() -> None:
    """Merging the two counts would erase the only useful difference."""
    from hyodo.dashboard import render_graph_html

    html = render_graph_html(
        {
            "status": "READY",
            "nodes": [
                _bare_event("e1", "ssh-keygen"),
                _bare_event("e2", "git.status", output_digest="dcb01359d6b9"),
            ],
            "edges": [],
            "root": "/tmp",
        }
    )
    assert 'data-missing-bucket="unmeasured_events" data-missing-count="1"' in html
    assert 'data-missing-bucket="unclassified_events" data-missing-count="1"' in html
    assert "Inspect the recording before adding fields." in html
    assert "never classify by tool name" in html


def test_missing_panel_never_calls_an_empty_ledger_clean() -> None:
    """No events means nothing is missing and nothing is proven."""
    from hyodo.dashboard import render_graph_html

    html = render_graph_html({"status": "READY", "nodes": [], "edges": [], "root": "/tmp"})
    assert 'data-missing-total="0"' in html
    assert "nothing is missing and nothing is proven" in html
    assert "Every recorded event resolved" not in html


def test_missing_panel_counts_agree_with_the_verification_view(tmp_path: Path) -> None:
    """One count, one source. The panel and the JSON route cannot disagree."""
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
                evidence_refs=["nowhere"],
                policy={"decision": "ALLOW", "rule_id": "r1", "reason": "cited"},
            ),
        ],
    )
    from hyodo.dashboard import render_graph_html
    from hyodo.report import build_report_graph
    from hyodo.verification_view import build_verification_view

    graph = build_report_graph(tmp_path)
    view = build_verification_view(graph, root=tmp_path)
    html = render_graph_html(graph, root=tmp_path)

    expected = len(view["missing"]["unresolved_refs"])
    assert expected == 1
    assert f'data-missing-bucket="unresolved_refs" data-missing-count="{expected}"' in html


@pytest.mark.parametrize("case", TRUTH_FIXTURES, ids=lambda case: case["name"])
def test_dashboard_truth_fixture_registry(tmp_path: Path, case: dict[str, object]) -> None:
    """The six dashboard truth cases stay visible through the real HTTP route."""
    _write_ledger(tmp_path, _truth_fixture_events(str(case["name"])))

    with _running_server(tmp_path) as port:
        status, _headers, body = _request(port, "GET", "/graph")
    assert status == 200
    html = body.decode("utf-8")

    assert f'data-recorded-decision="{case["recorded"]}"' in html
    assert f'data-presentable-decision="{case["presentable"]}"' in html
    rail = case["rail"]
    assert isinstance(rail, dict)
    for stage, state in rail.items():
        assert f'data-stage="{stage}" data-state="{state}"' in html


def test_same_unknown_role_keeps_two_participants_in_separate_timeline_rows(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="one", kind="tool_call", actor="agent", actor_id="one"),
            _event(event_id="two", kind="tool_call", actor="agent", actor_id="two"),
        ],
    )
    with _running_server(tmp_path) as port:
        _, _, body = _request(port, "GET", "/graph")
    html = body.decode()
    assert 'data-daw-track="agent:one"' in html
    assert 'data-daw-track="agent:two"' in html
    assert 'class="participant-role">role unobserved' in html
    assert "Agent / worker" not in html


def test_time_axis_orders_real_time_across_reset_run_indices() -> None:
    from hyodo.dashboard import _render_daw_timeline

    nodes = [
        {
            "id": "later",
            "actor": "agent",
            "run_id": "new",
            "step_index": 0,
            "ts": "2026-09-19T01:00:00+00:00",
        },
        {
            "id": "earlier",
            "actor": "agent",
            "run_id": "old",
            "step_index": 99,
            "ts": "2026-09-18T18:00:00-06:00",
        },
        {"id": "unknown", "actor": "agent", "run_id": "old", "step_index": 2, "ts": "not a time"},
    ]
    html, anchors = _render_daw_timeline(nodes, [])
    assert anchors["earlier"][1] < anchors["later"][1]
    assert "TIME UNOBSERVED" in html
    assert "TIME <b>EARLIER → LATER</b>" in html
    assert "永 / TIME" not in html
    assert "EARLIER → LATER" in html
    assert "2 recorded runs" in html


def test_how_shows_the_recorded_tool_without_claiming_policy_evaluation() -> None:
    from hyodo.dashboard import _event_detail_payload

    detail = _event_detail_payload(
        {"actor": "agent", "kind": "tool_call", "tool": {"name": "Bash"}, "policy": {}}
    )
    assert detail["how"] == "Bash"
    assert detail["presentableDecision"] == "UNOBSERVED"


def test_policy_rationale_is_not_presented_as_actor_intent() -> None:
    from hyodo.dashboard import _event_detail_payload

    payload = _event_detail_payload(
        {"id": "decision", "policy": {"reason": "tests passed", "decision": "ALLOW"}}
    )
    assert payload["why"].startswith("UNOBSERVED")
    assert payload["policyRationale"] == "tests passed"
    assert "tests passed" not in payload["why"]


def test_run_overview_selects_latest_run_and_exposes_recorded_trace(tmp_path: Path) -> None:
    """The landing view keeps a large ledger readable without inventing intent."""
    _write_ledger(
        tmp_path,
        [
            _event(event_id="old-request", run_id="run-old", kind="prompt", step_index=0),
            _event(event_id="new-request", run_id="run-new", kind="prompt", step_index=0),
            _event(
                event_id="new-call",
                run_id="run-new",
                kind="tool_call",
                step_index=1,
                parent_event_id="new-request",
                tool={"name": "pytest"},
            ),
            _event(
                event_id="new-result",
                run_id="run-new",
                kind="tool_result",
                step_index=2,
                parent_event_id="new-call",
                io={"output_digest": "abc123"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode()
    assert 'id="run-selector"' in html
    assert '<option value="run-new" selected>' in html
    assert 'data-run-summary="run-new"' in html
    assert "REQUEST 1" in html
    assert "RESULT 1" in html
    assert "REQUEST → RESULT → EVIDENCE" in html
    assert 'data-run-id="run-new"' in html
    assert "Missing text stays UNOBSERVED" in html


def test_event_detail_payload_marks_request_result_and_run() -> None:
    from hyodo.dashboard import _event_detail_payload

    prompt = _event_detail_payload({"run_id": "run-7", "kind": "prompt"})
    result = _event_detail_payload(
        {"run_id": "run-7", "kind": "tool_result", "io": {"output_digest": "abc123"}}
    )
    assert prompt["request"] is True
    assert prompt["result"] is False
    assert prompt["runId"] == "run-7"
    assert result["request"] is False
    assert result["result"] is True


def test_run_overview_marks_missing_request_without_counting_opaque_run_id(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [_event(event_id="call", run_id="run-no-prompt", kind="tool_call", step_index=0)],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode()
    assert "REQUEST UNOBSERVED" in html
    assert "GAPS 3" in html
    assert "[hidden] { display:none !important }" in html


def test_timeline_is_bounded_for_large_ledgers(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(
                event_id=f"event-{index}",
                run_id="run-large",
                kind="tool_call",
                step_index=index,
                ts=f"2026-09-06T00:{index // 60:02d}:{index % 60:02d}+00:00",
            )
            for index in range(100)
        ],
    )
    with _running_server(tmp_path) as port:
        _status, _headers, body = _request(port, "GET", "/graph")
    html = body.decode()
    assert "SHOWING 80 OF 100" in html


def test_promise_observation_does_not_promote_activity_to_fulfillment(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="call", run_id="run-action-only", kind="tool_call", step_index=0),
            _event(
                event_id="result",
                run_id="run-action-only",
                kind="tool_result",
                step_index=1,
                parent_event_id="call",
                io={"output_digest": "abc123"},
            ),
        ],
    )
    with _running_server(tmp_path) as port:
        _, _, body = _request(port, "GET", "/graph")
    html = body.decode()
    for stage in ("Human Intent", "Promise", "Contract", "Boundaries", "Artifact", "Readback"):
        assert f'data-promise-stage="{stage}"><b>{stage}</b> <strong>UNOBSERVED</strong>' in html
    assert 'data-promise-stage="Action"><b>Action</b> <strong>OBSERVED</strong>' in html
    assert 'data-promise-stage="Trust"><b>Trust</b> <strong>HUMAN JUDGMENT</strong>' in html
    assert "not verified connections or a completion score" in html


def test_missing_panel_can_project_one_run_without_erasing_global_gaps() -> None:
    from hyodo.dashboard import _render_missing_panel, _scoped_verification_view

    view = {
        "events": {
            "a": {"why": {"run_id": "one"}, "what": {"kind": "tool_call"}},
            "b": {"why": {"run_id": "two"}, "what": {"kind": "tool_call"}},
        },
        "event_order": ["a", "b"],
        "missing": {
            "calls_without_terminal_outcome": ["a", "b"],
            "calls_without_result": ["a", "b"],
            "runs_without_intent": ["one", "two"],
        },
    }
    scoped = _scoped_verification_view(view, "one")
    html = _render_missing_panel({}, view=scoped, scope="Selected run: one")
    assert 'data-missing-bucket="calls_without_terminal_outcome" data-missing-count="1"' in html
    assert "Selected run: one" in html
    assert view["missing"]["calls_without_result"] == ["a", "b"]
    assert "does not prove execution failed" in html


def test_scoped_view_does_not_borrow_other_run_edges() -> None:
    from hyodo.dashboard import _scoped_verification_view

    view = {
        "events": {
            "a": {"why": {"run_id": "one"}},
            "b": {"why": {"run_id": "one"}},
            "c": {"why": {"run_id": "two"}},
        },
        "edges_causal": [{"source": "a", "target": "b"}, {"source": "c", "target": "a"}],
        "edges_evidence": [{"source": "c", "target": "b"}],
        "missing": {},
    }
    scoped = _scoped_verification_view(view, "one")
    assert scoped["edges_causal"] == [{"source": "a", "target": "b"}]
    assert scoped["edges_evidence"] == []
    assert len(view["edges_causal"]) == 2


def test_promise_focus_is_not_a_score_or_exclusive_assignment() -> None:
    from hyodo.dashboard import _render_promise_observation

    html = _render_promise_observation({"events": {}, "missing": {}})
    assert "Primary: 仁 · 孝" in html
    assert "Primary: 眞 · 永" in html
    assert "not scores, measured evidence, or exclusive assignments" in html
    assert "Supporting: 眞 · 善 · 美" in html
    assert html.count("Lenses: 眞 · 善 · 美 · 仁 · 孝 · 永") == 9
    assert "All six lenses inform human judgment" in html
    assert "HUMAN JUDGMENT" in html


def test_event_detail_preserves_output_observation_without_inference() -> None:
    from hyodo.dashboard import _event_detail_payload

    recorded = _event_detail_payload(
        {
            "kind": "tool_result",
            "verification": {
                "how": {
                    "input_digest": "a123",
                    "output_digest": "b123",
                    "output_observation": "empty",
                }
            },
        }
    )
    assert recorded["inputDigest"] == "a123"
    assert recorded["outputObservation"] == "empty"
    historical = _event_detail_payload(
        {"kind": "tool_result", "verification": {"how": {"output_digest": "b123"}}}
    )
    assert historical["outputObservation"] == "UNOBSERVED"
