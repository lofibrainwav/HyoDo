"""Deterministic JSON Schema validation for local agent payloads."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from jsonschema import ValidationError
from jsonschema.exceptions import SchemaError
from jsonschema.validators import validator_for

JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]


def _pointer(parts: Iterable[object]) -> str:
    """Render JSON Pointer paths with the RFC 6901 escaping rules."""
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in parts)


def _load_json(path: Path, *, kind: str) -> tuple[JsonValue | None, dict[str, str] | None]:
    """Load one JSON input, returning a structured observation error when needed."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, {"code": f"{kind}_missing", "message": f"{kind} file does not exist"}
    except OSError as exc:
        return None, {"code": f"{kind}_unreadable", "message": str(exc)}

    if not text.strip():
        return None, {"code": f"{kind}_empty", "message": f"{kind} file is empty"}
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, {"code": f"{kind}_not_json", "message": exc.msg}


def validate_schema_payload(
    schema_path: Path, payload_path: Path
) -> tuple[bool, int, list[dict[str, str]]]:
    """Validate a payload and preserve HyoDo's 0/1/2 exit contract.

    Exit 0 means valid, 1 means the observed payload violates the observed
    schema, and 2 means one of those inputs could not be observed or trusted.
    """
    schema, reason = _load_json(schema_path, kind="schema")
    if reason is not None:
        return False, 2, [reason]
    payload, reason = _load_json(payload_path, kind="payload")
    if reason is not None:
        return False, 2, [reason]

    if not isinstance(schema, (bool, dict)):
        return (
            False,
            2,
            [{"code": "invalid_schema", "message": "schema must be an object or boolean"}],
        )

    try:
        validator_class = validator_for(schema)
        if isinstance(schema, dict):
            validator_class.check_schema(schema)
        validator = validator_class(schema)
    except SchemaError as exc:
        return False, 2, [{"code": "invalid_schema", "message": exc.message}]

    errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            tuple(str(part) for part in error.absolute_schema_path),
            error.validator or "",
        ),
    )
    if not errors:
        return True, 0, []

    return False, 1, [_validation_reason(error) for error in errors]


def _validation_reason(error: ValidationError) -> dict[str, str]:
    """Serialize one validation error without exposing implementation objects."""
    return {
        "code": "validation_error",
        "instance_path": _pointer(error.absolute_path),
        "schema_path": _pointer(error.absolute_schema_path),
        "keyword": str(error.validator) if error.validator else "unknown",
        "message": error.message,
    }
