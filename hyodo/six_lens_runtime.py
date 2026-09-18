"""Candidate six-lens runtime assembled from nursery components."""

from __future__ import annotations

import hashlib
import json
from typing import Any

LENSES = ("truth", "goodness", "beauty", "benevolence", "hyo", "eternity")
DIMENSIONS = (
    "freshness",
    "provenance",
    "safety",
    "clarity",
    "impact",
    "consent",
    "continuity",
    "reproducibility",
)
PROJECTION = {
    "truth": ("freshness", "provenance", "reproducibility"),
    "goodness": ("safety",),
    "beauty": ("clarity",),
    "benevolence": ("impact",),
    "hyo": ("consent",),
    "eternity": ("continuity",),
}


def _artifact(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) in {40, 64}
        and all(char in "0123456789abcdef" for char in value.lower())
    )


def _atoms(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    artifact = evidence.get("exact_artifact_sha")
    if not _artifact(artifact):
        return []
    result = []
    for key in sorted(evidence):
        if key in {"exact_artifact_sha", "authority", "approval", "decision", "score", "route"}:
            continue
        encoded = json.dumps(evidence[key], sort_keys=True, default=str)
        result.append(
            {
                "atom_id": hashlib.sha256(f"{artifact}:{key}:{encoded}".encode()).hexdigest(),
                "key": key,
                "value": evidence[key],
            }
        )
    return result


def measure_six_lenses(evidence: dict[str, Any]) -> dict[str, Any]:
    """Produce six independent evidence projections with explicit residuals."""
    artifact = evidence.get("exact_artifact_sha")
    atoms = _atoms(evidence)
    dimensions = {name: evidence.get(name, "UNOBSERVED") for name in DIMENSIONS}
    plates = []
    for lens in LENSES:
        selected = [atom for atom in atoms if atom["key"] in set(PROJECTION[lens])]
        residuals = [] if _artifact(artifact) else ["artifact_sha_unobserved"]
        if not selected:
            residuals.append("evidence_unobserved")
        plates.append(
            {
                "lens": lens,
                "state": "OBSERVED" if not residuals else "UNOBSERVED",
                "exact_artifact_sha": artifact if _artifact(artifact) else "UNOBSERVED",
                "dimensions": {key: dimensions[key] for key in PROJECTION[lens]},
                "evidence_atoms": selected,
                "authority": "UNOBSERVED",
                "residuals": residuals,
            }
        )
    return {
        "schema_version": "hyodo.six-lens-measurement/v1",
        "exact_artifact_sha": artifact if _artifact(artifact) else "UNOBSERVED",
        "plates": plates,
        "components": [
            "C1:isolated-judges",
            "C2:shared-atoms",
            "C3:dimension-projection",
            "CX:unknown-preserved",
        ],
        "authority": "UNOBSERVED",
    }
