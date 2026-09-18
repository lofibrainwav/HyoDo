"""Canonical evidence atoms and lens evidence plates.

This module measures observed evidence only. It never produces scores,
authorization, routing, or execution decisions.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

LENSES = ("truth", "goodness", "beauty", "benevolence", "hyo", "eternity")
_FORBIDDEN = frozenset({"authority", "approval", "merge", "route", "score", "decision"})
_SHA_LENGTHS = {40, 64}

# Public v1 extraction contract.  Keys absent from a lens are not silently
# reused: the plate records them as residuals instead.
LENS_ALLOWED_EVIDENCE = {
    "truth": frozenset({"freshness", "provenance", "reproducibility"}),
    "goodness": frozenset({"safety"}),
    "beauty": frozenset({"clarity"}),
    "benevolence": frozenset({"impact"}),
    "hyo": frozenset({"consent"}),
    "eternity": frozenset({"continuity"}),
}
LEGITIMATE_DEPENDENCIES = {"exact_artifact_sha"}


def _valid_artifact_sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) in _SHA_LENGTHS
        and all(char in "0123456789abcdef" for char in value.lower())
    )


def extract_evidence_atoms(envelope: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract deterministic, authority-free atoms from one evidence envelope."""
    artifact_sha = envelope.get("exact_artifact_sha")
    if not _valid_artifact_sha(artifact_sha):
        return []
    atoms: list[dict[str, Any]] = []
    for key in sorted(envelope):
        if key in {"exact_artifact_sha", "source", *_FORBIDDEN}:
            continue
        value = envelope[key]
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
        atom_id = hashlib.sha256(f"{artifact_sha}:{key}:{encoded}".encode()).hexdigest()
        atoms.append({"atom_id": atom_id, "key": key, "value": value})
    return atoms


def extract_lens_evidence(
    atoms: list[dict[str, Any]], lens: str
) -> tuple[list[dict[str, Any]], list[str]]:
    """Project only contract-allowed atoms and expose leakage as residuals."""
    if lens not in LENSES:
        return [], ["unknown_lens"]
    allowed = LENS_ALLOWED_EVIDENCE[lens]
    selected = [atom for atom in atoms if atom.get("key") in allowed]
    residuals = [
        f"unrelated_evidence:{atom.get('key')}"
        for atom in atoms
        if atom.get("key") not in allowed and atom.get("key") not in _FORBIDDEN
    ]
    return selected, residuals


def make_evidence_plate(
    envelope: dict[str, Any], lens: str, *, observed_at: str | None = None
) -> dict[str, Any]:
    """Build a schema-shaped evidence plate; the plate grants no authority."""
    artifact_sha = envelope.get("exact_artifact_sha")
    atoms = extract_evidence_atoms(envelope)
    selected, residuals = extract_lens_evidence(atoms, lens)
    if not _valid_artifact_sha(artifact_sha):
        residuals = [*residuals, "artifact_sha_unobserved"]
    # An observed plate may still carry residuals.  Residuals describe
    # excluded or unresolved inputs; they must not be silently promoted, but
    # they also must not erase an independently observed allowed signal.
    state = "OBSERVED" if selected and _valid_artifact_sha(artifact_sha) else "UNOBSERVED"
    return {
        "schema_version": "hyodo.evidence-plate/v1",
        "lens": lens,
        "state": state,
        "exact_artifact_sha": artifact_sha if _valid_artifact_sha(artifact_sha) else "UNOBSERVED",
        "observed_at": observed_at or envelope.get("observed_at", "UNOBSERVED"),
        "evidence_atoms": selected,
        "authority": "UNOBSERVED",
        "legitimate_dependencies": sorted(LEGITIMATE_DEPENDENCIES),
        "residuals": residuals,
    }
