"""Provenance-only agent nameplates.

An agent nameplate identifies the harness-assigned role and the observed
execution context for one exact artifact. It never authenticates an actor and
never grants authority, approval, or merge permission.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

AGENT_NAMEPLATE_SCHEMA_VERSION = "hyodo.agent-nameplate/v1"
UNOBSERVED = "UNOBSERVED"
ROLES = frozenset({"builder", "verifier", "observer", UNOBSERVED})
_ACTOR_ID_RE = re.compile(r"^[A-Za-z0-9._:@-]{1,64}$")
_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
_RUNTIME_FIELDS = ("host", "provider", "model", "mode", "session_id", "github_actor")
_FIELDS = frozenset(
    {
        "schema_version",
        "actor_id",
        "role",
        "host",
        "provider",
        "model",
        "mode",
        "session_id",
        "github_actor",
        "observed_at",
        "repo",
        "exact_artifact_sha",
    }
)

Linkage = Literal["MATCH", "MISMATCH", "UNOBSERVED"]


def runtime_observations(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Read only explicitly supported runtime labels; absent values stay unknown."""
    source = os.environ if environ is None else environ
    return {
        "actor_id": source.get("HYODO_AGENT") or UNOBSERVED,
        "host": source.get("HYODO_HOST") or UNOBSERVED,
        "provider": source.get("HYODO_PROVIDER") or UNOBSERVED,
        "model": source.get("HYODO_MODEL") or UNOBSERVED,
        "mode": source.get("HYODO_MODE") or UNOBSERVED,
        "session_id": source.get("HYODO_SESSION_ID") or UNOBSERVED,
        "github_actor": source.get("GITHUB_ACTOR") or UNOBSERVED,
    }


def _string_or_unobserved(value: Any) -> str | None:
    if value is None:
        return UNOBSERVED
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _valid_observed_at(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_nameplate(raw: Any) -> tuple[bool, list[str], dict[str, Any] | None]:
    """Validate and normalize one ``hyodo.agent-nameplate/v1`` object."""
    if not isinstance(raw, dict):
        return False, ["not_an_object"], None

    reasons = [f"unsupported_field:{key}" for key in raw if key not in _FIELDS]
    if raw.get("schema_version") != AGENT_NAMEPLATE_SCHEMA_VERSION:
        reasons.append("unsupported_schema")

    normalized: dict[str, Any] = {}
    for field in _FIELDS:
        if field not in raw:
            reasons.append(f"missing_field:{field}")

    actor_id = _string_or_unobserved(raw.get("actor_id"))
    if actor_id is None or (actor_id != UNOBSERVED and not _ACTOR_ID_RE.fullmatch(actor_id)):
        reasons.append("invalid_field:actor_id")
    else:
        normalized["actor_id"] = actor_id

    role = raw.get("role")
    if role not in ROLES:
        reasons.append("invalid_field:role")
    else:
        normalized["role"] = role

    for field in (*_RUNTIME_FIELDS, "repo"):
        value = _string_or_unobserved(raw.get(field))
        if value is None:
            reasons.append(f"invalid_field:{field}")
        else:
            normalized[field] = value

    observed_at = raw.get("observed_at")
    if not _valid_observed_at(observed_at):
        reasons.append("invalid_field:observed_at")
    else:
        normalized["observed_at"] = observed_at

    artifact_sha = raw.get("exact_artifact_sha")
    if not isinstance(artifact_sha, str) or not _SHA_RE.fullmatch(artifact_sha):
        reasons.append("invalid_field:exact_artifact_sha")
    else:
        normalized["exact_artifact_sha"] = artifact_sha

    if reasons:
        return False, list(dict.fromkeys(reasons)), None

    normalized["schema_version"] = AGENT_NAMEPLATE_SCHEMA_VERSION
    return True, [], {field: normalized[field] for field in _FIELDS}


def build_nameplate(
    *,
    actor_id: str | None,
    role: str | None,
    repo: str | None,
    exact_artifact_sha: str,
    observed_at: str,
    runtime: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a nameplate from harness inputs and observed runtime labels.

    ``role`` is an explicit harness input. This function never infers it from
    a model, prompt, or environment variable.
    """
    observations = (
        runtime_observations()
        if runtime is None
        else {
            field: runtime.get(field, UNOBSERVED) or UNOBSERVED
            for field in ("actor_id", *_RUNTIME_FIELDS)
        }
    )
    raw = {
        "schema_version": AGENT_NAMEPLATE_SCHEMA_VERSION,
        "actor_id": actor_id or observations["actor_id"],
        "role": role or UNOBSERVED,
        **observations,
        "observed_at": observed_at,
        "repo": repo or UNOBSERVED,
        "exact_artifact_sha": exact_artifact_sha,
    }
    ok, reasons, normalized = validate_nameplate(raw)
    if not ok or normalized is None:
        raise ValueError("invalid agent nameplate: " + ", ".join(reasons))
    return normalized


def validate_nameplate_for_artifact(
    raw: Any, artifact_sha: str
) -> tuple[bool, list[str], dict[str, Any] | None]:
    """Validate a nameplate and bind it to the exact artifact being observed."""
    ok, reasons, normalized = validate_nameplate(raw)
    if not ok or normalized is None:
        return ok, reasons, normalized
    if not isinstance(artifact_sha, str) or not _SHA_RE.fullmatch(artifact_sha):
        return False, ["invalid_artifact_sha"], None
    if normalized["exact_artifact_sha"] != artifact_sha:
        return False, ["artifact_sha_mismatch"], None
    return True, [], normalized


def actor_id_linkage(nameplate: Mapping[str, Any], event_actor_id: str | None) -> Linkage:
    """Compare nameplate ``actor_id`` with an existing event's opaque label."""
    nameplate_actor_id = nameplate.get("actor_id")
    if nameplate_actor_id in (None, UNOBSERVED) or event_actor_id is None or not event_actor_id:
        return "UNOBSERVED"
    return "MATCH" if nameplate_actor_id == event_actor_id else "MISMATCH"


__all__ = [
    "AGENT_NAMEPLATE_SCHEMA_VERSION",
    "ROLES",
    "UNOBSERVED",
    "Linkage",
    "actor_id_linkage",
    "build_nameplate",
    "runtime_observations",
    "validate_nameplate",
    "validate_nameplate_for_artifact",
]
