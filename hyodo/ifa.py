"""Information Flow Attestation v0 — observer-only privacy lineage.

IFA records observed information derivation. It never grants or denies
execution authority and it never treats evidence citations as flow edges.
"""

from __future__ import annotations

from typing import Any

IFA_SCHEMA = "hyodo.ifa/v0"
SENSITIVITY = frozenset({"public", "internal", "confidential", "restricted", "unknown"})
TRANSFORMS = frozenset({"copy", "summarize", "redact", "aggregate", "unknown"})
SINKS = frozenset({"local_process", "local_file", "human_visible", "external_network", "unknown"})


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _explicit_declassification(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    evaluated_by = _text(raw.get("evaluated_by"))
    evidence_ref = _text(raw.get("evidence_ref"))
    output_label = raw.get("output_label")
    if evaluated_by is None or evidence_ref is None or output_label not in SENSITIVITY:
        return None
    return {
        "evaluated_by": evaluated_by,
        "evidence_ref": evidence_ref,
        "output_label": output_label,
    }


def normalize_flow(raw: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """Normalize one asserted observation without inferring missing facts."""
    reasons: list[str] = []
    if raw.get("schema") != IFA_SCHEMA:
        reasons.append("unsupported_schema")
    flow_id = _text(raw.get("flow_id"))
    run_id = _text(raw.get("run_id"))
    source = _text(raw.get("source_event_id"))
    target = _text(raw.get("target_event_id"))
    if flow_id is None:
        reasons.append("missing_flow_id")
    if run_id is None:
        reasons.append("missing_run_id")
    if source is None:
        reasons.append("missing_source_event_id")
    if target is None:
        reasons.append("missing_target_event_id")

    label = raw.get("sensitivity")
    transform = raw.get("transformation")
    sink = raw.get("sink_class", "unknown")
    if label not in SENSITIVITY:
        reasons.append("invalid_sensitivity")
    if transform not in TRANSFORMS:
        reasons.append("invalid_transformation")
    if sink not in SINKS:
        reasons.append("invalid_sink")
    if reasons:
        return None, reasons

    declassification = _explicit_declassification(raw.get("declassification"))
    requested_declassification = raw.get("declassification") is not None
    return (
        {
            "schema": IFA_SCHEMA,
            "flow_id": flow_id,
            "run_id": run_id,
            "source_event_id": source,
            "target_event_id": target,
            "sensitivity": label,
            "transformation": transform,
            "sink_class": sink,
            "declassification": declassification,
            "declassification_observed": declassification is not None,
            "declassification_unobserved": requested_declassification and declassification is None,
        },
        [],
    )


def attest_information_flow(
    observations: list[dict[str, Any]], *, event_ids: set[str]
) -> dict[str, Any]:
    """Return deterministic privacy-lineage evidence without an authority verdict."""
    flows: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []
    risks: list[dict[str, str]] = []

    for raw in observations:
        normalized, reasons = normalize_flow(raw)
        if normalized is None:
            invalid.append({"flow_id": _text(raw.get("flow_id")) or "", "reasons": sorted(reasons)})
            continue
        source = normalized["source_event_id"]
        target = normalized["target_event_id"]
        if source not in event_ids:
            unresolved.append({"flow_id": normalized["flow_id"], "event_id": source})
        if target not in event_ids:
            unresolved.append({"flow_id": normalized["flow_id"], "event_id": target})

        effective_label = normalized["sensitivity"]
        if normalized["declassification_observed"]:
            effective_label = normalized["declassification"]["output_label"]
        normalized["effective_sensitivity"] = effective_label

        if (
            normalized["sink_class"] == "external_network"
            and effective_label not in {"public", "unknown"}
        ):
            risks.append(
                {
                    "flow_id": normalized["flow_id"],
                    "reason": "sensitive_external_sink_observed",
                }
            )
        elif normalized["sink_class"] == "external_network" and effective_label == "unknown":
            risks.append(
                {
                    "flow_id": normalized["flow_id"],
                    "reason": "external_sink_sensitivity_unobserved",
                }
            )
        flows.append(normalized)

    flows.sort(key=lambda row: (row["run_id"], row["flow_id"]))
    invalid.sort(key=lambda row: row["flow_id"])
    unresolved.sort(key=lambda row: (row["flow_id"], row["event_id"]))
    risks.sort(key=lambda row: (row["flow_id"], row["reason"]))
    status = "OBSERVED" if not invalid and not unresolved else "UNOBSERVED"
    return {
        "schema": IFA_SCHEMA,
        "status": status,
        "flows": flows,
        "invalid": invalid,
        "unresolved": unresolved,
        "risks": risks,
        "authority_decision": None,
    }


__all__ = [
    "IFA_SCHEMA",
    "SENSITIVITY",
    "SINKS",
    "TRANSFORMS",
    "attest_information_flow",
    "normalize_flow",
]
