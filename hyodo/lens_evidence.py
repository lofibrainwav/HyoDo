"""Deterministic emitter for ``hyodo.lens-evidence/v1``.

One receipt per canonical lens, built only from a ``hyodo.dashboard-evidence``
envelope that already exists: the gates that ran, the lens each gate is
attributed to, and the provenance of the measurement. Nothing is measured
here, no clock is read, and the same envelope always yields the same receipt.

The receipt is evidence, never judgment. A gate that ran and failed is
*observed*; whether that is good or bad for the lens is the host's call. The
receipt never carries a score, value, weight, aggregate, or decision.

The state is honest about what the envelope can and cannot support:

- the envelope was measured at a different commit than the subject, on a
  dirty tree, or without a recorded commit  -> ``UNOBSERVED`` (stale or
  unbound provenance: the evidence does not describe this subject);
- no gate is attributed to the lens          -> ``UNOBSERVED``;
- some attributed gates observed             -> ``PARTIAL``;
- every attributed gate observed             -> ``OBSERVED``.

Only gate evidence is read in this version. ``OBSERVED`` therefore means the
lens's attributed gates ran -- proxy coverage, not coverage of the virtue.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from hyodo.virtues import CANONICAL_VIRTUE_KEYS

LENS_EVIDENCE_SCHEMA_VERSION = "hyodo.lens-evidence/v1"

# Gate outcomes that mean the gate actually ran and produced a result.
OBSERVED_GATE_STATUSES = frozenset({"PASS", "FAIL"})

_SHA = re.compile(r"^([0-9a-f]{40}|[0-9a-f]{64})$")


def _digest(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _provenance_residuals(provenance: Mapping[str, Any], subject_sha: str) -> list[str]:
    target_commit = provenance.get("target_commit")
    if not isinstance(target_commit, str) or not target_commit:
        return ["provenance_unobserved"]
    residuals: list[str] = []
    if target_commit != subject_sha:
        residuals.append("stale_provenance")
    if provenance.get("target_dirty") is not False:
        residuals.append("target_tree_not_clean")
    return residuals


def emit_lens_evidence(evidence: Mapping[str, Any], lens: str, subject_sha: str) -> dict[str, Any]:
    """Build one ``hyodo.lens-evidence/v1`` receipt for *lens* about *subject_sha*.

    Raises ``ValueError`` for a lens outside the canonical six or a subject
    that is not a full commit or artifact digest: those are caller errors,
    not observations.
    """
    if lens not in CANONICAL_VIRTUE_KEYS:
        raise ValueError(f"unknown lens: {lens!r}")
    if not _SHA.match(subject_sha):
        raise ValueError("subject_sha must be a full 40- or 64-character hex digest")

    raw_provenance = evidence.get("provenance")
    provenance = raw_provenance if isinstance(raw_provenance, Mapping) else {}
    raw_gates = evidence.get("gates")
    gates = raw_gates if isinstance(raw_gates, Mapping) else {}

    declared: list[str] = []
    observed: list[str] = []
    refs: list[dict[str, str]] = []
    residuals: list[str] = []
    for name in sorted(gates):
        row = gates[name]
        if not isinstance(row, Mapping) or row.get("pillar") != lens:
            continue
        declared.append(name)
        # In-process envelopes carry a str-valued enum; served ones a plain str.
        raw_status = row.get("status")
        status = getattr(raw_status, "value", raw_status)
        if status in OBSERVED_GATE_STATUSES:
            observed.append(name)
            refs.append({"kind": "gate", "ref": name, "digest": _digest(dict(row))})
        else:
            residuals.append(f"gate_unobserved:{name}:{status}")

    unbound = _provenance_residuals(provenance, subject_sha)
    residuals = unbound + residuals
    if not declared:
        residuals.append("no_attributed_gate")
    if unbound:
        # Gates that ran against another tree did not observe this subject:
        # neither count them as coverage nor cite them as evidence.
        observed, refs = [], []

    if unbound or not observed:
        state = "UNOBSERVED"
    elif len(observed) < len(declared):
        state = "PARTIAL"
    else:
        state = "OBSERVED"

    tool_version = provenance.get("tool_version")
    measured_at = evidence.get("measured_at")
    return {
        "schema_version": LENS_EVIDENCE_SCHEMA_VERSION,
        "lens": lens,
        "subject": {"exact_artifact_sha": subject_sha},
        "state": state,
        "coverage": {"proxies_declared": declared, "proxies_observed": observed},
        "provenance": {
            "hyodo_version": tool_version
            if isinstance(tool_version, str) and tool_version
            else "UNOBSERVED",
            "measured_by": _digest(dict(provenance)) if provenance else "UNOBSERVED",
        },
        "evidence_refs": refs,
        "residuals": residuals,
        "observed_at": measured_at
        if isinstance(measured_at, str) and measured_at
        else "UNOBSERVED",
        "authority": "UNOBSERVED",
    }


def emit_all_lens_evidence(evidence: Mapping[str, Any], subject_sha: str) -> list[dict[str, Any]]:
    """One receipt per canonical lens, in canonical order."""
    return [emit_lens_evidence(evidence, lens, subject_sha) for lens in CANONICAL_VIRTUE_KEYS]
