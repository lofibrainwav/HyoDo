"""Fail-closed state transitions for release orchestration receipts."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from itertools import pairwise
from typing import Any

RELEASE_STATES = (
    "OBSERVED",
    "PLANNED",
    "AUTHORIZED",
    "APPLIED",
    "VERIFIED",
    "PUSHED",
    "PR_OPEN",
    "REMOTE_GATED",
    "MERGED",
    "PUBLISHED",
    "READBACK_VERIFIED",
)

ALLOWED_TRANSITIONS: dict[str, str] = {
    "OBSERVED": "PLANNED",
    "PLANNED": "AUTHORIZED",
    "AUTHORIZED": "APPLIED",
    "APPLIED": "VERIFIED",
    "VERIFIED": "PUSHED",
    "PUSHED": "PR_OPEN",
    "PR_OPEN": "REMOTE_GATED",
    "REMOTE_GATED": "MERGED",
    "MERGED": "PUBLISHED",
    "PUBLISHED": "READBACK_VERIFIED",
}


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _entry(state: str, evidence: str, observed_at: str | None = None) -> dict[str, str]:
    if state not in RELEASE_STATES:
        raise ValueError(f"unknown release state: {state}")
    if not evidence.strip():
        raise ValueError(f"{state}: evidence is required")
    return {"state": state, "evidence": evidence, "observed_at": observed_at or _now()}


def start_receipt(plan: dict[str, Any]) -> dict[str, Any]:
    """Convert a passing plan into a PLANNED receipt without writing state."""
    if plan.get("schema") != "hyodo.release-plan/v1":
        raise ValueError("receipt requires a hyodo.release-plan/v1 plan")
    if plan.get("result") != "PASS":
        raise ValueError("only a passing plan can enter PLANNED")
    receipt = deepcopy(plan)
    evidence = f"plan {plan['release_id']} @ {plan['candidate_sha']}"
    receipt["schema"] = "hyodo.release-receipt/v1"
    receipt["state"] = "PLANNED"
    receipt["history"] = [
        _entry("OBSERVED", f"source readback @ {plan['candidate_sha']}"),
        _entry("PLANNED", evidence),
    ]
    receipt["residuals"] = []
    receipt["final_state"] = "PLANNED"
    return receipt


def transition(receipt: dict[str, Any], target: str, evidence: str) -> dict[str, Any]:
    """Advance exactly one allowed state, requiring target-bound evidence."""
    current = receipt.get("state")
    if current not in ALLOWED_TRANSITIONS:
        raise ValueError(f"no transition allowed from {current!r}")
    expected = ALLOWED_TRANSITIONS[current]
    if target != expected:
        raise ValueError(f"invalid release transition: {current} -> {target}; expected {expected}")
    updated = deepcopy(receipt)
    updated["history"].append(_entry(target, evidence))
    updated["state"] = target
    updated["final_state"] = target
    return updated


def validate_receipt(receipt: dict[str, Any]) -> None:
    """Validate a receipt's state and contiguous transition history."""
    if receipt.get("schema") != "hyodo.release-receipt/v1":
        raise ValueError("unexpected release receipt schema")
    history = receipt.get("history")
    if not isinstance(history, list) or not history:
        raise ValueError("release receipt history is required")
    states = [entry.get("state") for entry in history]
    if states[0] != "OBSERVED":
        raise ValueError("release receipt must begin at OBSERVED")
    for previous, current in pairwise(states):
        if ALLOWED_TRANSITIONS.get(previous) != current:
            raise ValueError(f"invalid release history transition: {previous} -> {current}")
    for entry in history:
        _entry(entry["state"], entry.get("evidence", ""), entry.get("observed_at"))
    if receipt.get("state") != states[-1] or receipt.get("final_state") != states[-1]:
        raise ValueError("receipt state does not match its history")
