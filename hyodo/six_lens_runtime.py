"""Candidate six-lens runtime assembled from nursery components."""

from __future__ import annotations

from typing import Any

from hyodo.evidence_plate import (
    LENSES,
    extract_evidence_atoms,
    extract_lens_evidence,
    make_evidence_plate,
)

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
EXPERIMENTAL_PROJECTION = {
    "truth": ("freshness", "provenance", "reproducibility"),
    "goodness": ("safety",),
    "beauty": ("clarity",),
    "benevolence": ("impact",),
    "hyo": ("consent",),
    "eternity": ("continuity",),
}


def _artifact(value: Any) -> bool:
    """Validate the output binding without reimplementing atom extraction."""
    return (
        isinstance(value, str)
        and len(value) in {40, 64}
        and all(char in "0123456789abcdef" for char in value.lower())
    )


def measure_six_lenses(evidence: dict[str, Any]) -> dict[str, Any]:
    """Produce six independent evidence projections with explicit residuals."""
    artifact = evidence.get("exact_artifact_sha")
    atoms = extract_evidence_atoms(evidence)
    dimensions = {name: evidence.get(name, "UNOBSERVED") for name in DIMENSIONS}
    plates = []
    for lens in LENSES:
        selected, extraction_residuals = extract_lens_evidence(atoms, lens)
        plate = make_evidence_plate(evidence, lens)
        plate["residuals"] = [*plate["residuals"], *extraction_residuals]
        if not selected:
            plate["residuals"].append("evidence_unobserved")
            plate["state"] = "UNOBSERVED"
        plates.append(plate)
    return {
        "schema_version": "hyodo.six-lens-measurement/v1",
        "exact_artifact_sha": artifact if _artifact(artifact) else "UNOBSERVED",
        "plates": plates,
        "projection_status": "EXPERIMENTAL",
        "experimental_dimensions": dimensions,
        "experimental_projection": {
            lens: list(keys) for lens, keys in EXPERIMENTAL_PROJECTION.items()
        },
        "components": [
            "C1:isolated-judges",
            "C2:shared-atoms",
            "C3:dimension-projection",
            "CX:unknown-preserved",
        ],
        "authority": "UNOBSERVED",
    }
