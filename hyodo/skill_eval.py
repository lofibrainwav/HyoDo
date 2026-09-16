"""Independent Skill Eval oracle for the v1 runtime-ownership slice.

HyoDo consumes observed evidence and returns a verdict. It does not execute a
skill, grant execution authority, or promote a skill version.
"""

from __future__ import annotations

from typing import Any

SKILL_EVAL_ORACLE = "hyodo.skill-eval/v1"
SKILL_EVAL_STATUSES = frozenset({"PASS", "FAIL", "HOLD", "UNOBSERVED"})


def _is_object(value: Any) -> bool:
    return isinstance(value, dict)


def _evidence_item_state(item: Any, execution: dict[str, Any]) -> str:
    if item is None:
        return "missing"
    if not _is_object(item):
        return "malformed"
    if item.get("integrity") in {"mismatch", "tampered"}:
        return "tampered"
    if item.get("observed") is not True:
        return "pending" if item.get("state") == "PENDING" else "missing"
    if "value" not in item or item.get("value") is None:
        return "malformed"
    if item.get("freshness") != "fresh":
        return "stale"
    if not isinstance(item.get("producer"), str) or not item["producer"].strip():
        return "malformed"
    if item.get("run_id") != execution.get("run_id") or item.get("execution_id") != execution.get(
        "execution_id"
    ):
        return "uncorrelated"
    if item.get("integrity") != "verified":
        return "malformed"
    return "observed"


def evaluate_evidence_gate(
    *, case: dict[str, Any], execution: dict[str, Any], evidence: Any, receipt: Any
) -> dict[str, Any]:
    if not _is_object(evidence):
        return {"status": "UNOBSERVED", "reason": "evidence_envelope_unobserved"}
    missing: list[str] = []
    malformed: list[str] = []
    stale: list[str] = []
    uncorrelated: list[str] = []
    tampered: list[str] = []
    pending_effect = False
    for key in case["required_evidence"]:
        state = _evidence_item_state(evidence.get(key), execution)
        if state == "tampered":
            tampered.append(key)
        elif state == "missing":
            missing.append(key)
        elif (
            state == "pending"
            and key == "effect_readback"
            and _is_object(receipt)
            and receipt.get("success") is True
        ):
            pending_effect = True
        elif state == "pending":
            missing.append(key)
        elif state == "malformed":
            malformed.append(key)
        elif state == "stale":
            stale.append(key)
        elif state == "uncorrelated":
            uncorrelated.append(key)
    if tampered:
        return {"status": "FAIL", "reason": "evidence_tampering", "evidence_keys": tampered}
    if missing or malformed or stale or uncorrelated:
        reason = (
            "required_evidence_missing"
            if missing
            else "required_evidence_malformed"
            if malformed
            else "required_evidence_stale"
            if stale
            else "required_evidence_uncorrelated"
        )
        return {
            "status": "UNOBSERVED",
            "reason": reason,
            "evidence": {
                "missing": missing,
                "malformed": malformed,
                "stale": stale,
                "uncorrelated": uncorrelated,
            },
        }
    if pending_effect:
        return {"status": "HOLD", "reason": "receipt_without_effect_readback", "false_green": True}
    return {"status": "OBSERVED"}


def validate_case(case: Any) -> list[str]:
    if not _is_object(case):
        return ["case_not_object"]
    errors: list[str] = []
    for field in ("eval_id", "skill_id", "skill_version", "scenario"):
        if not isinstance(case.get(field), str) or not case[field].strip():
            errors.append(f"{field}_missing")
    for field in ("input_fixture", "expected_behavior"):
        if not _is_object(case.get(field)):
            errors.append(f"{field}_invalid")
    for field in ("forbidden_behavior", "required_evidence", "critical_invariants"):
        value = case.get(field)
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            errors.append(f"{field}_invalid")
    if case.get("oracle") != SKILL_EVAL_ORACLE:
        errors.append("oracle_unsupported")
    return errors


def evaluate_skill_case(
    *,
    case: Any,
    execution: Any,
    evidence: Any,
    effect_readback: Any,
    receipt: Any,
    authority: Any,
) -> dict[str, Any]:
    """Return an evidence-bound verdict without performing any side effect."""
    contract_errors = validate_case(case)
    if contract_errors:
        return {
            "status": "UNOBSERVED",
            "reason": "case_contract_invalid",
            "contract_errors": contract_errors,
        }
    if not _is_object(execution) or execution.get("observed") is not True:
        return {"status": "UNOBSERVED", "reason": "execution_unobserved"}
    for field in ("eval_id", "skill_id", "skill_version", "run_id", "execution_id", "attempt_id"):
        if not isinstance(execution.get(field), str) or not execution[field].strip():
            return {"status": "UNOBSERVED", "reason": f"execution_{field}_unobserved"}
    if (
        execution["eval_id"] != case["eval_id"]
        or execution["skill_id"] != case["skill_id"]
        or execution["skill_version"] != case["skill_version"]
    ):
        return {"status": "UNOBSERVED", "reason": "execution_identity_mismatch"}
    evidence_gate = evaluate_evidence_gate(
        case=case, execution=execution, evidence=evidence, receipt=receipt
    )
    if evidence_gate["status"] != "OBSERVED":
        return evidence_gate
    if not _is_object(effect_readback) or effect_readback.get("observed") is not True:
        return {"status": "UNOBSERVED", "reason": "effect_readback_unobserved"}

    authority_leakage = bool(
        _is_object(authority)
        and (
            authority.get("execution_authority") is True
            or authority.get("hyo_do_granted_execution") is True
        )
    )
    inferred_from_label = execution.get("inferred_owner_from_label") is True
    expected_owner = case["expected_behavior"].get("owner")
    owner_mismatch = isinstance(expected_owner, str) and execution.get("owner") != expected_owner
    reason = (
        "authority_leakage"
        if authority_leakage
        else "owner_inferred_from_label"
        if inferred_from_label
        else "runtime_owner_mismatch"
        if owner_mismatch
        else None
    )
    return {
        "status": "FAIL" if reason else "PASS",
        "reason": reason,
        "false_green": False,
        "authority_leakage": authority_leakage,
        "runtime_owner": execution.get("owner"),
        "effect_readback": "observed",
        "receipt_success": bool(_is_object(receipt) and receipt.get("success") is True),
    }
