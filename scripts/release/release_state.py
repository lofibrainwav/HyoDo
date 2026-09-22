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
    # Publication. v4.21.2 went MERGED -> tag -> published Release by hand, with
    # no draft and no evidence, and immutable releases made that permanent. Each
    # step now has its own state, and PUBLISHED is reachable only from a draft
    # whose SBOM evidence was attached and verified.
    "TAGGED",
    "DRAFT_CREATED",
    "EVIDENCE_BUILT",
    "EVIDENCE_ATTACHED",
    "DRAFT_VERIFIED",
    "PUBLISHED",
    "PYPI_PUBLISHED",
    "PROVENANCE_VERIFIED",
    "INSTALL_VERIFIED",
    "READBACK_VERIFIED",
)

# Strictly linear: every state has exactly one successor, so no stage can be
# skipped and no irreversible step can be reached early.
ALLOWED_TRANSITIONS: dict[str, str] = dict(pairwise(RELEASE_STATES))

# A publication receipt starts from an already merged release candidate.
RECEIPT_START_STATES = ("OBSERVED", "MERGED")


class ReleaseOrderError(ValueError):
    """Raised when a release action is attempted from the wrong state."""


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


def start_publication_receipt(version: str, merged_sha: str, evidence: str) -> dict[str, Any]:
    """Start the publication half of a release at MERGED, bound to one main SHA."""
    if not merged_sha or len(merged_sha) != 40:
        raise ValueError("publication requires the full merged main SHA")
    return {
        "schema": "hyodo.release-receipt/v1",
        "phase": "publication",
        "version": version,
        "tag": f"v{version}",
        "merged_sha": merged_sha,
        "state": "MERGED",
        "final_state": "MERGED",
        "history": [_entry("MERGED", evidence)],
        "residuals": [],
    }


def require_state(receipt: dict[str, Any], expected: str, action: str) -> None:
    """Refuse an action unless the receipt is exactly in ``expected``."""
    current = receipt.get("state")
    if current != expected:
        raise ReleaseOrderError(f"{action} requires {expected}; receipt is at {current}")


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
    if states[0] not in RECEIPT_START_STATES:
        raise ValueError("release receipt must begin at OBSERVED or, for publication, MERGED")
    for previous, current in pairwise(states):
        if ALLOWED_TRANSITIONS.get(previous) != current:
            raise ValueError(f"invalid release history transition: {previous} -> {current}")
    for entry in history:
        _entry(entry["state"], entry.get("evidence", ""), entry.get("observed_at"))
    if receipt.get("state") != states[-1] or receipt.get("final_state") != states[-1]:
        raise ValueError("receipt state does not match its history")
