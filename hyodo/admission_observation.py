"""Bounded observations of an external executor's policy admission decision."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ADMISSION_OBSERVATION_SCHEMA_VERSION = "hyodo.admission-observation/v1"
ADMISSION_OBSERVATIONS_RELATIVE_PATH = Path(".hyodo") / "admission-observations.jsonl"
DECISIONS = frozenset({"AUTO_RUN", "ASK_COMMANDER", "BLOCK", "UNKNOWN"})


def _non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_admission_observation(raw: Any) -> tuple[bool, list[str], dict[str, Any] | None]:
    if not isinstance(raw, Mapping):
        return False, ["not_an_object"], None

    reasons: list[str] = []
    for field in ("schema", "observation_id", "decision_id", "run_id", "source", "ts"):
        if field == "schema":
            if raw.get(field) != ADMISSION_OBSERVATION_SCHEMA_VERSION:
                reasons.append("unsupported_schema")
        elif not _non_empty(raw.get(field)):
            reasons.append(f"invalid_field:{field}")

    if raw.get("decision") not in DECISIONS:
        reasons.append("invalid_field:decision")
    for field in ("observed", "admitted", "execution_attempted", "execution_observed"):
        if not isinstance(raw.get(field), bool):
            reasons.append(f"invalid_field:{field}")
    if raw.get("execution_attempted") is True or raw.get("execution_observed") is True:
        reasons.append("admission_cannot_claim_execution")
    score = raw.get("s_score")
    if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float))):
        reasons.append("invalid_field:s_score")

    if reasons:
        return False, reasons, None

    normalized = {
        "schema": ADMISSION_OBSERVATION_SCHEMA_VERSION,
        "observation_id": raw["observation_id"].strip(),
        "decision_id": raw["decision_id"].strip(),
        "run_id": raw["run_id"].strip(),
        "decision": raw["decision"],
        "s_score": score,
        "observed": raw["observed"],
        "admitted": raw["admitted"],
        "execution_attempted": raw["execution_attempted"],
        "execution_observed": raw["execution_observed"],
        "source": raw["source"].strip(),
        "ts": raw["ts"].strip(),
        "observation_identity": raw.get("observation_identity"),
    }
    return True, [], normalized


def append_admission_observation(root: Path, raw: Any) -> dict[str, Any]:
    ok, reasons, normalized = validate_admission_observation(raw)
    if not ok or normalized is None:
        raise ValueError(";".join(reasons) or "invalid_admission_observation")

    path = root / ADMISSION_OBSERVATIONS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n")
    os.chmod(path, 0o600)
    return normalized


__all__ = [
    "ADMISSION_OBSERVATIONS_RELATIVE_PATH",
    "ADMISSION_OBSERVATION_SCHEMA_VERSION",
    "DECISIONS",
    "append_admission_observation",
    "validate_admission_observation",
]
