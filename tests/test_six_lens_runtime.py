from hyodo.six_lens_runtime import LENSES, measure_six_lenses


def test_candidate_recombines_six_lenses_and_preserves_artifact_binding() -> None:
    result = measure_six_lenses(
        {
            "exact_artifact_sha": "a" * 40,
            "freshness": "fresh",
            "provenance": "observed",
            "safety": "observed",
            "clarity": "observed",
            "impact": "UNOBSERVED",
            "consent": "observed",
            "continuity": "observed",
            "reproducibility": "observed",
        }
    )
    assert [plate["lens"] for plate in result["plates"]] == list(LENSES)
    assert all(plate["exact_artifact_sha"] == "a" * 40 for plate in result["plates"])
    assert result["authority"] == "UNOBSERVED"
    assert {"C1:isolated-judges", "C2:shared-atoms", "C3:dimension-projection"}.issubset(
        result["components"]
    )


def test_missing_artifact_and_missing_evidence_remain_unobserved() -> None:
    result = measure_six_lenses({"freshness": "fresh"})
    assert result["exact_artifact_sha"] == "UNOBSERVED"
    assert all(plate["state"] == "UNOBSERVED" for plate in result["plates"])


def test_forbidden_authority_and_score_are_not_atoms() -> None:
    result = measure_six_lenses(
        {"exact_artifact_sha": "b" * 64, "freshness": "fresh", "authority": "human", "score": 1}
    )
    keys = {atom["key"] for plate in result["plates"] for atom in plate["evidence_atoms"]}
    assert "authority" not in keys
    assert "score" not in keys
