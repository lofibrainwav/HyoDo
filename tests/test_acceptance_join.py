"""Frozen acceptance membership, pinned evidence and canonical UI projection."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from hyodo.dashboard import _render_intent_comparisons
from hyodo.intent_review import acceptance_join, load_acceptance_join


def contract():
    return {
        "contract_id": "test",
        "revision": 1,
        "origin": "HUMAN_RECONSTITUTED",
        "criteria_count": 7,
        "required_criteria": [{"id": f"E{i:02}", "text": "required"} for i in range(1, 8)],
        "governing_invariants": [{"id": f"E{i:02}", "text": "invariant"} for i in range(8, 13)],
    }


def check(tmp_path, value, name="evidence.json"):
    p = tmp_path / name
    p.write_text(json.dumps({"actual": value}))
    return {
        "operator": "eq",
        "expected": True,
        "receipts": [
            {
                "path": str(p),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "pointer": "/actual",
            }
        ],
    }


def test_missing_members_are_not_dropped():
    result = acceptance_join(contract(), {})
    assert len(result["criteria"]) == 7
    assert result["status"] == "HOLD"
    assert all(row["state"] == "UNOBSERVED" for row in result["criteria"])


@pytest.mark.parametrize(
    ("value", "state"), [(True, "PASS"), (False, "FAIL"), (None, "UNOBSERVED")]
)
def test_comparison_states(tmp_path, value, state):
    result = acceptance_join(contract(), {"E01": [check(tmp_path, value)]})
    assert result["criteria"][0]["state"] == state
    assert result["status"] == ("NOT_COMPLETE" if state == "FAIL" else "HOLD")


def test_conflicting_receipts_are_not_last_writer_wins(tmp_path):
    a = check(tmp_path, True, "a.json")
    b = check(tmp_path, False, "b.json")
    a["receipts"] += b["receipts"]
    assert acceptance_join(contract(), {"E01": [a]})["status"] == "CONFLICTING"


def test_tampered_evidence_cannot_pass(tmp_path):
    c = check(tmp_path, True)
    Path(c["receipts"][0]["path"]).write_text('{"actual":false}')
    assert acceptance_join(contract(), {"E01": [c]})["criteria"][0]["state"] == "UNOBSERVED"


def test_live_mismatch_regression(tmp_path):
    p = Path(__file__).parent / "fixtures/acceptance-join-live-mismatch.json"
    binding = {
        "operator": "eq",
        "expected": "MATCH",
        "receipts": [
            {
                "path": str(p),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "pointer": "/provenance/validity",
            }
        ],
    }
    result = acceptance_join(contract(), {"E06": [binding]})
    assert result["criteria"][5]["state"] == "FAIL"
    assert result["status"] == "NOT_COMPLETE"


def test_frozen_contract_read_model_and_ui(tmp_path):
    c = contract()
    before = copy.deepcopy(c)
    p = tmp_path / "contract.json"
    p.write_text(json.dumps(c))
    (tmp_path / ".hyodo").mkdir()
    manifest = {"path": str(p), "digest": hashlib.sha256(p.read_bytes()).hexdigest()}
    (tmp_path / ".hyodo/acceptance-contract.json").write_text(json.dumps(manifest))
    result = load_acceptance_join(tmp_path)
    html = _render_intent_comparisons({"acceptance_join": result})
    assert result["status"] == "HOLD"
    for row in result["criteria"]:
        assert f"{row['id']}: {row['state']}" in html
    assert c == before
    p.write_text("{}")
    assert load_acceptance_join(tmp_path)["status"] == "CONFLICTING"


def ready_bindings(tmp_path):
    b = {f"E{i:02}": [check(tmp_path, True)] for i in range(1, 13)}
    for name in ("verification_observed", "identity_correlation", "visible_readback"):
        b[name] = [check(tmp_path, True)]
    execution = {
        "candidate_sha": "a" * 40,
        "source_sha": "a" * 40,
        "runtime_sha": "a" * 40,
        "served_sha": "a" * 40,
        "dirty": False,
        "observed_at": "2026-09-20T10:01:00Z",
        "restarted_at": "2026-09-20T10:00:00Z",
        "required_checks": ["required"],
        "checks": [
            {
                "name": "required",
                "head_sha": "a" * 40,
                "status": "completed",
                "conclusion": "success",
            }
        ],
        "contract_id": "test",
        "revision": 1,
        "visible_criteria": {f"E{i:02}": "PASS" for i in range(1, 8)},
    }
    return b, execution


def bind_execution(tmp_path, bindings, execution):
    p = tmp_path / "execution.json"
    p.write_text(json.dumps(execution))
    bindings["execution_receipt"] = {
        "path": str(p),
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
    }


def test_all_required_and_guards_needed_for_complete(tmp_path):
    b, e = ready_bindings(tmp_path)
    assert acceptance_join(contract(), b)["status"] == "HOLD"
    bind_execution(tmp_path, b, e)
    assert acceptance_join(contract(), b)["status"] == "COMPLETE"
    del b["E07"]
    e["visible_criteria"]["E07"] = "UNOBSERVED"
    bind_execution(tmp_path, b, e)
    assert acceptance_join(contract(), b)["status"] == "HOLD"


@pytest.mark.parametrize(
    ("case", "state"),
    [
        ("wrong_sha", "NOT_COMPLETE"),
        ("dirty", "HOLD"),
        ("old_readback", "HOLD"),
        ("skipped_ci", "HOLD"),
        ("wrong_head_ci", "HOLD"),
        ("failed_ci", "NOT_COMPLETE"),
        ("conflicting_ci", "CONFLICTING"),
        ("wrong_visible", "NOT_COMPLETE"),
        ("missing_invariant", "HOLD"),
        ("invariant_violation", "NOT_COMPLETE"),
    ],
)
def test_completion_guards(tmp_path, case, state):
    b, e = ready_bindings(tmp_path)
    if case == "wrong_sha":
        e["served_sha"] = "b" * 40
    elif case == "dirty":
        e["dirty"] = True
    elif case == "old_readback":
        e["observed_at"] = e["restarted_at"]
    elif case == "skipped_ci":
        e["checks"][0]["conclusion"] = "skipped"
    elif case == "wrong_head_ci":
        e["checks"][0]["head_sha"] = "b" * 40
    elif case == "failed_ci":
        e["checks"][0]["conclusion"] = "failure"
    elif case == "conflicting_ci":
        e["checks"].append({**e["checks"][0], "conclusion": "failure"})
    elif case == "wrong_visible":
        e["visible_criteria"]["E01"] = "FAIL"
    elif case == "missing_invariant":
        del b["E08"]
    elif case == "invariant_violation":
        b["E08"] = [check(tmp_path, False, "violation.json")]
    bind_execution(tmp_path, b, e)
    assert acceptance_join(contract(), b)["status"] == state
