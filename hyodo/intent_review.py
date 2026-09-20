"""Bounded comparisons of host-supplied requirements, never semantic approval.

The host owns interpretation and supplies the values. Resolving a citation does
not authenticate a person, verify those values, or establish a complete intent.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

DIMENSIONS = ("goal", "scope", "constraints", "completion")
SCHEMA = "hyodo.intent-review/v1"


def _text(value: Any, limit: int = 200) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def _number(value: Any) -> bool:
    return type(value) in (int, float) and abs(value) <= 1e100 and math.isfinite(value)


def _scalar(value: Any) -> bool:
    return type(value) is bool or _text(value, 160) or _number(value)


def normalize_intent_review(raw: Any) -> dict[str, Any] | None:
    """Validate the opt-in comparison block; reject malformed or ambiguous inputs."""
    keys = {"schema_version", "intent_ref", "mode", "target", "checks"}
    if (
        not isinstance(raw, dict)
        or not keys <= set(raw)
        or set(raw) - keys - {"previous_review_ref"}
    ):
        return None
    if (
        raw["schema_version"] != SCHEMA
        or not _text(raw["intent_ref"])
        or raw["mode"] not in ("OBSERVED", "PROJECTED")
        or raw["target"] not in ("interpretation", "action", "outcome")
        or not isinstance(raw["checks"], list)
        or not 1 <= len(raw["checks"]) <= 32
        or (raw.get("previous_review_ref") is not None and not _text(raw["previous_review_ref"]))
    ):
        return None
    checks: list[dict[str, Any]] = []
    ids: set[str] = set()
    fields = {"id", "dimension", "basis", "operator", "expected", "actual", "unit", "evidence_refs"}
    for check in raw["checks"]:
        if not isinstance(check, dict) or set(check) != fields:
            return None
        refs = check["evidence_refs"]
        expected, actual = check["expected"], check["actual"]
        if (
            not _text(check["id"], 80)
            or check["id"].strip() in ids
            or check["dimension"] not in DIMENSIONS
            or check["basis"] not in ("DECLARED", "INFERRED")
            or check["operator"] not in ("eq", "lte", "gte")
            or not _scalar(expected)
            or (actual is not None and not _scalar(actual))
            or (check["unit"] is not None and not _text(check["unit"], 40))
            or not isinstance(refs, list)
            or len(refs) > 32
            or any(not _text(ref) for ref in refs)
        ):
            return None
        if check["operator"] != "eq" and not _number(expected):
            return None
        if actual is not None:
            compatible = (_number(expected) and _number(actual)) or type(expected) is type(actual)
            if not compatible:
                return None
        ids.add(check["id"].strip())
        checks.append(
            {
                **check,
                "id": check["id"].strip(),
                "evidence_refs": list(dict.fromkeys(r.strip() for r in refs)),
            }
        )
    return {**raw, "intent_ref": raw["intent_ref"].strip(), "checks": checks}


def _time(node: dict[str, Any]) -> datetime | None:
    try:
        value = datetime.fromisoformat(str(node.get("ts", "")).replace("Z", "+00:00"))
        return value if value.tzinfo is not None else None
    except ValueError:
        return None


def _precedes(source: dict[str, Any], target: dict[str, Any]) -> bool:
    before, after = _time(source), _time(target)
    if before is None or after is None:
        return False
    if before != after:
        return before < after
    source_step, target_step = source.get("step_index"), target.get("step_index")
    return (
        isinstance(source.get("run_id"), str)
        and source.get("run_id") == target.get("run_id")
        and type(source_step) is int
        and type(target_step) is int
        and source_step < target_step
    )


def _history_link(
    review: dict[str, Any], node: dict[str, Any], nodes: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    ref = review.get("previous_review_ref")
    result: dict[str, Any] = {
        "previous_review_ref": ref,
        "state": "UNOBSERVED",
        "requirement_changes": [],
    }
    previous = nodes.get(ref) if isinstance(ref, str) and ref != node.get("id") else None
    before = normalize_intent_review(previous.get("intent_review")) if previous else None
    if before is None or previous is None or not _precedes(previous, node):
        return result
    old = {c["id"]: c for c in before["checks"]}
    new = {c["id"]: c for c in review["checks"]}
    changes = []
    fields = ("dimension", "basis", "operator", "expected", "unit")
    for key in sorted(old.keys() | new.keys()):
        a, b = old.get(key), new.get(key)
        changed = [field for field in fields if (a or {}).get(field) != (b or {}).get(field)]
        if a is None or b is None or changed:
            changes.append(
                {
                    "id": key,
                    "kind": "added" if a is None else "removed" if b is None else "changed",
                    "fields": changed,
                    "before": {f: a[f] for f in fields} if a else None,
                    "after": {f: b[f] for f in fields} if b else None,
                }
            )
    result.update(
        state="LINKED",
        intent_source_changed=before["intent_ref"] != review["intent_ref"],
        previous_mode=before["mode"],
        previous_target=before["target"],
        requirement_changes=changes,
    )
    return result


def project_intent_review(
    node: dict[str, Any], nodes: dict[str, dict[str, Any]], *, references_ready: bool = True
) -> dict[str, Any]:
    """Compare declared values while exposing missing, inferred, or future evidence.

    A result is a bounded comparison of host-supplied values, not independent
    verification of those values or a semantic alignment score. No lens state,
    policy decision, or execution authority is changed by this projection.
    """
    review = normalize_intent_review(node.get("intent_review"))
    if review is None:
        return {
            "state": "UNOBSERVED",
            "reason": "no_valid_intent_review",
            "checks": [],
            "missing_dimensions": list(DIMENSIONS),
        }
    intent = nodes.get(review["intent_ref"])
    common: list[str] = []
    if not references_ready:
        common.append("graph_references_not_ready")
    if not intent or intent.get("kind") != "prompt" or intent.get("actor") != "human":
        common.append("human_intent_source_unobserved")
    else:
        if not _precedes(intent, node):
            common.append("intent_time_unobserved_or_later")
    if review["mode"] == "PROJECTED":
        common.append("hypothetical_comparison")
    history = (
        _history_link(review, node, nodes)
        if references_ready
        else {
            "previous_review_ref": review.get("previous_review_ref"),
            "state": "UNOBSERVED",
            "requirement_changes": [],
        }
    )
    changed_without_source = {
        change["id"]
        for change in history["requirement_changes"]
        if history.get("intent_source_changed") is False
    }
    checks: list[dict[str, Any]] = []
    for check in review["checks"]:
        missing = list(common)
        if check["id"] in changed_without_source:
            missing.append("requirement_changed_without_new_intent_source")
        if check["basis"] == "INFERRED":
            missing.append("inferred_requirement_not_user_confirmed")
        if check["actual"] is None:
            missing.append("actual_value_unobserved")
        if not check["evidence_refs"]:
            missing.append("result_evidence_unobserved")
        for ref in check["evidence_refs"]:
            evidence = nodes.get(ref)
            if not evidence or ref == node.get("id"):
                missing.append("unresolved_or_self_evidence:" + ref)
                continue
            if not _precedes(evidence, node):
                missing.append("evidence_time_unobserved_or_later:" + ref)
            io = evidence.get("io")
            if not isinstance(io, dict) or not io.get("output_digest"):
                missing.append("result_digest_unobserved:" + ref)
        expected, actual = check["expected"], check["actual"]
        comparison = "UNOBSERVED"
        delta = None
        if actual is not None:
            matches = (
                actual == expected
                if check["operator"] == "eq"
                else actual <= expected
                if check["operator"] == "lte"
                else actual >= expected
            )
            comparison = "SATISFIED" if matches else "DEVIATES"
            if _number(expected) and _number(actual):
                delta = actual - expected
        checks.append(
            {
                **check,
                "comparison": comparison,
                "state": "UNOBSERVED" if missing else comparison,
                "delta": delta,
                "missing": missing,
            }
        )
    return {
        "state": "RECORDED",
        "intent_ref": review["intent_ref"],
        "target": review["target"],
        "mode": review["mode"],
        "history": history,
        "reviewer": {"actor": node.get("actor"), "actor_id": node.get("actor_id")},
        "checks": checks,
        "missing_dimensions": [
            d for d in DIMENSIONS if not any(c["dimension"] == d for c in checks)
        ],
        "boundary": "Host-supplied requirements and values; references are not authenticated intent, verified values, or authorization.",
    }
