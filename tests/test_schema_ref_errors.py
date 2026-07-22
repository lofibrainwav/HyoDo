"""Unresolvable ``$ref`` targets must observe as exit 2, not crash with a traceback.

jsonschema only raises ``SchemaError`` while *building* a validator. A
reference that fails to resolve (an unretrievable relative ``$ref``) is
raised later, while *iterating* validation errors
(``validator.iter_errors``), as ``jsonschema.exceptions._WrappedReferencingError``
-- which is-a ``referencing.exceptions.Unresolvable`` by design (jsonschema's
own deprecation notice for the old ``RefResolutionError`` tells callers to
catch ``referencing.exceptions.Unresolvable`` directly). Before the fix, that
exception was outside every try/except in ``hyodo.schema`` and propagated as
a raw Python traceback instead of HyoDo's 0/1/2 exit contract.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.schema import validate_schema_payload

runner = CliRunner()

_UNRESOLVABLE_REF_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {"event_id": {"$ref": "does-not-exist.schema.json#/definitions/EventId"}},
    }
)

_VALID_PAYLOAD = json.dumps({"event_id": "abc"})
_INVALID_PAYLOAD = json.dumps({"event_id": 7})


def _write(path: Path, name: str, content: str) -> Path:
    target = path / name
    target.write_text(content, encoding="utf-8")
    return target


def test_unresolvable_ref_is_exit_2_not_a_traceback(tmp_path: Path):
    """Direct library call: a schema with an unresolvable $ref observes as unobserved."""
    schema = _write(tmp_path, "bad-ref.schema.json", _UNRESOLVABLE_REF_SCHEMA)
    payload = _write(tmp_path, "payload.json", _VALID_PAYLOAD)

    ok, exit_code, reasons = validate_schema_payload(schema, payload)

    assert ok is False
    assert exit_code == 2
    assert reasons == [
        {
            "code": "invalid_schema",
            "message": ("Unresolvable: does-not-exist.schema.json#/definitions/EventId"),
        }
    ]


def test_cli_schema_check_reports_unresolvable_ref_as_json_not_a_traceback(tmp_path: Path):
    """CLI ``--json`` consumers must receive JSON, never a raw Python traceback."""
    schema = _write(tmp_path, "bad-ref.schema.json", _UNRESOLVABLE_REF_SCHEMA)
    payload = _write(tmp_path, "payload.json", _VALID_PAYLOAD)

    result = runner.invoke(
        app,
        ["schema", "check", "--schema", str(schema), "--payload", str(payload), "--json"],
    )

    assert result.exit_code == 2
    # A clean CLI exit only ever raises typer's SystemExit(2); anything else
    # (e.g. the unresolvable-ref exception itself) means it leaked out raw.
    assert isinstance(result.exception, SystemExit)

    machine = json.loads(result.output)
    assert machine["ok"] is False
    assert machine["exit_code"] == 2
    assert machine["reasons"][0]["code"] == "invalid_schema"


def test_ordinary_invalid_payload_still_exits_1_after_the_ref_fix(tmp_path: Path):
    """The ref-resolution fix must not weaken the existing invalid-payload gate."""
    schema = _write(
        tmp_path,
        "object.schema.json",
        json.dumps(
            {
                "type": "object",
                "properties": {"event_id": {"type": "string"}},
            }
        ),
    )
    payload = _write(tmp_path, "payload.json", _INVALID_PAYLOAD)

    ok, exit_code, reasons = validate_schema_payload(schema, payload)

    assert ok is False
    assert exit_code == 1
    assert reasons[0]["code"] == "validation_error"


def test_ordinary_valid_payload_still_exits_0_after_the_ref_fix(tmp_path: Path):
    """The ref-resolution fix must not disturb the success path."""
    schema = _write(
        tmp_path,
        "object.schema.json",
        json.dumps(
            {
                "type": "object",
                "properties": {"event_id": {"type": "string"}},
            }
        ),
    )
    payload = _write(tmp_path, "payload.json", _VALID_PAYLOAD)

    ok, exit_code, reasons = validate_schema_payload(schema, payload)

    assert ok is True
    assert exit_code == 0
    assert reasons == []
