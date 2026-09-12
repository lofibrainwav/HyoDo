"""Bounded QMD retrieval provenance for the agent-event ledger.

The QMD result is an input to this module, never a ledger value.  HyoDo stores
only a deterministic digest and a small, explicitly allow-listed metadata
projection so retrieval provenance can be correlated without retaining
queries, prompts, or retrieved document bodies.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

RETRIEVAL_PROVENANCE_SCHEMA_VERSION = "provenance.retrieval/v1"
RETRIEVAL_PROVENANCE_FIELDS = frozenset(
    {
        "schema_version",
        "source_sha",
        "run_id",
        "qmd_uri",
        "evidence_ref",
        "result_digest",
        "result_metadata",
        "receipt_id",
    }
)
_RECEIPT_ID_FIELDS = ("source_sha", "run_id", "qmd_uri", "evidence_ref", "result_digest")
_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_METADATA_KEYS = 8
_MAX_METADATA_DEPTH = 2
_MAX_STRING_LENGTH = 256

# These are the scalar facts useful for readback and safe to expose.  In
# particular, arbitrary QMD/provider keys are not allowed to become a covert
# document-body channel.
RESULT_METADATA_ALLOWLIST = frozenset(
    {
        "chunk_id",
        "collection",
        "document_id",
        "language",
        "mime_type",
        "rank",
        "result_count",
        "score",
    }
)

_LEAKAGE_MARKERS = (
    "token=",
    "api_key=",
    "apikey=",
    "secret=",
    "password=",
    "access_token=",
    "authorization:",
    "bearer ",
)


def normalize_qmd_uri(value: Any) -> str | None:
    """Return the only safe qmd URI form accepted by the carrier.

    QMD virtual paths are identifiers, not URLs with transport credentials.  A
    query or fragment is therefore rejected instead of being silently dropped.
    """
    if not isinstance(value, str):
        return None
    uri = value.strip()
    if not uri or any(ord(char) < 0x20 for char in uri) or any(char.isspace() for char in uri):
        return None
    if "?" in uri or "#" in uri:
        return None
    if not uri.startswith("qmd:"):
        return None
    rest = uri[4:].lstrip("/")
    parts = rest.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return f"qmd://{parts[0]}/{parts[1]}"


def canonical_json(value: Any) -> str:
    """Serialize JSON with recursive lexicographic object keys and UTF-8-safe output."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def result_digest(qmd_result: Any) -> str:
    """Return the full SHA-256 digest of canonical JSON *qmd_result*."""
    return hashlib.sha256(canonical_json(qmd_result).encode("utf-8")).hexdigest()


def projection_receipt_id(
    *,
    source_sha: str,
    run_id: str,
    qmd_uri: str,
    evidence_ref: str,
    result_digest: str,
) -> str:
    """Derive the stable projection id required by ``provenance.retrieval/v1``."""
    identity = {
        "source_sha": source_sha,
        "run_id": run_id,
        "qmd_uri": qmd_uri,
        "evidence_ref": evidence_ref,
        "result_digest": result_digest,
    }
    return hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()


def _metadata_depth(value: Any, depth: int = 1) -> int:
    if isinstance(value, dict):
        return max((_metadata_depth(child, depth + 1) for child in value.values()), default=depth)
    if isinstance(value, list):
        return depth + 1
    return depth


