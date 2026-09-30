"""Consumer contract for a host-supplied Promise observation and its fan-in on the rail.

The contract is deliberately strict: an allowlist parser that minimises what is read, fail-closed
``UNOBSERVED`` for anything unreadable or inconsistent, and a rail that a host can only fill for
Promise, Contract, and Boundaries.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from hyodo.dashboard import _render_promise_observation, render_graph_html
from hyodo.host_promise_observation import (
    HOST_PROMISE_RELATIVE_PATH,
    HOST_PROMISE_SCHEMA,
    load_host_promise_observation,
    parse_host_promise_observation,
)

VIEW: dict[str, Any] = {"events": {}, "missing": {}}


def _stage(state: str, note: str | None = None) -> dict[str, Any]:
    return {"state": state, **({"note": note} if note else {})}


def _projection(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema": HOST_PROMISE_SCHEMA,
        "producer": {"host": "kingdom", "schema_version": "kingdom.promise-observation/v0"},
        "observed_at": "2026-09-30T12:00:00Z",
        "authority": "NONE",
        "source": {"state": "OBSERVED", "problem_count": 0},
        "active_promise": {"resolution": "NONE", "promise_id": None},
        "rail": {
            "promise": _stage("NONE"),
            "contract": _stage("NONE"),
            "boundaries": _stage("NONE"),
        },
        "promises": [],
    }
    base.update(over)
    return base


def _active() -> dict[str, Any]:
    return _projection(
        active_promise={"resolution": "ACTIVE", "promise_id": "P-ACTIVE-1"},
        rail={
            "promise": _stage("OBSERVED"),
            "contract": _stage("OBSERVED"),
            "boundaries": _stage("OBSERVED"),
        },
        promises=[
            {
                "promise_id": "P-ACTIVE-1",
                "status": "OPEN",
                "host_reported_authority": "HOST_VERIFIED_DIRECT_HUMAN",
                "delegation_counts": {
                    "auto": 3,
                    "ask": 1,
                    "must_not": 1,
                    "completion_conditions": 2,
                },
            }
        ],
    )


def _stage_html(html: str, label: str) -> str:
    start = html.index(f'data-promise-stage="{label}"')
    return html[start : html.index("</li>", start)]


# ---- observed absence is not non-observation -------------------------------------------------


def test_observed_source_with_no_promise_is_none_not_unobserved() -> None:
    parsed = parse_host_promise_observation(_projection())
    assert parsed["state"] == "OBSERVED"
    assert parsed["resolution"] == "NONE"
    assert {parsed["rail"][s]["state"] for s in ("promise", "contract", "boundaries")} == {"NONE"}


def test_unobserved_source_with_all_unobserved_stages_is_accepted_as_unobserved() -> None:
    parsed = parse_host_promise_observation(
        _projection(
            source={"state": "UNOBSERVED", "reason": "store missing"},
            active_promise={"resolution": "UNOBSERVED", "promise_id": None},
            rail={k: _stage("UNOBSERVED") for k in ("promise", "contract", "boundaries")},
        )
    )
    assert parsed["state"] == "OBSERVED"  # a valid projection *reporting* UNOBSERVED
    assert parsed["source_state"] == "UNOBSERVED"
    assert parsed["resolution"] == "UNOBSERVED"


@pytest.mark.parametrize("raw", [None, [], "x", 3, {}])
def test_non_object_or_empty_input_is_unobserved_never_none(raw: Any) -> None:
    assert parse_host_promise_observation(raw)["state"] == "UNOBSERVED"


# ---- authority is never accepted -------------------------------------------------------------


@pytest.mark.parametrize("claim", ["GRANTED", "AUTHORITATIVE", None, "none", ""])
def test_a_projection_that_claims_authority_is_rejected(claim: Any) -> None:
    result = parse_host_promise_observation(_projection(authority=claim))
    assert result["state"] == "UNOBSERVED"
    assert "authority NONE" in result["reason"]


# ---- consistency: a producer must not contradict itself --------------------------------------


@pytest.mark.parametrize(
    ("over", "needle"),
    [
        (
            {"source": {"state": "UNOBSERVED"}, "active_promise": {"resolution": "UNOBSERVED"}},
            "source UNOBSERVED",
        ),
        ({"active_promise": {"resolution": "ACTIVE", "promise_id": "P-A-1"}}, "active promise"),
        (
            {
                "rail": {
                    "promise": _stage("OBSERVED"),
                    "contract": _stage("OBSERVED"),
                    "boundaries": _stage("OBSERVED"),
                },
            },
            "no active promise",
        ),
        (
            {
                "active_promise": {"resolution": "AMBIGUOUS"},
                "rail": {
                    "promise": _stage("OBSERVED"),
                    "contract": _stage("NONE"),
                    "boundaries": _stage("NONE"),
                },
            },
            "AMBIGUOUS",
        ),
    ],
)
def test_internally_inconsistent_projections_are_rejected(
    over: dict[str, Any], needle: str
) -> None:
    result = parse_host_promise_observation(_projection(**over))
    assert result["state"] == "UNOBSERVED"
    assert needle in result["reason"]


def test_active_requires_a_promise_id() -> None:
    bad = _active()
    bad["active_promise"]["promise_id"] = None
    assert parse_host_promise_observation(bad)["state"] == "UNOBSERVED"


# ---- privacy minimisation --------------------------------------------------------------------


def test_free_text_and_lists_are_dropped_and_counted_never_returned() -> None:
    raw = _active()
    raw["promises"][0]["commitment"] = "ship the secret plan sk-abcdefghijklmnop1234"
    raw["promises"][0]["responsibility"] = "everything"
    raw["promises"][0]["delegation_counts"]["auto_list"] = ["read", "test"]
    raw["promises"][0]["receipt_id"] = "authority-receipt:sess:prompt"
    raw["extra_top_level"] = {"anything": 1}
    parsed = parse_host_promise_observation(raw)
    assert parsed["state"] == "OBSERVED"
    blob = json.dumps(parsed)
    for leaked in (
        "secret plan",
        "sk-abc",
        "everything",
        "authority-receipt",
        "auto_list",
        "extra_top_level",
    ):
        assert leaked not in blob
    assert parsed["dropped_fields"] == 5
    assert parsed["promises"][0]["delegation_counts"] == {
        "auto": 3,
        "ask": 1,
        "must_not": 1,
        "completion_conditions": 2,
    }


def test_a_host_cannot_supply_stages_it_does_not_own() -> None:
    raw = _active()
    raw["rail"]["evidence"] = _stage("OBSERVED")
    raw["rail"]["readback"] = _stage("OBSERVED")
    raw["rail"]["trust"] = _stage("OBSERVED")
    parsed = parse_host_promise_observation(raw)
    assert set(parsed["rail"]) == {"promise", "contract", "boundaries"}
    assert parsed["dropped_fields"] == 3


def test_note_text_is_sanitised_and_bounded() -> None:
    raw = _active()
    raw["rail"]["promise"]["note"] = "line\x00one\x1b[31m" + "x" * 500
    note = parse_host_promise_observation(raw)["rail"]["promise"]["note"]
    assert "\x00" not in note
    assert "\x1b" not in note
    assert len(note) <= 200


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r["producer"].update(host="<script>alert(1)</script>"),
        lambda r: r["active_promise"].update(promise_id="../../etc/passwd"),
        lambda r: r["promises"][0].update(promise_id="a b"),
        lambda r: r["promises"][0].update(status="DONE"),
        lambda r: r["promises"][0].update(host_reported_authority="GRANTED"),
        lambda r: r["promises"][0].update(host_reported_authority="VERIFIED_DIRECT_HUMAN"),
        lambda r: r["promises"][0].pop("host_reported_authority"),
        lambda r: r["promises"].__setitem__(0, "not an object"),
        lambda r: r.update(promises=[copy.deepcopy(r["promises"][0])] * 201),
    ],
)
def test_malformed_entries_are_rejected_not_repaired(mutate: Any) -> None:
    raw = _active()
    mutate(raw)
    assert parse_host_promise_observation(raw)["state"] == "UNOBSERVED"


# ---- loading: absent file is nothing supplied; a bad file is never an absence ----------------


def test_no_file_means_nothing_was_supplied(tmp_path: Path) -> None:
    assert load_host_promise_observation(tmp_path) is None
    assert load_host_promise_observation(None) is None


def _write(root: Path, text: str) -> Path:
    path = root / HOST_PROMISE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_invalid_json_and_oversized_files_are_unobserved(tmp_path: Path) -> None:
    _write(tmp_path, "{not json")
    assert load_host_promise_observation(tmp_path)["state"] == "UNOBSERVED"  # type: ignore[index]
    _write(tmp_path, " " * (256 * 1024 + 1))
    assert "too large" in load_host_promise_observation(tmp_path)["reason"]  # type: ignore[index]


def test_a_directory_at_the_path_is_unobserved_not_absent(tmp_path: Path) -> None:
    (tmp_path / HOST_PROMISE_RELATIVE_PATH).mkdir(parents=True)
    assert load_host_promise_observation(tmp_path)["state"] == "UNOBSERVED"  # type: ignore[index]


def test_valid_file_loads(tmp_path: Path) -> None:
    _write(tmp_path, json.dumps(_active()))
    assert load_host_promise_observation(tmp_path)["resolution"] == "ACTIVE"  # type: ignore[index]


def test_consumer_never_reads_outside_the_evidence_root(tmp_path: Path) -> None:
    import hyodo.host_promise_observation as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert ".kingdom" not in source
    assert "expanduser" not in source
    assert "home()" not in source


# ---- rail fan-in -----------------------------------------------------------------------------


def test_without_a_host_projection_the_rail_is_byte_identical_to_before() -> None:
    plain = _render_promise_observation(VIEW)
    assert plain == _render_promise_observation(VIEW, None)
    for stage in ("Promise", "Contract", "Boundaries", "Artifact", "Readback"):
        assert f'data-promise-stage="{stage}"><b>{stage}</b> <strong>UNOBSERVED</strong>' in plain
    assert "data-source" not in plain
    assert "host-promise-summary" not in plain


def test_observed_absence_renders_none_for_exactly_the_three_host_stages() -> None:
    html = _render_promise_observation(VIEW, parse_host_promise_observation(_projection()))
    for stage in ("Promise", "Contract", "Boundaries"):
        block = _stage_html(html, stage)
        assert "<strong>NONE</strong>" in block
        assert 'data-source="host:kingdom"' in html
    for stage in ("Artifact", "Readback"):
        assert f'data-promise-stage="{stage}"><b>{stage}</b> <strong>UNOBSERVED</strong>' in html
    assert 'data-promise-stage="Trust"><b>Trust</b> <strong>HUMAN JUDGMENT</strong>' in html


def test_active_renders_observed_with_source_labels_and_no_authority_claim() -> None:
    html = _render_promise_observation(VIEW, parse_host_promise_observation(_active()))
    for stage in ("Promise", "Contract", "Boundaries"):
        assert "<strong>OBSERVED</strong>" in _stage_html(html, stage)
    assert "authority NONE" in html
    assert "not proof of fulfillment or authority" in html
    assert "1 promise record(s)" in html


def test_a_host_cannot_change_what_hyodo_measured_for_other_stages() -> None:
    view = {
        "events": {"e1": {"what": {"kind": "tool_call"}}},
        "missing": {},
    }
    raw = _active()
    raw["rail"]["artifact"] = _stage("OBSERVED")
    html = _render_promise_observation(view, parse_host_promise_observation(raw))
    assert (
        'data-promise-stage="Action"><b>Action</b> <strong>OBSERVED</strong>' in html
    )  # HyoDo's own evidence
    assert (
        'data-promise-stage="Artifact"><b>Artifact</b> <strong>UNOBSERVED</strong>' in html
    )  # not host-fillable
    assert 'data-source="host' not in _stage_html(html, "Action")


def test_a_rejected_projection_renders_unobserved_with_the_reason_never_none() -> None:
    rejected = parse_host_promise_observation(_projection(authority="GRANTED"))
    html = _render_promise_observation(VIEW, rejected)
    for stage in ("Promise", "Contract", "Boundaries"):
        block = _stage_html(html, stage)
        assert "<strong>UNOBSERVED</strong>" in block
        assert "rejected" in block
    assert "This is not the same as no promise." in html
    assert "<strong>NONE</strong>" not in html


def test_producer_and_notes_are_html_escaped() -> None:
    raw = _active()
    raw["rail"]["promise"]["note"] = "<img src=x onerror=alert(1)>"
    html = _render_promise_observation(VIEW, parse_host_promise_observation(raw))
    assert "<img src=x" not in html
    assert "&lt;img" in html


def test_dropped_field_count_is_visible_but_the_dropped_content_is_not() -> None:
    raw = _active()
    raw["promises"][0]["commitment"] = "PRIVATE-COMMITMENT-TEXT"
    html = _render_promise_observation(VIEW, parse_host_promise_observation(raw))
    assert "1 field(s) not read" in html
    assert "PRIVATE-COMMITMENT-TEXT" not in html


def test_graph_page_reads_the_projection_from_the_evidence_root_only(tmp_path: Path) -> None:
    graph: dict[str, Any] = {
        "status": "UNOBSERVED",
        "reason": "no ledger",
        "nodes": [],
        "edges": [],
    }
    without = render_graph_html(graph, root=tmp_path)
    assert "host-promise-summary" not in without
    _write(tmp_path, json.dumps(_projection()))
    with_host = render_graph_html(graph, root=tmp_path)
    assert 'data-host-promise="observed"' in with_host
    _write(tmp_path, "{broken")
    broken = render_graph_html(graph, root=tmp_path)
    assert 'data-host-promise="rejected"' in broken


# ---- published schema stays in step with the parser --------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/host-promise-observation-v0.schema.json"
PIN_PATH = ROOT / "schemas/host-promise-observation-v0.pin.json"


def test_schema_pin_matches_public_schema() -> None:
    import hashlib

    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    assert hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest() == pin["digest"]
    assert pin["schema_version"] == HOST_PROMISE_SCHEMA
    assert json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["$id"] == pin["schema_id"]


def test_schema_constants_and_enums_match_the_parser() -> None:
    from hyodo.host_promise_observation import (
        HOST_AUTHORITY_VALUES,
        PROMISE_STATUSES,
        RESOLUTIONS,
        STAGE_STATES,
        SUPPLIED_STAGES,
    )

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    props = schema["properties"]
    assert props["schema"]["const"] == HOST_PROMISE_SCHEMA
    assert props["authority"]["const"] == "NONE"
    assert set(props["active_promise"]["properties"]["resolution"]["enum"]) == RESOLUTIONS
    assert set(props["rail"]["required"]) == set(SUPPLIED_STAGES)
    assert (
        set(props["rail"]["properties"]["promise"]["properties"]["state"]["enum"]) == STAGE_STATES
    )
    item = props["promises"]["items"]["properties"]
    assert set(item["status"]["enum"]) == PROMISE_STATUSES
    assert set(item["host_reported_authority"]["enum"]) == HOST_AUTHORITY_VALUES
    assert "authority_state" not in item


def test_schema_allows_extras_because_the_consumer_drops_them() -> None:
    """Privacy is enforced by the consumer's allowlist, not by rejecting a richer producer."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is True
    assert "commitment" not in json.dumps(schema["properties"])
    assert "responsibility" not in json.dumps(schema["properties"])


