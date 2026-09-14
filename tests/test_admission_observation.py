from pathlib import Path

from hyodo.admission_observation import (
    ADMISSION_OBSERVATION_SCHEMA_VERSION,
    append_admission_observation,
    validate_admission_observation,
)


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
