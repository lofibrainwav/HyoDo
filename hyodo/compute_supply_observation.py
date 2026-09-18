"""Provider-neutral observation receipt for external compute supply."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "hyodo.compute-supply-observation/v1"
OBSERVATION_STATES = frozenset({"FREE_OK", "STALE", "UNOBSERVED", "OBSERVED"})
_SECRET_TERMS = ("api_key", "token", "secret", "password", "authorization", "credential")
_CONTENT_TERMS = ("prompt", "response", "content")


def _redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(term in lowered for term in _SECRET_TERMS):
                cleaned[str(key)] = "REDACTED"
            elif any(term in lowered for term in _CONTENT_TERMS):
                continue
            else:
                cleaned[str(key)] = _redact(item)
        return cleaned
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def build_observation_receipt(
    *,
    catalog: Mapping[str, Any] | None = None,
    user_availability: Mapping[str, Any] | None = None,
    live_access: Mapping[str, Any] | None = None,
    observed_at: str | None = None,
    fresh_until: str | None = None,
    evidence_source: str = "UNOBSERVED",
) -> dict[str, Any]:
    """Build evidence only; this function never selects or routes a model."""
    return {
        "schema_version": SCHEMA_VERSION,
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        "fresh_until": fresh_until or "UNOBSERVED",
        "evidence_source": evidence_source,
        "catalog": _redact(dict(catalog or {})),
        "user_availability": _redact(dict(user_availability or {})),
        "live_access": _redact(dict(live_access or {})),
    }


def validate_observation_receipt(receipt: Any) -> tuple[bool, list[str]]:
    if not isinstance(receipt, dict):
        return False, ["not_object"]
    reasons: list[str] = []
    if receipt.get("schema_version") != SCHEMA_VERSION:
        reasons.append("unsupported_schema")
    for field in ("observed_at", "fresh_until", "evidence_source", "catalog", "user_availability", "live_access"):
        if field not in receipt:
            reasons.append(f"missing:{field}")
    if not isinstance(receipt.get("catalog"), dict):
        reasons.append("catalog_not_object")
    if not isinstance(receipt.get("user_availability"), dict):
        reasons.append("user_availability_not_object")
    if not isinstance(receipt.get("live_access"), dict):
        reasons.append("live_access_not_object")
    return not reasons, reasons


__all__ = ["SCHEMA_VERSION", "build_observation_receipt", "validate_observation_receipt"]