# ---- wording: host-reported authority and HyoDo-owned stages ------------------------------------


def test_authority_values_are_host_reported_never_a_hyodo_finding() -> None:
    from hyodo.host_promise_observation import HOST_AUTHORITY_VALUES

    assert all(v.startswith("HOST_") for v in HOST_AUTHORITY_VALUES)
    parsed = parse_host_promise_observation(_active())
    assert parsed["promises"][0]["host_reported_authority"] == "HOST_VERIFIED_DIRECT_HUMAN"
    assert "authority_state" not in json.dumps(parsed)


def test_old_field_name_is_not_accepted_as_the_authority_field() -> None:
    raw = _active()
    entry = raw["promises"][0]
    entry["authority_state"] = entry.pop("host_reported_authority")
    assert parse_host_promise_observation(raw)["state"] == "UNOBSERVED"


def test_hyodo_owned_stages_say_so_when_a_host_projection_is_shown() -> None:
    html = _render_promise_observation(VIEW, parse_host_promise_observation(_active()))
    for stage in ("Artifact", "Readback"):
        block = _stage_html(html, stage)
        assert "<strong>UNOBSERVED</strong>" in block
        assert (
            "HyoDo-owned stage; HyoDo has not observed it yet (a host cannot supply it)." in block
        )
    assert "HyoDo-owned" not in _stage_html(html, "Promise")
    assert "HyoDo-owned" not in _stage_html(html, "Trust")


def test_hyodo_owned_note_names_hyodo_evidence_when_it_did_observe() -> None:
    view = {"events": {"e1": {"what": {"kind": "tool_call"}}}, "missing": {}}
    from html import unescape

    html = _render_promise_observation(view, parse_host_promise_observation(_active()))
    block = unescape(_stage_html(html, "Action"))
    assert "<strong>OBSERVED</strong>" in block
    assert "HyoDo-owned stage, from HyoDo's own evidence." in block


def test_without_a_host_projection_the_owned_stage_text_is_unchanged() -> None:
    assert "HyoDo-owned" not in _render_promise_observation(VIEW)