def _validate_metadata(value: Any, reasons: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        reasons.append("invalid_field:provenance.retrieval.result_metadata")
        return None
    if len(value) > _MAX_METADATA_KEYS:
        reasons.append("metadata_bound:key_count")
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if key not in RESULT_METADATA_ALLOWLIST:
            reasons.append(f"unsupported_metadata_key:{key}")
            continue
        if isinstance(item, (dict, list)):
            reasons.append(f"metadata_bound:nested:{key}")
            continue
        if isinstance(item, str) and len(item) > _MAX_STRING_LENGTH:
            reasons.append(f"metadata_bound:string_length:{key}")
            continue
        if isinstance(item, str) and any(marker in item.lower() for marker in _LEAKAGE_MARKERS):
            reasons.append(f"unsupported_metadata_value:{key}")
            continue
        if item is not None and not isinstance(item, (str, int, float, bool)):
            reasons.append(f"invalid_metadata_value:{key}")
            continue
        normalized[key] = item
    if _metadata_depth(value) > _MAX_METADATA_DEPTH:
        reasons.append("metadata_bound:depth")
    return normalized


def normalize_retrieval_projection(
    raw: Any,
    *,
    event_run_id: str | None = None,
    event_source_sha: str | None = None,
    event_evidence_ref: str | None = None,
) -> tuple[bool, list[str], dict[str, Any] | None]:
    """Validate and normalize a retrieval projection, dropping raw result data."""
    if not isinstance(raw, dict):
        return False, ["invalid_field:provenance.retrieval"], None
    reasons: list[str] = []
    for key in raw:
        if key == "retrieval_receipt":
            reasons.append("unsupported_field:retrieval_receipt")
            continue
        if key not in RETRIEVAL_PROVENANCE_FIELDS and key != "qmd_result":
            reasons.append(f"unsupported_field:provenance.retrieval.{key}")
    supplied_digest = raw.get("result_digest")
    digest = supplied_digest
    if "qmd_result" not in raw and "result_digest" not in raw:
        reasons.append("missing_field:provenance.retrieval.result_digest")
    if "qmd_result" in raw:
        try:
            computed_digest = result_digest(raw["qmd_result"])
            if supplied_digest is not None and computed_digest != supplied_digest:
                reasons.append("digest_mismatch:provenance.retrieval.result_digest")
            digest = computed_digest
        except (TypeError, ValueError, OverflowError):
            reasons.append("invalid_field:provenance.retrieval.qmd_result")
    if raw.get("schema_version") != RETRIEVAL_PROVENANCE_SCHEMA_VERSION:
        reasons.append("unsupported_schema:provenance.retrieval")

    string_fields = ("source_sha", "run_id", "qmd_uri", "evidence_ref")
    for field in string_fields:
        value = raw.get(field)
        if not isinstance(value, str) or not value.strip():
            reasons.append(f"missing_field:provenance.retrieval.{field}")
    source_sha = raw.get("source_sha")
    if isinstance(source_sha, str) and not _SHA_RE.fullmatch(source_sha):
        reasons.append("invalid_field:provenance.retrieval.source_sha")
    raw_qmd_uri = raw.get("qmd_uri")
    qmd_uri = normalize_qmd_uri(raw_qmd_uri)
    if qmd_uri is None:
        reasons.append("invalid_field:provenance.retrieval.qmd_uri")
    if isinstance(digest, str) and not _DIGEST_RE.fullmatch(digest):
        reasons.append("invalid_field:provenance.retrieval.result_digest")
    receipt_id = raw.get("receipt_id")
    if receipt_id is None:
        reasons.append("missing_field:provenance.retrieval.receipt_id")
    elif not isinstance(receipt_id, str) or not _DIGEST_RE.fullmatch(receipt_id):
        reasons.append("invalid_field:provenance.retrieval.receipt_id")

    if "result_metadata" in raw:
        metadata_out = _validate_metadata(raw["result_metadata"], reasons)
    else:
        metadata_out = None

    if event_run_id is not None and raw.get("run_id") != event_run_id:
        reasons.append("mismatch:provenance.retrieval.run_id")
    if event_source_sha is not None and raw.get("source_sha") != event_source_sha:
        reasons.append("mismatch:provenance.retrieval.source_sha")
    if event_evidence_ref is not None and raw.get("evidence_ref") != event_evidence_ref:
        reasons.append("mismatch:provenance.retrieval.evidence_ref")

    if not reasons:
        assert isinstance(source_sha, str)
        assert isinstance(raw.get("run_id"), str)
        assert isinstance(qmd_uri, str)
        assert isinstance(raw.get("evidence_ref"), str)
        assert isinstance(digest, str)
        expected_id = projection_receipt_id(
            source_sha=source_sha,
            run_id=raw["run_id"],
            qmd_uri=qmd_uri,
            evidence_ref=raw["evidence_ref"],
            result_digest=digest,
        )
        if receipt_id != expected_id:
            reasons.append("mismatch:provenance.retrieval.receipt_id")

    if reasons:
        return False, list(dict.fromkeys(reasons)), None
    normalized = {
        "schema_version": RETRIEVAL_PROVENANCE_SCHEMA_VERSION,
        "source_sha": source_sha,
        "run_id": raw["run_id"],
        "qmd_uri": qmd_uri,
        "evidence_ref": raw["evidence_ref"],
        "result_digest": digest,
        "receipt_id": receipt_id,
    }
    if metadata_out is not None:
        normalized["result_metadata"] = metadata_out
    return True, [], normalized


def normalize_event_provenance(
    raw: Any,
    *,
    event_run_id: str,
    event_evidence_ref: str | None = None,
) -> tuple[bool, list[str], dict[str, Any] | None]:
    """Normalize the event carrier and enforce execution/retrieval correlation."""
    if raw is None:
        return True, [], None
    if not isinstance(raw, dict):
        return False, ["invalid_field:provenance"], None
    if "retrieval_receipt" in raw:
        return False, ["unsupported_field:retrieval_receipt"], None
    allowed = {"source_sha", "retrieval"}
    reasons = [f"unsupported_field:provenance.{key}" for key in raw if key not in allowed]
    retrieval = raw.get("retrieval")
    if retrieval is None:
        if "source_sha" not in raw:
            return False, reasons, None
        if not isinstance(raw["source_sha"], str) or not _SHA_RE.fullmatch(raw["source_sha"]):
            reasons.append("invalid_field:provenance.source_sha")
        return (not reasons), reasons, {"source_sha": raw["source_sha"], "retrieval": None}
    source_sha = raw.get("source_sha")
    if source_sha is not None and (not isinstance(source_sha, str) or not source_sha.strip()):
        reasons.append("invalid_field:provenance.source_sha")
    ok, retrieval_reasons, normalized_retrieval = normalize_retrieval_projection(
        retrieval,
        event_run_id=event_run_id,
        event_source_sha=source_sha,
        event_evidence_ref=event_evidence_ref,
    )
    reasons.extend(retrieval_reasons)
    if reasons or not ok or normalized_retrieval is None:
        return False, list(dict.fromkeys(reasons)), None
    return True, [], {"source_sha": source_sha, "retrieval": normalized_retrieval}


__all__ = [
    "RESULT_METADATA_ALLOWLIST",
    "RETRIEVAL_PROVENANCE_FIELDS",
    "RETRIEVAL_PROVENANCE_SCHEMA_VERSION",
    "canonical_json",
    "normalize_event_provenance",
    "normalize_qmd_uri",
    "normalize_retrieval_projection",
    "projection_receipt_id",
    "result_digest",
]
