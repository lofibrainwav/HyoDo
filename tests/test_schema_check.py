"""Contracts for deterministic ``hyodo schema check`` validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()
FIXTURES = Path(__file__).parent / "fixtures" / "schema"


@pytest.mark.parametrize(
    ("schema_name", "payload_name", "exit_code", "ok"),
    [
        ("object.schema.json", "valid-payload.json", 0, True),
        ("object.schema.json", "type-error-payload.json", 1, False),
        ("missing.schema.json", "valid-payload.json", 2, False),
        ("object.schema.json", "empty-payload.json", 2, False),
    ],
)
def test_schema_check_fixture_matrix(schema_name: str, payload_name: str, exit_code: int, ok: bool):
    """Schema validation separates valid, invalid, and unobserved inputs."""
    result = runner.invoke(
        app,
        [
            "schema",
            "check",
            "--schema",
            str(FIXTURES / schema_name),
            "--payload",
            str(FIXTURES / payload_name),
            "--json",
        ],
    )

    assert result.exit_code == exit_code
    payload = json.loads(result.output)
    assert payload["ok"] is ok
    assert payload["exit_code"] == exit_code
    assert isinstance(payload["reasons"], list)


def test_schema_check_reports_a_stable_machine_reason_for_type_error():
    result = runner.invoke(
        app,
        [
            "schema",
            "check",
            "--schema",
            str(FIXTURES / "object.schema.json"),
            "--payload",
            str(FIXTURES / "type-error-payload.json"),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["reasons"] == [
        {
            "code": "validation_error",
            "instance_path": "/event_id",
            "keyword": "type",
            "message": "7 is not of type 'string'",
            "schema_path": "/properties/event_id/type",
        }
    ]


def test_schema_check_rejects_an_invalid_schema_as_unobserved(tmp_path: Path):
    schema = tmp_path / "invalid-schema.json"
    payload = tmp_path / "payload.json"
    schema.write_text('{"type": 4}', encoding="utf-8")
    payload.write_text("{}", encoding="utf-8")

    result = runner.invoke(
        app,
        ["schema", "check", "--schema", str(schema), "--payload", str(payload), "--json"],
    )

    assert result.exit_code == 2
    machine = json.loads(result.output)
    assert machine["ok"] is False
    assert machine["reasons"][0]["code"] == "invalid_schema"
