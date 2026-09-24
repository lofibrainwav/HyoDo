"""`hyodo.lens-evidence/v1` carries evidence for one lens and nothing a judge
would own: no score, value, weight, aggregate, decision, or authority."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema.validators import validator_for

from hyodo.virtues import CANONICAL_VIRTUE_KEYS

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / "schemas/lens-evidence-v1.schema.json"
PIN_PATH = ROOT / "schemas/lens-evidence-v1.pin.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

RECEIPT = {
    "schema_version": "hyodo.lens-evidence/v1",
    "lens": "truth",
    "subject": {"exact_artifact_sha": "a" * 40},
    "state": "PARTIAL",
    "coverage": {
        "proxies_declared": ["tests", "typing", "static_checks"],
        "proxies_observed": ["tests", "typing"],
    },
    "provenance": {"hyodo_version": "4.21.7"},
    "evidence_refs": [{"kind": "gate", "ref": "tests", "digest": "sha256:" + "b" * 64}],
    "residuals": ["static_checks_unobserved"],
    "observed_at": "2026-09-24T00:00:00Z",
    "authority": "UNOBSERVED",
}


def _errors(payload: dict) -> list[str]:
    validator = validator_for(SCHEMA)(SCHEMA)
    return [error.message for error in validator.iter_errors(payload)]


def test_schema_pin_matches_public_schema() -> None:
    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    assert hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest() == pin["digest"]
    assert pin["schema_version"] == SCHEMA["properties"]["schema_version"]["const"]


def test_evidence_receipt_is_valid() -> None:
    assert _errors(RECEIPT) == []


def test_lenses_are_exactly_the_canonical_six() -> None:
    assert tuple(SCHEMA["properties"]["lens"]["enum"]) == CANONICAL_VIRTUE_KEYS


def test_partial_is_a_first_class_state() -> None:
    assert SCHEMA["properties"]["state"]["enum"] == ["OBSERVED", "PARTIAL", "UNOBSERVED"]


@pytest.mark.parametrize(
    "field", ["score", "value", "weight", "aggregate", "decision", "verdict", "rationale"]
)
def test_judgment_fields_are_rejected(field: str) -> None:
    payload = {**copy.deepcopy(RECEIPT), field: 0.9}
    assert _errors(payload), field


def test_receipt_never_claims_authority() -> None:
    payload = {**copy.deepcopy(RECEIPT), "authority": "ALLOW"}
    assert _errors(payload)
