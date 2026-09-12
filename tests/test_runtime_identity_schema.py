"""Cross-repo contract tests for the canonical runtime identity payload."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from hyodo.identity import build_runtime_identity

SCHEMA = Path(__file__).parents[1] / "schemas" / "runtime-identity-v1.schema.json"


def test_generated_identity_matches_v1_schema(tmp_path: Path) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    identity = build_runtime_identity(tmp_path)

    errors = sorted(Draft202012Validator(schema).iter_errors(identity), key=str)

    assert errors == []


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update({"unexpected": True}),
        lambda payload: payload["provenance"].update({"validity": "GREEN"}),
        lambda payload: payload["ledger"].update({"events": -1}),
    ],
)
def test_runtime_identity_schema_rejects_protocol_drift(tmp_path: Path, mutator) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    payload = copy.deepcopy(build_runtime_identity(tmp_path))
    mutator(payload)

    assert list(Draft202012Validator(schema).iter_errors(payload))
