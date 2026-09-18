from __future__ import annotations

import hashlib
import json
from pathlib import Path

from hyodo.evidence_plate import extract_evidence_atoms, make_evidence_plate


def test_atoms_are_exact_artifact_bound_and_authority_free() -> None:
    atoms = extract_evidence_atoms(
        {
            "exact_artifact_sha": "a" * 40,
            "source": "fixture",
            "freshness": "fresh",
            "authority": "human",
            "score": 1,
        }
    )
    assert len(atoms) == 1
    assert atoms[0]["key"] == "freshness"
    assert all(atom["atom_id"] for atom in atoms)


def test_plate_is_observed_without_becoming_a_decision() -> None:
    plate = make_evidence_plate(
        {
            "exact_artifact_sha": "b" * 64,
            "observed_at": "2026-09-18T00:00:00Z",
            "provenance": "fixture",
            "freshness": "fresh",
        },
        "truth",
    )
    assert plate["state"] == "OBSERVED"
    assert plate["authority"] == "UNOBSERVED"
    assert "decision" not in plate


def test_missing_artifact_is_unobserved() -> None:
    plate = make_evidence_plate({"freshness": "fresh"}, "truth")
    assert plate["state"] == "UNOBSERVED"
    assert "artifact_sha_unobserved" in plate["residuals"]


def test_unrelated_atoms_do_not_leak_between_lenses() -> None:
    plate = make_evidence_plate(
        {
            "exact_artifact_sha": "c" * 40,
            "freshness": "fresh",
            "safety": "observed",
            "clarity": "observed",
        },
        "truth",
    )
    assert {atom["key"] for atom in plate["evidence_atoms"]} == {"freshness"}
    assert "unrelated_evidence:safety" in plate["residuals"]
    assert "unrelated_evidence:clarity" in plate["residuals"]
    assert plate["legitimate_dependencies"] == ["exact_artifact_sha"]


def test_schema_pin_matches_public_plate_schema() -> None:
    root = Path(__file__).parents[1]
    schema = root / "schemas/evidence-plate-v1.schema.json"
    pin = json.loads((root / "schemas/evidence-plate-v1.pin.json").read_text())
    assert hashlib.sha256(schema.read_bytes()).hexdigest() == pin["digest"]
