from __future__ import annotations

import json
import subprocess
from pathlib import Path

from hyodo.six_lens_runtime import LENSES, measure_six_lenses, measure_workspace_six_lenses


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
    assert result["projection_status"] == "EXPERIMENTAL"
    assert result["experimental_dimensions"]["impact"] == "UNOBSERVED"
    benevolence = next(plate for plate in result["plates"] if plate["lens"] == "benevolence")
    assert benevolence["state"] == "UNOBSERVED"
    assert "evidence_unobserved" in benevolence["residuals"]
    assert result["experimental_projection"]["truth"] == [
        "freshness",
        "provenance",
        "reproducibility",
    ]
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


def test_unrelated_evidence_is_residual_not_cross_lens_atom() -> None:
    result = measure_six_lenses(
        {"exact_artifact_sha": "c" * 40, "freshness": "fresh", "safety": "observed"}
    )
    truth = next(plate for plate in result["plates"] if plate["lens"] == "truth")
    assert {atom["key"] for atom in truth["evidence_atoms"]} == {"freshness"}
    assert truth["residuals"].count("unrelated_evidence:safety") == 1


def test_measure_workspace_six_lenses_observes_all_six_from_local_receipts(
    tmp_path: Path,
) -> None:
    from hyodo.events import append_agent_event

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()

    # 1. Empty workspace with no .hyodo receipts -> all 6 plates are UNOBSERVED
    empty_measurement = measure_workspace_six_lenses(repo)
    assert empty_measurement["exact_artifact_sha"] == sha
    assert all(p["state"] == "UNOBSERVED" for p in empty_measurement["plates"])

    # 2. Populate local deterministic receipts (untracked in .gitignore so tree stays clean)
    (repo / ".gitignore").write_text(".hyodo/\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "ignore hyodo"], cwd=repo, check=True)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()

    hyodo_dir = repo / ".hyodo"
    hyodo_dir.mkdir()
    history_entry = {
        "provenance": {
            "target_commit": sha,
            "target_dirty": False,
            "validity": "OBSERVED",
            "relation": "BYOG_PROJECT",
        },
        "input_digest": {"before": "d" * 64, "after": "d" * 64},
        "gates": {
            "unit": {"pillar": "truth", "status": "PASS"},
            "security": {"pillar": "goodness", "status": "PASS"},
            "lint": {"pillar": "beauty", "status": "PASS"},
        },
    }
    (hyodo_dir / "history.jsonl").write_text(json.dumps(history_entry) + "\n", encoding="utf-8")
    (hyodo_dir / "gates-trust.json").write_text(json.dumps({"digest": "e" * 64}), encoding="utf-8")
    append_agent_event(
        repo,
        {
            "schema_version": "hyodo.agent-event/v1",
            "event_id": "00000000-0000-4000-8000-000000000001",
            "run_id": "00000000-0000-4000-8000-0000000000aa",
            "ts": "2026-11-13T00:00:00+00:00",
            "kind": "model_response",
            "step_index": 0,
            "actor": "agent",
            "tool": None,
            "io": {
                "input_digest": "111111111111",
                "output_digest": "222222222222",
                "bytes_in": 10,
                "bytes_out": 20,
            },
            "policy": {"decision": "ALLOW", "rule_id": "default", "reason": "ok"},
            "meta": {"model": "jev-shadow", "tags": ["no-execution-authority"]},
        },
    )

    observed_measurement = measure_workspace_six_lenses(repo)
    assert observed_measurement["exact_artifact_sha"] == sha
    assert observed_measurement["authority"] == "UNOBSERVED"
    states = {p["lens"]: p["state"] for p in observed_measurement["plates"]}
    assert states == {
        "truth": "OBSERVED",
        "goodness": "OBSERVED",
        "beauty": "OBSERVED",
        "benevolence": "OBSERVED",
        "hyo": "OBSERVED",
        "eternity": "OBSERVED",
    }
