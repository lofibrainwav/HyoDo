import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.admission_observation import (
    ADMISSION_OBSERVATION_SCHEMA_VERSION,
    append_admission_observation,
    validate_admission_observation,
)
from hyodo.cli.main import app


def payload(**overrides):
    value = {
        "schema": ADMISSION_OBSERVATION_SCHEMA_VERSION,
        "observation_id": "observation-1",
        "decision_id": "decision-1",
        "run_id": "run-1",
        "decision": "BLOCK",
        "s_score": 7.894,
        "observed": True,
        "admitted": False,
        "execution_attempted": False,
        "execution_observed": False,
        "source": "kingdom.agent-loop.eros-gate",
        "ts": "2026-09-13T21:00:00Z",
        "observation_identity": {"kind": "receipt_id", "value": "opaque-1"},
    }
    value.update(overrides)
    return value


def test_validates_and_appends_admission_observation(tmp_path: Path):
    ok, reasons, normalized = validate_admission_observation(payload())
    assert ok is True
    assert reasons == []
    assert normalized["decision"] == "BLOCK"

    saved = append_admission_observation(tmp_path, payload())
    ledger = tmp_path / ".hyodo" / "admission-observations.jsonl"
    assert saved["observation_id"] == "observation-1"
    assert ledger.read_text(encoding="utf-8").count("observation-1") == 1


def test_rejects_execution_claim_on_admission_only():
    ok, reasons, _ = validate_admission_observation(
        payload(admitted=True, execution_attempted=True, execution_observed=True)
    )
    assert ok is False
    assert "admission_cannot_claim_execution" in reasons


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"decision": []}, "invalid_field:decision"),
        ({"decision": {}}, "invalid_field:decision"),
        ({"s_score": float("nan")}, "invalid_field:s_score"),
        ({"s_score": float("inf")}, "invalid_field:s_score"),
        ({"s_score": -float("inf")}, "invalid_field:s_score"),
        ({"execution_attempted": True}, "admission_cannot_claim_execution"),
        ({"execution_observed": True}, "admission_cannot_claim_execution"),
        ({"observation_identity": {"nested": float("nan")}}, "invalid_json_observation"),
    ],
)
def test_cli_rejects_bad_observation_without_writing(tmp_path: Path, override, reason):
    result = CliRunner().invoke(
        app,
        ["admission", "record", "--stdin", "--root", str(tmp_path), "--json"],
        input=json.dumps(payload(**override)),
    )
    assert result.exit_code == 2, result.output
    receipt = json.loads(result.output)
    assert receipt["ok"] is False
    assert any(reason in item for item in receipt["reasons"])
    assert not (tmp_path / ".hyodo").exists()


def test_invalid_observation_preserves_existing_ledger(tmp_path: Path):
    append_admission_observation(tmp_path, payload())
    ledger = tmp_path / ".hyodo" / "admission-observations.jsonl"
    before = ledger.read_bytes()
    with pytest.raises(ValueError, match="invalid_json_observation"):
        append_admission_observation(tmp_path, payload(observation_identity={"bad": object()}))
    assert ledger.read_bytes() == before


@pytest.mark.parametrize("decision", ["AUTO_RUN", "ASK_COMMANDER", "BLOCK", "UNKNOWN"])
def test_cli_records_observation_without_execution_or_authority(tmp_path: Path, decision):
    incoming = payload(decision=decision, authority={"approved": True})
    result = CliRunner().invoke(
        app,
        ["admission", "record", "--stdin", "--root", str(tmp_path), "--json"],
        input=json.dumps(incoming),
    )
    assert result.exit_code == 0, result.output
    ledger = tmp_path / ".hyodo" / "admission-observations.jsonl"
    recorded = json.loads(ledger.read_text())
    assert recorded["decision"] == decision
    assert recorded["execution_attempted"] is False
    assert recorded["execution_observed"] is False
    assert "authority" not in recorded
    assert list((tmp_path / ".hyodo").iterdir()) == [ledger]
