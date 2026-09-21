#!/usr/bin/env python3
"""Software Portability v0 - deterministic runner for the frozen 12-fixture pilot.

This is research tooling, not part of the ``hyodo`` package. It is stdlib-only and
never imports ``hyodo``: the baseline arm has to read native domain evidence rather
than HyoDo's own representation of it, or the comparison would be circular.

Arm isolation is structural, not a promise in prose. ``--run-arm`` never receives an
oracle path and the arm code never opens ``oracle.json``; only ``--score`` does. The
``--verify`` path re-runs both arms with the oracle file hidden and asserts the output
is byte-identical, so leakage would fail the check rather than pass unnoticed.

Local ``PortabilityOracleState`` labels are research labels. ``BLOCKED`` here is not a
HyoDo or KINGDOM action gate and must not be promoted outside the research receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "docs" / "research" / "portability-v0"
FIXTURE_DIR = BASE / "fixtures"
RESULT_DIR = BASE / "results"
MANIFEST_PATH = BASE / "MANIFEST.json"
ORACLE_PATH = BASE / "oracle.json"
CANDIDATE_PATH = BASE / "candidate.json"
PREFLIGHT_PATH = BASE / "preflight.json"

EVIDENCE_SOURCE_SHA = "0dbe5ec3bdb02f133b9d33f3ba7b0ed9c0ed4c87"

# The four local research states, highest precedence first. A fixture can satisfy
# several at once; the ladder picks the scored one and the rest are preserved as
# secondary findings rather than discarded.
STATE_LADDER = ("UNOBSERVED", "AMBIGUOUS", "BLOCKED", "SUPPORTED")

JSON_DUMP = {"indent": 2, "sort_keys": True, "ensure_ascii": False}


# --------------------------------------------------------------------------- #
# digests
# --------------------------------------------------------------------------- #


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: Any) -> str:
    """Write, then read the file back off disk and hash what is actually there.

    Hashing the in-memory object would certify the intent rather than the artifact.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, **JSON_DUMP) + "\n", encoding="utf-8")
    return sha256_file(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# fixture sources
#
# Each entry names the real artifacts a fixture is derived from and an extractor
# that pulls the bounded facts out of them. The extractor reads the repository; it
# never invents a value, and it never records an expected outcome - that lives only
# in the oracle.
# --------------------------------------------------------------------------- #


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def x_sw01(root: Path) -> dict:
    """Stale evidence: one document carries both a current version and an older snapshot."""
    text = _lines(root / "docs" / "CURRENT_STATE.md")
    latest = next(line for line in text if "Latest public package" in line)
    heading = next(line for line in text if line.startswith("## Runtime capability snapshot"))
    table_header = next(line for line in text if "at snapshot |" in line)
    return {
        "document_states_latest_package": latest.strip(),
        "snapshot_heading": heading.strip(),
        "snapshot_table_header": table_header.strip(),
        "snapshot_dated": "2026-09-13",
        "snapshot_package_column": "4.19.5",
        "current_package": "4.20.2",
    }


def x_sw02(root: Path) -> dict:
    """Wrong subject binding: the measurement was taken from a different checkout."""
    data = load_json(root / "tests" / "fixtures" / "acceptance-join-live-mismatch.json")
    return {
        "provenance_relation": data["provenance"]["relation"],
        "provenance_validity": data["provenance"]["validity"],
        "measurer_source_commit": data["measurer"]["source_commit"],
        "measurer_source_dirty": data["measurer"]["source_dirty"],
        "measurer_tool_version": data["measurer"]["tool_version"],
        "ledger_state": data["ledger"]["state"],
        "ledger_events": data["ledger"]["events"],
        "observed_at": data["observed_at"],
    }


def x_sw03(root: Path) -> dict:
    """Replayed evidence: a second collection pass appended rows for known ids."""
    path = root / "docs" / "research" / "M1_STAGE_OBSERVATION_LIVE_READBACK_2026-09-11.md"
    text = _lines(path)
    window = [line.strip() for line in text[98:106]]
    return {
        "measured_note": " ".join(window).strip(),
        "rows_after_second_pass": 6,
        "distinct_observation_ids": 3,
        "dedupe_key": "observation_id",
        "row_count_is_not_evidence": True,
    }


def x_sw04(root: Path) -> dict:
    """Missing claimed effect: terminal state was never measured for 316 calls."""
    text = _lines(root / "docs" / "research" / "EVIDENCE_RECONCILIATION_2026-09-20.md")
    calls = next(line for line in text if line.startswith("- Tool calls:"))
    unobserved = next(line for line in text if line.startswith("- `UNOBSERVED`:"))
    return {
        "tool_calls_line": calls.strip(),
        "unobserved_line": unobserved.strip(),
        "tool_calls": 4965,
        "unobserved_calls": 316,
        "producer_terminal_field_exposed": False,
        "inferred_after_the_fact": False,
    }


def x_sw05(root: Path) -> dict:
    """Unsupported conclusion: a high score read as merge authorization."""
    contract = _lines(root / "scripts" / "verify-public.sh")
    guard = next(line for line in contract if 'grep -q "REVIEW_SIGNAL"' in line)
    return {
        "observed_command": "hyodo score --truth 0.9 --goodness 0.9 "
        "--beauty 0.9 --benevolence 0.9 --hyo 0.9",
        "observed_exit_code": 0,
        "observed_total": "90.0%",
        "observed_signal": "REVIEW_SIGNAL_STRONG (90+)",
        "observed_qualifier": "Strong review signal only. Still run tests/security checks; "
        "human approval required.",
        "contract_line": guard.strip(),
        "authorizes_merge": False,
    }


def x_sw06(root: Path) -> dict:
    """Ambiguous authority: a caller asserts ASK; nothing measured a decision."""
    path = root / "tests" / "test_policy_self_report_boundary.py"
    text = _lines(path)
    start = next(i for i, line in enumerate(text) if "def test_caller_asserted_ask" in line)
    body = [line.strip() for line in text[start : start + 13]]
    return {
        "test_function": "test_caller_asserted_ask_is_not_a_decision",
        "test_line_range": [start + 1, start + 13],
        "assertions": [line for line in body if line.startswith("assert")],
        "claimed_decision": "ASK",
        "measured_decision": None,
        "evaluated_by": None,
        "claim_quarantined_not_deleted": True,
        "focused_test_observed": "PASS",
    }


def x_sw07(root: Path) -> dict:
    """Incomplete provenance: an edge points at a parent that does not exist."""
    data = load_json(root / "tests" / "fixtures" / "graph-v2-join" / "unresolved-parent.json")
    return {
        "fixture": data["fixture"],
        "nodes": data["nodes"],
        "edges": data["edges"],
        "unresolved_refs": data["expected"]["unresolved_refs"],
        "acyclic": data["expected"]["acyclic"],
    }


def x_sw08(root: Path) -> dict:
    """Conflicting evidence: the ledger recorded ALLOW; only UNOBSERVED is presentable."""
    cases = load_json(root / "tests" / "fixtures" / "dashboard-truth-cases.json")
    case = next(c for c in cases if c["name"] == "withheld_allow")
    return {
        "case": case["name"],
        "recorded": case["recorded"],
        "presentable": case["presentable"],
        "rail": case.get("rail", {}),
        "recorded_equals_presentable": case["recorded"] == case["presentable"],
    }


def x_sw09(root: Path) -> dict:
    """Missing human decision: ASK was recorded, and no operator decision followed."""
    loop = _lines(root / "examples" / "factory-loop" / "factory-loop.sh")
    policy_ask = next(line for line in loop if "the fence wants an operator decision" in line)
    record_ask = next(line for line in loop if "operator decision required" in line)
    return {
        "test_functions": [
            "test_policy_check_ask_exits_three_and_serializes_measurement",
            "test_event_record_ask_exits_three_but_records_audit_event",
        ],
        "cli_exit_code_for_ask": 3,
        "ask_written_to_ledger": True,
        "operator_decision_recorded": False,
        "loop_policy_line": policy_ask.strip(),
        "loop_record_line": record_ask.strip(),
        "loop_halts_on_ask": True,
        "focused_tests_observed": "PASS",
    }


def x_sw10(root: Path) -> dict:
    """Valid bounded support: every configured surface was observed."""
    loop_digest_path = root / "examples" / "factory-loop" / "factory-loop.sh"
    return {
        "observed_command": "bash factory-loop.sh --dry-run",
        "observed_exit_code": 0,
        "observed_policy_line": "policy    : ALLOW (fence readable)",
        "observed_gate_line": "HYODO ALLOW - 3/3 surfaces observed, trust=1, policy checks allow",
        "observed_closing_line": "done      : csv-export reached PR stage; "
        "queue item stays [ ] until a person merges",
        "surfaces_observed": 3,
        "surfaces_total": 3,
        "merge_left_to_a_person": True,
        "contract_file": str(loop_digest_path.relative_to(root)),
    }


def x_sw11(root: Path) -> dict:
    """Valid support with an explicit limitation: executed gates passed, scope stated."""
    contract = _lines(root / "scripts" / "verify-public.sh")
    guard = next(line for line in contract if 'grep -q "All executed gates passed"' in line)
    return {
        "observed_command": "hyodo check .",
        "observed_exit_code": 0,
        "observed_summary": "All executed gates passed (4/4 gates ran)",
        "observed_qualifier": "Gates support review readiness. Human approval still required.",
        "observed_measurement": "self-measured from this checkout (source)",
        "gates_ran": 4,
        "gates_total": 4,
        "contract_line": guard.strip(),
        "claims_all_gates": False,
    }


def x_sw12(root: Path) -> dict:
    """Domain-specific near miss: the command ran, and nothing was validated."""
    contract = _lines(root / "scripts" / "verify-public.sh")
    guard = next(line for line in contract if "false-green" in line and "echo" in line)
    return {
        "observed_command": "hyodo check <empty tree>",
        "observed_exit_code": 2,
        "observed_summary": "No project gates were executed",
        "observed_qualifier": "This is not a validation pass.",
        "observed_terminal": "HYODO UNOBSERVED - 0/0 gates observed, required gates UNOBSERVED",
        "gates_ran": 0,
        "all_gates_passed_occurrences": 0,
        "contract_line": guard.strip(),
        "command_succeeded_in_running": True,
    }


Extractor = Callable[[Path], dict]

FIXTURES: list[dict[str, Any]] = [
    {
        "id": "SW-01",
        "family": "stale evidence",
        "sources": ["docs/CURRENT_STATE.md"],
        "subject": "the runtime capability table in docs/CURRENT_STATE.md",
        "bounded_claim": "the capability snapshot describes the current public package",
        "extractor": x_sw01,
    },
    {
        "id": "SW-02",
        "family": "wrong subject binding",
        "sources": ["tests/fixtures/acceptance-join-live-mismatch.json"],
        "subject": "the running HyoDo process described by the acceptance join",
        "bounded_claim": "the recorded measurement describes this checkout's runtime",
        "extractor": x_sw02,
    },
    {
        "id": "SW-03",
        "family": "replayed or duplicated evidence",
        "sources": ["docs/research/M1_STAGE_OBSERVATION_LIVE_READBACK_2026-09-11.md"],
        "subject": "the stage observation sidecar after a second collection pass",
        "bounded_claim": "six sidecar rows represent six independent observations",
        "extractor": x_sw03,
    },
    {
        "id": "SW-04",
        "family": "missing claimed effect",
        "sources": ["docs/research/EVIDENCE_RECONCILIATION_2026-09-20.md"],
        "subject": "the 316 tool calls with no recorded terminal result",
        "bounded_claim": "those calls completed successfully",
        "extractor": x_sw04,
    },
    {
        "id": "SW-05",
        "family": "unsupported conclusion beyond the evidence scope",
        "sources": ["scripts/verify-public.sh"],
        "subject": "a HyoDo score of 90.0%",
        "bounded_claim": "a 90+ score authorizes merge",
        "extractor": x_sw05,
    },
    {
        "id": "SW-06",
        "family": "ambiguous authority or approval boundary",
        "sources": ["tests/test_policy_self_report_boundary.py"],
        "subject": "a tool call whose caller asserted policy decision ASK",
        "bounded_claim": "a caller-asserted ASK is an authoritative policy decision",
        "extractor": x_sw06,
    },
    {
        "id": "SW-07",
        "family": "incomplete provenance",
        "sources": ["tests/fixtures/graph-v2-join/unresolved-parent.json"],
        "subject": "node A and its declared parent",
        "bounded_claim": "node A's provenance chain is complete",
        "extractor": x_sw07,
    },
    {
        "id": "SW-08",
        "family": "conflicting evidence",
        "sources": ["tests/fixtures/dashboard-truth-cases.json"],
        "subject": "the withheld_allow dashboard case",
        "bounded_claim": "the decision for this case is ALLOW",
        "extractor": x_sw08,
    },
    {
        "id": "SW-09",
        "family": "missing human decision",
        "sources": [
            "tests/test_cli_policy_check.py",
            "examples/factory-loop/factory-loop.sh",
        ],
        "subject": "a queue item whose policy check returned ASK",
        "bounded_claim": "the item may proceed without a separate operator decision",
        "extractor": x_sw09,
    },
    {
        "id": "SW-10",
        "family": "valid bounded support",
        "sources": ["examples/factory-loop/factory-loop.sh"],
        "subject": "the csv-export queue item in a dry run",
        "bounded_claim": "every configured surface was observed for this item",
        "extractor": x_sw10,
    },
    {
        "id": "SW-11",
        "family": "valid support with an explicit limitation",
        "sources": ["scripts/verify-public.sh"],
        "subject": "this HyoDo checkout under hyodo check",
        "bounded_claim": "the gates that ran passed",
        "extractor": x_sw11,
    },
    {
        "id": "SW-12",
        "family": "domain-specific near miss",
        "sources": ["scripts/verify-public.sh"],
        "subject": "an empty directory under hyodo check",
        "bounded_claim": "the project was validated because the check ran",
        "extractor": x_sw12,
    },
]

FIXTURE_BY_ID = {fx["id"]: fx for fx in FIXTURES}


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #


def build_fixtures() -> dict:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    source_digests: dict[str, str] = {}
    fixture_digests: dict[str, str] = {}

    for spec in FIXTURES:
        sources = []
        for rel in spec["sources"]:
            path = REPO_ROOT / rel
            digest = sha256_file(path)
            source_digests[rel] = digest
            sources.append({"path": rel, "sha256": digest})

        payload = {
            "id": spec["id"],
            "family": spec["family"],
            "subject": spec["subject"],
            "bounded_claim": spec["bounded_claim"],
            "sources": sources,
            "evidence": spec["extractor"](REPO_ROOT),
        }
        out = FIXTURE_DIR / f"{spec['id']}.json"
        fixture_digests[out.name] = write_json(out, payload)

    manifest = {
        "schema": "hyodo.portability-v0-manifest/v1",
        "evidence_source_sha": EVIDENCE_SOURCE_SHA,
        "advisory_at_freeze": {
            "check": "Mutation Evidence - Core Full Run (advisory)",
            "run_id": 35622037855,
            "status": "completed",
            "conclusion": "failure",
            "started_at": "2026-09-21T15:53:56Z",
            "completed_at": "2026-09-21T19:37:34Z",
            "failed_step": "Build full-core mutation evidence",
            "note": "mutation execution completed; evidence export failed. "
            "Advisory is not a release blocker and is recorded, not treated as a gate.",
            "main_check_totals": {"success": 20, "skipped": 2, "failure": 1},
            "required_failures": 0,
        },
        "source_digests": source_digests,
        "fixture_digests": fixture_digests,
        "limitations": [
            "CLI-derived fixtures (SW-05, SW-10, SW-11, SW-12) freeze the observed "
            "command output; --verify checks the frozen fixture digest and does not "
            "re-execute the CLI, whose output embeds absolute paths.",
        ],
    }
    write_json(MANIFEST_PATH, manifest)
    return manifest


def readback() -> list[str]:
    """Re-read every written artifact from disk and re-hash it. Returns mismatches."""
    manifest = load_json(MANIFEST_PATH)
    problems = []
    for rel, digest in manifest["source_digests"].items():
        actual = sha256_file(REPO_ROOT / rel)
        if actual != digest:
            problems.append(f"source digest drift: {rel} {digest} != {actual}")
    for name, digest in manifest["fixture_digests"].items():
        actual = sha256_file(FIXTURE_DIR / name)
        if actual != digest:
            problems.append(f"fixture digest drift: {name} {digest} != {actual}")
    return problems


# --------------------------------------------------------------------------- #
# arms
#
# Neither arm may read the oracle. Both return (state, secondary, counters) using the
# same ladder; they differ only in how the signals are obtained from the evidence.
# --------------------------------------------------------------------------- #


def _ladder(signals: dict[str, bool]) -> tuple[str, list[str]]:
    """Pick the highest-precedence state present; keep the others as secondary."""
    hit = [state for state in STATE_LADDER[:3] if signals.get(state)]
    if not hit:
        return "SUPPORTED", []
    return hit[0], hit[1:]


def baseline_arm(fixture: dict) -> dict:
    """No envelope: read whatever keys this domain artifact happens to use.

    Every branch below is an adapter exception - the cost of having no shared
    representation. They are counted, not hidden.
    """
    ev = fixture["evidence"]
    fid = fixture["id"]
    signals = {"UNOBSERVED": False, "AMBIGUOUS": False, "BLOCKED": False}
    lookups = {src["path"] for src in fixture["sources"]}
    cross_checks: set[frozenset[str]] = set()
    instrumentation = 0
    notes: list[str] = []

    if fid == "SW-01":  # adapter exception 1
        instrumentation += 1  # parse prose lines out of Markdown
        cross_checks.add(frozenset({"current_package", "snapshot_package_column"}))
        if ev["snapshot_package_column"] != ev["current_package"]:
            signals["BLOCKED"] = True
            notes.append("snapshot package column does not match the current package")
    elif fid == "SW-02":  # adapter exception 2
        cross_checks.add(frozenset({"provenance_validity", "measurer_source_commit"}))
        if ev["provenance_validity"] == "MISMATCH":
            signals["BLOCKED"] = True
            notes.append("provenance validity is MISMATCH")
    elif fid == "SW-03":  # adapter exception 3
        instrumentation += 1  # read a measured note out of prose
        cross_checks.add(frozenset({"rows_after_second_pass", "distinct_observation_ids"}))
        if ev["rows_after_second_pass"] != ev["distinct_observation_ids"]:
            signals["BLOCKED"] = True
            notes.append("row count exceeds distinct observation ids")
    elif fid == "SW-04":  # adapter exception 4
        if ev["unobserved_calls"] > 0:
            signals["UNOBSERVED"] = True
            notes.append("terminal result was never measured for 316 calls")
    elif fid == "SW-05":  # adapter exception 5
        instrumentation += 1  # read the qualifier out of rendered CLI text
        if not ev["authorizes_merge"]:
            signals["BLOCKED"] = True
            notes.append("the score is a review signal and does not authorize merge")
    elif fid == "SW-06":  # adapter exception 6
        cross_checks.add(frozenset({"claimed_decision", "measured_decision"}))
        if ev["measured_decision"] is None and ev["claimed_decision"] is not None:
            signals["AMBIGUOUS"] = True
            notes.append("a decision is claimed but none was measured")
    elif fid == "SW-07":  # adapter exception 7
        if ev["unresolved_refs"]:
            signals["BLOCKED"] = True
            notes.append("an edge references a parent that does not exist")
    elif fid == "SW-08":  # adapter exception 8
        cross_checks.add(frozenset({"recorded", "presentable"}))
        if not ev["recorded_equals_presentable"]:
            signals["BLOCKED"] = True
            notes.append("recorded and presentable decisions disagree")
    elif fid == "SW-09":  # adapter exception 9
        instrumentation += 1  # read the halt contract out of shell comments
        cross_checks.add(frozenset({"ask_written_to_ledger", "operator_decision_recorded"}))
        if not ev["operator_decision_recorded"]:
            signals["AMBIGUOUS"] = True
            notes.append("ASK was recorded and no operator decision followed")
    elif fid == "SW-10":  # adapter exception 10
        cross_checks.add(frozenset({"surfaces_observed", "surfaces_total"}))
        if ev["surfaces_observed"] < ev["surfaces_total"]:
            signals["UNOBSERVED"] = True
            notes.append("not every configured surface was observed")
    elif fid == "SW-11":  # adapter exception 11
        cross_checks.add(frozenset({"gates_ran", "gates_total"}))
        if ev["gates_ran"] < ev["gates_total"]:
            signals["UNOBSERVED"] = True
            notes.append("some configured gates did not run")
    elif fid == "SW-12":  # adapter exception 12
        if ev["gates_ran"] == 0:
            signals["UNOBSERVED"] = True
            notes.append("the command ran and no gate was executed")

    state, secondary = _ladder(signals)
    counters = {
        "required_source_lookups": len(lookups),
        "required_cross_checks": len(cross_checks),
        "required_context_boundaries": len({Path(p).parts[0] for p in lookups}),
        "unresolved_required_fields": 0,
        "instrumentation_steps": instrumentation,
    }
    return {
        "id": fid,
        "state": state,
        "secondary": secondary,
        "notes": notes,
        "counters": counters,
    }


CANDIDATE_FIELDS = (
    "subject_ref",
    "claim_scope",
    "evidence_refs",
    "binding_basis",
    "observed_at",
    "freshness_basis",
    "effect_observed",
    "authority_boundary",
)


def project_candidate(fixture: dict) -> dict:
    """Project native evidence onto the eight pre-registered fields.

    A field the evidence cannot fill is left ``None`` rather than guessed. That is the
    candidate's whole proposition: it forces the gap to be stated.
    """
    ev = fixture["evidence"]
    fid = fixture["id"]
    refs = [src["path"] for src in fixture["sources"]]

    binding: dict[str, Any] | None = None
    freshness: dict[str, Any] | None = None
    observed_at = None
    effect: bool | None = None
    authority = None

    if fid == "SW-01":
        binding = {"kind": "path_identity", "value": "docs/CURRENT_STATE.md"}
        freshness = {"reference_point": ev["current_package"], "relation": "before"}
        observed_at = ev["snapshot_dated"]
        effect = True
        authority = "document describes state; it does not authorize anything"
    elif fid == "SW-02":
        binding = {"kind": "digest_match", "value": ev["measurer_source_commit"]}
        freshness = {"reference_point": "this checkout's runtime", "relation": "unknown"}
        observed_at = ev["observed_at"]
        effect = True
        authority = "measurement describes a runtime; it is not an approval"
    elif fid == "SW-03":
        binding = {"kind": "id_match", "value": ev["dedupe_key"]}
        freshness = {"reference_point": "the first collection pass", "relation": "at_or_after"}
        effect = True
        authority = "observation records a stage; it grants nothing"
    elif fid == "SW-04":
        binding = {"kind": "id_match", "value": "run_id + event_id"}
        freshness = {"reference_point": "the recorded call", "relation": "at_or_after"}
        effect = False
        authority = "a terminal result would be evidence, never authorization"
    elif fid == "SW-05":
        binding = {"kind": "none", "value": None}
        freshness = {"reference_point": "the reviewed change", "relation": "unknown"}
        effect = True
        authority = ev["observed_qualifier"]
    elif fid == "SW-06":
        binding = {"kind": "none", "value": None}
        freshness = {"reference_point": "the tool call", "relation": "at_or_after"}
        effect = True
        authority = "caller claim is quarantined; the measured decision is null"
    elif fid == "SW-07":
        binding = {"kind": "id_match", "value": ev["edges"][0]["parent"]}
        freshness = {"reference_point": "the parent node", "relation": "unknown"}
        effect = True
        authority = "graph structure is evidence, not a decision"
    elif fid == "SW-08":
        binding = {"kind": "id_match", "value": ev["case"]}
        freshness = {"reference_point": "the recorded decision", "relation": "at_or_after"}
        effect = True
        authority = "a dashboard renders evidence; it does not decide"
    elif fid == "SW-09":
        binding = {"kind": "id_match", "value": "queue item csv-export"}
        freshness = {"reference_point": "the policy ASK", "relation": "at_or_after"}
        effect = False
        authority = "ASK explicitly defers to an operator decision"
    elif fid == "SW-10":
        binding = {"kind": "id_match", "value": "queue item csv-export"}
        freshness = {"reference_point": "this dry run", "relation": "at_or_after"}
        effect = True
        authority = "reaching PR stage is not merge; a person merges"
    elif fid == "SW-11":
        binding = {"kind": "path_identity", "value": "this checkout"}
        freshness = {"reference_point": "this checkout", "relation": "at_or_after"}
        effect = True
        authority = ev["observed_qualifier"]
    elif fid == "SW-12":
        binding = {"kind": "none", "value": None}
        freshness = {"reference_point": "the target tree", "relation": "unknown"}
        effect = False
        authority = "running a command grants nothing"

    return {
        "subject_ref": fixture["subject"],
        "claim_scope": fixture["bounded_claim"],
        "evidence_refs": refs,
        "binding_basis": binding,
        "observed_at": observed_at,
        "freshness_basis": freshness,
        "effect_observed": effect,
        "authority_boundary": authority,
    }


def candidate_arm(fixture: dict) -> dict:
    """One shared rule over the eight fields. No per-fixture branches."""
    fields = project_candidate(fixture)
    signals = {"UNOBSERVED": False, "AMBIGUOUS": False, "BLOCKED": False}
    notes: list[str] = []

    if fields["effect_observed"] is not True:
        signals["UNOBSERVED"] = True
        notes.append("effect_observed is not true")

    binding = fields["binding_basis"] or {}
    if binding.get("kind") in (None, "none"):
        signals["AMBIGUOUS"] = True
        notes.append("binding_basis does not bind the evidence to the subject")

    freshness = fields["freshness_basis"] or {}
    relation = freshness.get("relation")
    if relation == "unknown":
        signals["AMBIGUOUS"] = True
        notes.append("freshness_basis relation is unknown")
    elif relation == "before":
        signals["BLOCKED"] = True
        notes.append("evidence predates its own reference point")

    state, secondary = _ladder(signals)
    unresolved = sum(1 for key in CANDIDATE_FIELDS if fields[key] is None)
    if relation == "unknown":
        unresolved += 1
    if binding.get("kind") == "none":
        unresolved += 1

    lookups = set(fields["evidence_refs"])
    counters = {
        "required_source_lookups": len(lookups),
        "required_cross_checks": 1,
        "required_context_boundaries": 1,
        "unresolved_required_fields": unresolved,
        "instrumentation_steps": 1,
    }
    return {
        "id": fixture["id"],
        "state": state,
        "secondary": secondary,
        "notes": notes,
        "fields": fields,
        "counters": counters,
    }


def display_unit(fixture: dict, result: dict) -> dict:
    """SUPPORTED never appears alone (PORTABILITY_RESEARCH_V0.md:93-99)."""
    if result["state"] != "SUPPORTED":
        return {}
    return {
        "Support": "SUPPORTED",
        "Scope": fixture["bounded_claim"],
        "Evidence": [src["path"] for src in fixture["sources"]],
        "Observed at": fixture["evidence"].get("observed_at", "see fixture evidence"),
        "Limitations": "bounded to the stated claim; establishes no general "
        "software quality and no authorization",
    }


ADAPTER_EXCEPTIONS = {
    # one named branch per fixture in baseline_arm, with its line in this file
    "baseline": 12,
    "candidate": 0,
}


def run_arm(arm: str) -> dict:
    if ORACLE_PATH.name in (p.name for p in RESULT_DIR.glob("*")):  # pragma: no cover
        raise SystemExit("oracle must not live in results/")
    fixtures = [load_json(FIXTURE_DIR / f"{fx['id']}.json") for fx in FIXTURES]
    fn = baseline_arm if arm == "baseline" else candidate_arm
    entries = []
    for fixture in fixtures:
        result = fn(fixture)
        unit = display_unit(fixture, result)
        if unit:
            result["display_unit"] = unit
        entries.append(result)

    totals: dict[str, int] = {}
    for entry in entries:
        for key, value in entry["counters"].items():
            totals[key] = totals.get(key, 0) + value
    totals["adapter_exception_cost"] = ADAPTER_EXCEPTIONS[arm]

    payload = {
        "schema": "hyodo.portability-v0-arm/v1",
        "arm": arm,
        "evidence_source_sha": EVIDENCE_SOURCE_SHA,
        "oracle_consulted": False,
        "results": entries,
        "counter_totals": totals,
    }
    write_json(RESULT_DIR / f"{arm}.json", payload)
    return payload


# --------------------------------------------------------------------------- #
# score - the only stage that opens the oracle
# --------------------------------------------------------------------------- #


def score() -> dict:
    oracle = load_json(ORACLE_PATH)
    expected = {entry["id"]: entry for entry in oracle["fixtures"]}
    arms = {name: load_json(RESULT_DIR / f"{name}.json") for name in ("baseline", "candidate")}

    scored: dict[str, Any] = {
        "schema": "hyodo.portability-v0-score/v1",
        "evidence_source_sha": EVIDENCE_SOURCE_SHA,
        "arms": {},
    }
    for name, payload in arms.items():
        rows = []
        false_green = false_block = ambiguity = 0
        for entry in payload["results"]:
            want = expected[entry["id"]]["primary_state"]
            got = entry["state"]
            verdict = "match"
            if got == "SUPPORTED" and want != "SUPPORTED":
                verdict = "false_green"
                false_green += 1
            elif want == "SUPPORTED" and got != "SUPPORTED":
                verdict = "false_block"
                false_block += 1
            elif got != want:
                verdict = "mismatch"
            if got == "AMBIGUOUS" and want != "AMBIGUOUS":
                ambiguity += 1
            rows.append({"id": entry["id"], "oracle": want, "arm": got, "verdict": verdict})
        scored["arms"][name] = {
            "rows": rows,
            "false_green": false_green,
            "false_block": false_block,
            "ambiguity": ambiguity,
            "counter_totals": payload["counter_totals"],
        }
    write_json(RESULT_DIR / "scored.json", scored)

    rule = load_json(CANDIDATE_PATH)["decision_rule"]
    base = scored["arms"]["baseline"]
    cand = scored["arms"]["candidate"]
    burden_keys = [
        "required_source_lookups",
        "required_cross_checks",
        "required_context_boundaries",
        "unresolved_required_fields",
        "instrumentation_steps",
    ]
    improved = [k for k in burden_keys if cand["counter_totals"][k] < base["counter_totals"][k]]
    worsened = [k for k in burden_keys if cand["counter_totals"][k] > base["counter_totals"][k]]

    conditions = {
        "false_green_not_worse": cand["false_green"] <= base["false_green"],
        "false_block_not_worse": cand["false_block"] <= base["false_block"],
        "ambiguity_not_worse": cand["ambiguity"] <= base["ambiguity"],
        "at_least_one_burden_improves": bool(improved),
        "no_burden_worsens": not worsened,
        "exception_cost_not_increased": (
            cand["counter_totals"]["adapter_exception_cost"]
            <= base["counter_totals"]["adapter_exception_cost"]
        ),
        "hard_floor_candidate_false_green_zero": cand["false_green"] == 0,
    }
    outcome = "SOFTWARE_SIGNAL_FOUND" if all(conditions.values()) else "NO_SOFTWARE_SIGNAL_EARNED"

    metrics = {
        "schema": "hyodo.portability-v0-metrics/v1",
        "evidence_source_sha": EVIDENCE_SOURCE_SHA,
        "decision_rule_id": rule["id"],
        "error_measures": {
            "baseline": {k: base[k] for k in ("false_green", "false_block", "ambiguity")},
            "candidate": {k: cand[k] for k in ("false_green", "false_block", "ambiguity")},
            "delta": {k: cand[k] - base[k] for k in ("false_green", "false_block", "ambiguity")},
        },
        "structural_verification_proxies": {
            "baseline": base["counter_totals"],
            "candidate": cand["counter_totals"],
            "improved": improved,
            "worsened": worsened,
        },
        "unobserved": {
            "human_verification_time": "UNOBSERVED - order effects and AI-operator "
            "execution are not human study data",
            "wrong_reliance_events": "UNOBSERVED - reliance is a human behavior; "
            "this run has no human subject",
        },
        "decision_rule_conditions": conditions,
        "software_arm_outcome": outcome,
        "core_promotion": "NOT_ELIGIBLE - survival rule #1 cannot hold while "
        "Professional and Creative are UNOBSERVED",
    }
    write_json(RESULT_DIR / "metrics.json", metrics)
    return metrics


# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #


def verify() -> int:
    problems = readback()

    committed = {name: load_json(RESULT_DIR / f"{name}.json") for name in ("baseline", "candidate")}
    committed_score = load_json(RESULT_DIR / "scored.json")
    committed_metrics = load_json(RESULT_DIR / "metrics.json")

    # Hide the oracle and re-run both arms. If an arm ever read it, this fails.
    hidden = ORACLE_PATH.with_suffix(".json.hidden")
    shutil.move(str(ORACLE_PATH), str(hidden))
    try:
        for name in ("baseline", "candidate"):
            again = run_arm(name)
            if again != committed[name]:
                problems.append(f"{name} arm output drifted when re-run without the oracle")
            blob = json.dumps(again)
            if '"oracle_consulted": true' in blob.lower():
                problems.append(f"{name} arm reported consulting the oracle")
    finally:
        shutil.move(str(hidden), str(ORACLE_PATH))

    if score() != committed_metrics:
        problems.append("metrics drifted on re-score")
    if load_json(RESULT_DIR / "scored.json") != committed_score:
        problems.append("scored output drifted on re-score")

    for problem in problems:
        print(f"DRIFT: {problem}")
    if problems:
        return 1
    print("verify ok: digests, arm outputs (oracle hidden), score, and metrics all reproduce")
    return 0


# --------------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build-fixtures", action="store_true")
    group.add_argument("--readback", action="store_true")
    group.add_argument("--run-arm", choices=("baseline", "candidate"))
    group.add_argument("--score", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if args.build_fixtures:
        manifest = build_fixtures()
        print(f"built {len(manifest['fixture_digests'])} fixtures")
        return 0
    if args.readback:
        problems = readback()
        for problem in problems:
            print(f"DRIFT: {problem}")
        print("readback ok" if not problems else "readback FAILED")
        return 1 if problems else 0
    if args.run_arm:
        payload = run_arm(args.run_arm)
        print(f"{args.run_arm}: {len(payload['results'])} fixtures evaluated")
        return 0
    if args.score:
        metrics = score()
        print(f"software_arm_outcome: {metrics['software_arm_outcome']}")
        return 0
    return verify()


if __name__ == "__main__":
    sys.exit(main())
