"""Read-only final evidence check, never an execution or approval authority.

A trusted caller must supply the plan digest and fresh run id OUT OF BAND.
Check observations must come from trusted runners, not builder assertions.
Same-account writable files do not provide authenticated execution attestation.
This verifies exact bytes, required coverage and freshness, not tax/legal truth.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import time
from pathlib import Path
from typing import Any, cast

from hyodo.workspace_io import open_workspace_file, open_workspace_root

REQUIRED = {
    "code": frozenset({"tests", "security", "execution"}),
    "accounting": frozenset({"source", "recalculation", "reconciliation", "review"}),
    "document": frozenset({"source", "completeness", "review"}),
}
MAX_BYTES = 2_000_000


class Hold(ValueError):
    """Missing or inconsistent evidence cannot release a deliverable."""


def _require(ok, reason):
    if not ok:
        raise Hold(reason)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(raw: bytes) -> dict[str, Any]:
    def pairs(items):
        """Reject duplicate JSON keys rather than accepting the last value."""
        result = {}
        for key, value in items:
            _require(key not in result, "duplicate_json_key")
            result[key] = value
        return result

    def invalid(_):
        """Reject nonfinite constants at the parsing boundary."""
        raise Hold("nonfinite_json")

    parsed = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    _require(type(parsed) is dict, "json_object_required")
    return cast(dict[str, Any], parsed)


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _relative(value):
    _require(isinstance(value, str) and value and "\\" not in value, "invalid_path")
    path = Path(value)
    _require(
        not path.is_absolute() and all(p not in (".", "..") for p in value.split("/")),
        "path_escape",
    )
    _require(str(path) == value, "noncanonical_path")
    return path


def _read(root, relative):
    relative = _relative(relative)
    _require(
        all(hasattr(os, name) for name in ("O_NONBLOCK", "O_NOFOLLOW", "O_DIRECTORY")),
        "descriptor_primitives_unavailable",
    )
    _, root_fd = open_workspace_root(root)
    try:
        fd = open_workspace_file(root, relative, os.O_RDONLY | os.O_NONBLOCK, root_fd=root_fd)
    finally:
        os.close(root_fd)
    with os.fdopen(fd, "rb") as stream:
        _require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "regular_file_required")
        raw = stream.read(MAX_BYTES + 1)
    _require(len(raw) <= MAX_BYTES, "file_too_large")
    return raw


def inspect_handoff(
    root: Path,
    plan_path: Path,
    expected_plan_sha256: str,
    expected_run_id: str,
    now: float | None = None,
) -> dict:
    """Return VERIFIED_EVIDENCE or HOLD; caller owns persistence and last readback.

    VERIFIED_EVIDENCE is NOT permission to send/file and is only as trustworthy
    as the out-of-band plan and runner observations. No commands are executed.
    """
    result: dict[str, Any] = {
        "schema": "hyodo.handoff-verdict/v1",
        "status": "HOLD",
        "external_action_allowed": False,
        "checks_observed": 0,
        "trust_boundary": "trusted_caller_plan_pin_and_runner_observations",
        "same_account_execution_attestation": False,
    }
    try:
        root = Path(root).absolute()
        _require(_digest(expected_plan_sha256), "trusted_plan_pin_required")
        _require(
            isinstance(expected_run_id, str) and bool(expected_run_id), "fresh_run_id_required"
        )
        current = time.time() if now is None else now
        _require(_number(current), "invalid_clock")
        plan_relative = str(Path(plan_path).absolute().relative_to(root))
        plan_raw = _read(root, plan_relative)
        _require(_sha(plan_raw) == expected_plan_sha256, "plan_pin_mismatch")
        plan = _json(plan_raw)
        _require(
            type(plan) is dict
            and plan.get("schema") == "hyodo.handoff-plan/v1"
            and set(plan)
            == {
                "schema",
                "kind",
                "run_id",
                "created_at",
                "max_age_seconds",
                "producer",
                "artifacts",
                "checks",
            },
            "plan_schema",
        )
        producer = plan.get("producer")
        _require(
            isinstance(producer, str) and producer.strip() == producer and bool(producer),
            "canonical_producer_required",
        )
        kind = cast(str, plan.get("kind"))
        _require(isinstance(kind, str) and kind in REQUIRED, "unsupported_work_kind")
        _require(plan.get("run_id") == expected_run_id, "run_replay")
        created = cast(float, plan.get("created_at"))
        age = cast(float, plan.get("max_age_seconds"))
        _require(_number(created) and _number(age) and 0 < age <= 86400, "freshness_required")
        _require(0 <= current - created <= age, "stale_or_future_plan")
        artifacts = cast(list[dict[str, Any]], plan.get("artifacts"))
        checks = cast(list[dict[str, Any]], plan.get("checks"))
        _require(type(artifacts) is list and 2 <= len(artifacts) <= 100, "artifacts_required")
        _require(type(checks) is list and 0 < len(checks) <= 100, "checks_required")
        observed, roles, snapshots = {}, set(), {plan_relative: expected_plan_sha256}
        for artifact in artifacts:
            _require(
                type(artifact) is dict and set(artifact) == {"path", "sha256", "role"},
                "artifact_schema",
            )
            relative, digest, role = (
                cast(str, artifact.get("path")),
                cast(str, artifact.get("sha256")),
                artifact.get("role"),
            )
            _relative(relative)
            _require(
                _digest(digest) and relative not in snapshots and role in ("source", "output"),
                "artifact_binding",
            )
            _require(_sha(_read(root, relative)) == digest, "artifact_changed_or_unavailable")
            observed[relative] = digest
            snapshots[relative] = digest
            roles.add(role)
        _require(roles == {"source", "output"}, "source_and_output_required")
        ids = set()
        for check in checks:
            _require(type(check) is dict and set(check) == {"id", "path", "sha256"}, "check_schema")
            cid, relative, digest = (
                cast(str, check.get("id")),
                cast(str, check.get("path")),
                cast(str, check.get("sha256")),
            )
            _require(isinstance(cid, str) and cid and cid not in ids, "duplicate_or_invalid_check")
            ids.add(cid)
            _relative(relative)
            _require(relative not in snapshots and _digest(digest), "check_binding")
            raw = _read(root, relative)
            _require(_sha(raw) == digest, "check_changed")
            snapshots[relative] = digest
            row = _json(raw)
            _require(
                type(row) is dict
                and row.get("schema") == "hyodo.handoff-check/v1"
                and set(row)
                == {
                    "schema",
                    "run_id",
                    "id",
                    "status",
                    "coverage",
                    "exit_code",
                    "observed_at",
                    "artifact_digests",
                    "producer",
                },
                "observation_schema",
            )
            _require(row.get("run_id") == expected_run_id and row.get("id") == cid, "check_replay")
            _require(
                row.get("status") == "PASS"
                and row.get("coverage") == "OBSERVED"
                and type(row.get("exit_code")) is int
                and row["exit_code"] == 0,
                "check_not_passed",
            )
            stamped = cast(float, row.get("observed_at"))
            _require(
                _number(stamped) and created <= stamped <= current and current - stamped <= age,
                "stale_or_future_observation",
            )
            _require(row.get("artifact_digests") == observed, "check_artifact_mismatch")
            _require(
                isinstance(row.get("producer"), str)
                and bool(row["producer"])
                and row["producer"].strip() == row["producer"],
                "canonical_producer_required",
            )
            if cid == "review":
                producer = plan.get("producer")
                _require(
                    isinstance(producer, str) and producer.strip() and row["producer"] != producer,
                    "independent_review_required",
                )
            result["checks_observed"] += 1
        _require(REQUIRED[kind] <= ids, "required_check_missing")
        # Detect mutation during verification, including plan or observation edits.
        for relative, digest in snapshots.items():
            _require(_sha(_read(root, relative)) == digest, "changed_during_verification")
        final_now = time.time() if now is None else now
        _require(current <= final_now <= created + age, "expired_during_verification")
        result.update(
            status="VERIFIED_EVIDENCE",
            kind=kind,
            run_id=expected_run_id,
            plan_sha256=expected_plan_sha256,
            artifact_digests=observed,
            checked_at=final_now,
            expires_at=created + age,
        )
    except (Hold, OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError):
        result["reason"] = "missing_invalid_stale_or_failed_evidence"
    return result


def receipt_matches(path: Path, expected: bytes) -> bool:
    """Read back a bounded regular receipt without following symlinks."""
    absolute = Path(path).absolute()
    return _read(absolute.parent, absolute.name) == expected
