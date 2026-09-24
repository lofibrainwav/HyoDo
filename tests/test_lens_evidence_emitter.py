"""The lens-evidence emitter: deterministic, schema-valid, and never more
certain than its envelope. The envelope comes from the real
`collect_dashboard_evidence` path on a real git checkout."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from jsonschema.validators import validator_for

from hyodo.cli.main import GateResult, GateStatus, collect_dashboard_evidence
from hyodo.lens_evidence import emit_all_lens_evidence, emit_lens_evidence
from hyodo.virtues import CANONICAL_VIRTUE_KEYS

SCHEMA = json.loads(
    (Path(__file__).parents[1] / "schemas/lens-evidence-v1.schema.json").read_text(encoding="utf-8")
)
JUDGMENT_KEYS = {"score", "value", "weight", "aggregate", "decision", "verdict", "rationale"}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _checkout(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    (root / ".gitignore").write_text(".hyodo/\n", encoding="utf-8")
    (root / "app.py").write_text("x = 1\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "init")
    return root, _git(root, "rev-parse", "HEAD")


def _envelope(root: Path, *, tests: GateResult) -> dict:
    ok = GateResult(GateStatus.PASS, "ok")
    safety = {"risk_score": 0, "source": "git diff HEAD", "findings": []}
    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=ok),
        patch("hyodo.cli.main.run_ruff_check", return_value=ok),
        patch("hyodo.cli.main.run_pytest_check", return_value=tests),
        patch("hyodo.cli.main.run_sbom_check", return_value=ok),
        patch("hyodo.cli.main.run_safety_scan", return_value=safety),
    ):
        return collect_dashboard_evidence(root)


def _valid(receipt: dict) -> None:
    errors = [e.message for e in validator_for(SCHEMA)(SCHEMA).iter_errors(receipt)]
    assert errors == []
    assert not JUDGMENT_KEYS & set(receipt)


def test_all_attributed_gates_ran_is_observed(tmp_path: Path) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    assert evidence["provenance"]["target_commit"] == sha
    assert evidence["provenance"]["target_dirty"] is False

    receipt = emit_lens_evidence(evidence, "truth", sha)
    _valid(receipt)
    assert receipt["state"] == "OBSERVED"
    assert receipt["coverage"] == {
        "proxies_declared": ["tests", "typecheck"],
        "proxies_observed": ["tests", "typecheck"],
    }
    assert [ref["ref"] for ref in receipt["evidence_refs"]] == ["tests", "typecheck"]


def test_a_failing_gate_is_observed_not_judged(tmp_path: Path) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.FAIL, "2 failed"))
    receipt = emit_lens_evidence(evidence, "truth", sha)
    _valid(receipt)
    assert receipt["state"] == "OBSERVED"
    assert "tests" in receipt["coverage"]["proxies_observed"]


def test_a_gate_that_did_not_run_makes_the_lens_partial(tmp_path: Path) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.SKIP, "no tests/ directory"))
    receipt = emit_lens_evidence(evidence, "truth", sha)
    _valid(receipt)
    assert receipt["state"] == "PARTIAL"
    assert receipt["coverage"]["proxies_observed"] == ["typecheck"]
    assert "gate_unobserved:tests:SKIP" in receipt["residuals"]


@pytest.mark.parametrize("status", ["SKIP", "UNSUPPORTED", "UNOBSERVED_TOOL_UNAVAILABLE"])
def test_no_attributed_gate_ran_is_unobserved(tmp_path: Path, status: str) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    evidence["gates"]["lint_format"]["status"] = status
    receipt = emit_lens_evidence(evidence, "beauty", sha)
    _valid(receipt)
    assert receipt["state"] == "UNOBSERVED"
    assert receipt["evidence_refs"] == []


def test_a_lens_without_attributed_gates_is_unobserved(tmp_path: Path) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    receipt = emit_lens_evidence(evidence, "goodness", sha)
    _valid(receipt)
    assert receipt["state"] == "UNOBSERVED"
    assert "no_attributed_gate" in receipt["residuals"]


def test_evidence_measured_at_another_commit_is_stale_not_observed(tmp_path: Path) -> None:
    root, old_sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    (root / "app.py").write_text("x = 2\n", encoding="utf-8")
    _git(root, "commit", "-q", "-am", "change")
    new_sha = _git(root, "rev-parse", "HEAD")
    assert new_sha != old_sha

    receipt = emit_lens_evidence(evidence, "truth", new_sha)
    _valid(receipt)
    assert receipt["state"] == "UNOBSERVED"
    assert "stale_provenance" in receipt["residuals"]
    assert receipt["coverage"]["proxies_observed"] == []
    assert receipt["evidence_refs"] == []


def test_evidence_from_a_dirty_tree_is_not_bound_to_the_commit(tmp_path: Path) -> None:
    root, sha = _checkout(tmp_path)
    (root / "app.py").write_text("x = 3\n", encoding="utf-8")
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    assert evidence["provenance"]["target_dirty"] is True
    receipt = emit_lens_evidence(evidence, "truth", sha)
    _valid(receipt)
    assert receipt["state"] == "UNOBSERVED"
    assert "target_tree_not_clean" in receipt["residuals"]


@pytest.mark.parametrize("provenance", [None, {}, {"target_commit": None}])
def test_missing_provenance_is_unobserved(tmp_path: Path, provenance: dict | None) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    if provenance is None:
        del evidence["provenance"]
    else:
        evidence["provenance"] = provenance
    receipt = emit_lens_evidence(evidence, "truth", sha)
    _valid(receipt)
    assert receipt["state"] == "UNOBSERVED"
    assert "provenance_unobserved" in receipt["residuals"]


def test_emission_is_deterministic_and_covers_the_canonical_six(tmp_path: Path) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    first = emit_all_lens_evidence(copy.deepcopy(evidence), sha)
    second = emit_all_lens_evidence(copy.deepcopy(evidence), sha)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert tuple(receipt["lens"] for receipt in first) == CANONICAL_VIRTUE_KEYS
    for receipt in first:
        _valid(receipt)


def test_served_envelope_yields_the_same_receipts_as_in_process(tmp_path: Path) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.SKIP, "no tests/ directory"))
    served = json.loads(json.dumps(evidence, default=str))
    assert emit_all_lens_evidence(served, sha) == emit_all_lens_evidence(evidence, sha)


@pytest.mark.parametrize(
    ("status", "residual"),
    [
        (["PASS"], "gate_unobserved:tests:malformed_status"),
        ({"value": "PASS"}, "gate_unobserved:tests:malformed_status"),
        (None, "gate_unobserved:tests:malformed_status"),
        (1, "gate_unobserved:tests:malformed_status"),
        ("", "gate_unobserved:tests:malformed_status"),
        ("pass", "gate_unobserved:tests:pass"),
    ],
)
def test_malformed_status_is_unobserved_not_raised(tmp_path: Path, status, residual: str) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    evidence["gates"]["tests"]["status"] = status
    receipt = emit_lens_evidence(evidence, "truth", sha)
    _valid(receipt)
    assert receipt["state"] == "PARTIAL"
    assert receipt["coverage"]["proxies_observed"] == ["typecheck"]
    assert residual in receipt["residuals"]


def test_unserializable_row_is_unobserved_not_raised(tmp_path: Path) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    evidence["gates"]["tests"]["extra"] = {1, 2}
    receipt = emit_lens_evidence(evidence, "truth", sha)
    _valid(receipt)
    assert receipt["state"] == "PARTIAL"
    assert "gate_unobserved:tests:unserializable_row" in receipt["residuals"]
    assert [ref["ref"] for ref in receipt["evidence_refs"]] == ["typecheck"]


@pytest.mark.parametrize("name", [7, "", None, ("a", "b")])
def test_malformed_gate_name_counts_as_unobserved(tmp_path: Path, name) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    evidence["gates"][name] = {"status": "PASS", "message": "ok", "pillar": "truth"}
    receipt = emit_lens_evidence(evidence, "truth", sha)
    _valid(receipt)
    # Two named gates ran, a third attributed gate cannot be cited: not complete.
    assert receipt["state"] == "PARTIAL"
    assert receipt["coverage"]["proxies_declared"] == ["tests", "typecheck"]
    assert "gate_unobserved:malformed_name" in receipt["residuals"]


def test_only_a_malformed_name_is_unobserved(tmp_path: Path) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    evidence["gates"] = {7: {"status": "PASS", "pillar": "goodness"}}
    receipt = emit_lens_evidence(evidence, "goodness", sha)
    _valid(receipt)
    assert receipt["state"] == "UNOBSERVED"
    assert "no_attributed_gate" not in receipt["residuals"]


@pytest.mark.parametrize("evidence", [None, [], "envelope", 3, {"gates": [], "provenance": 1}])
def test_malformed_envelope_is_unobserved_not_raised(evidence) -> None:
    receipt = emit_lens_evidence(evidence, "truth", "a" * 40)
    _valid(receipt)
    assert receipt["state"] == "UNOBSERVED"
    assert "provenance_unobserved" in receipt["residuals"]


def test_unserializable_provenance_is_still_a_valid_receipt(tmp_path: Path) -> None:
    root, sha = _checkout(tmp_path)
    evidence = _envelope(root, tests=GateResult(GateStatus.PASS, "ok"))
    evidence["provenance"]["extra"] = object()
    receipt = emit_lens_evidence(evidence, "truth", sha)
    _valid(receipt)
    assert receipt["provenance"]["measured_by"] == "UNOBSERVED"


@pytest.mark.parametrize(
    ("lens", "sha", "message"),
    [
        ("serenity", "a" * 40, "unknown lens"),
        (["truth"], "a" * 40, "unknown lens"),
        ("truth", "abc123", "subject_sha"),
        ("truth", 12345, "subject_sha"),
    ],
)
def test_caller_errors_are_refused_not_emitted(lens: str, sha: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        emit_lens_evidence({}, lens, sha)
