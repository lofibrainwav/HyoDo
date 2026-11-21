"""Paired comparison of two ``hyodo eval`` runs on the same dataset.

Two runs are comparable only when both observed the same dataset bytes
(``dataset_sha256``) and the same case ids. Each case then forms a pair:
the candidate wins when only it passed, loses when only the baseline passed.
The exact two-sided McNemar test on the discordant pairs says whether the
difference is larger than chance. The result is evidence for a reviewer,
never a gate: it grants nothing and does not change any exit status of
``hyodo eval``.
"""

from __future__ import annotations

import json
from math import comb
from pathlib import Path
from typing import Any

from hyodo.eval import EVAL_SCHEMA_VERSION, EvalInputError

COMPARE_SCHEMA_VERSION = "hyodo.eval-compare/v1"


def load_run(path: Path) -> dict[str, Any]:
    """Load one persisted eval result, rejecting anything that is not a completed run."""
    try:
        data = path.read_bytes()
    except FileNotFoundError as exc:
        raise EvalInputError(f"eval result does not exist: {path.name}") from exc
    except OSError as exc:
        raise EvalInputError(f"eval result unreadable: {exc}") from exc
    try:
        run = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvalInputError(f"eval result is not JSON: {path.name}") from exc
    if not isinstance(run, dict) or run.get("schema_version") != EVAL_SCHEMA_VERSION:
        raise EvalInputError(f"eval result has the wrong schema: {path.name}")
    if run.get("runner_failure"):
        raise EvalInputError(f"eval run did not complete (runner failure): {path.name}")
    cases = run.get("cases")
    sha = run.get("dataset_sha256")
    if not isinstance(cases, list) or not cases or not isinstance(sha, str) or len(sha) != 64:
        raise EvalInputError(f"eval result has no observed cases or dataset hash: {path.name}")
    for case in cases:
        if (
            not isinstance(case, dict)
            or not isinstance(case.get("id"), str)
            or not isinstance(case.get("passed"), bool)
        ):
            raise EvalInputError(f"eval result has a malformed case: {path.name}")
    return run


def mcnemar_exact_p(wins: int, losses: int) -> float:
    """Exact two-sided McNemar p-value from the discordant pair counts."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2 * tail)


def compare_runs(
    baseline: dict[str, Any], candidate: dict[str, Any], *, alpha: float = 0.05
) -> dict[str, Any]:
    """Pair two completed runs case by case."""
    if baseline["dataset_sha256"] != candidate["dataset_sha256"]:
        raise EvalInputError("runs observed different datasets (dataset_sha256 differs)")
    base_cases = {c["id"]: c for c in baseline["cases"]}
    cand_cases = {c["id"]: c for c in candidate["cases"]}
    if len(base_cases) != len(baseline["cases"]) or len(cand_cases) != len(candidate["cases"]):
        raise EvalInputError("a run repeats a case id")
    if set(base_cases) != set(cand_cases):
        raise EvalInputError("runs observed different case ids")

    pairs: list[dict[str, Any]] = []
    counts = {"wins": 0, "losses": 0, "both_pass": 0, "both_fail": 0}
    tags: dict[str, dict[str, int]] = {}
    for case_id in sorted(base_cases):
        b = base_cases[case_id]["passed"]
        c = cand_cases[case_id]["passed"]
        outcome = (
            "win" if c and not b else "loss" if b and not c else "both_pass" if b else "both_fail"
        )
        counts["wins" if outcome == "win" else "losses" if outcome == "loss" else outcome] += 1
        pairs.append({"id": case_id, "baseline": b, "candidate": c, "outcome": outcome})
        case_tags = base_cases[case_id].get("tags")
        for tag in case_tags if isinstance(case_tags, list) else []:
            if not isinstance(tag, str):
                continue
            row = tags.setdefault(tag, {"cases": 0, "baseline_pass": 0, "candidate_pass": 0})
            row["cases"] += 1
            row["baseline_pass"] += int(b)
            row["candidate_pass"] += int(c)

    n = len(pairs)
    p_value = mcnemar_exact_p(counts["wins"], counts["losses"])
    if p_value < alpha and counts["wins"] > counts["losses"]:
        verdict = "CANDIDATE_BETTER"
    elif p_value < alpha and counts["losses"] > counts["wins"]:
        verdict = "CANDIDATE_WORSE"
    else:
        verdict = "NO_SIGNIFICANT_DIFFERENCE"
    return {
        "schema_version": COMPARE_SCHEMA_VERSION,
        "dataset_sha256": baseline["dataset_sha256"],
        "baseline_run_id": baseline.get("run_id"),
        "candidate_run_id": candidate.get("run_id"),
        "cases": n,
        "baseline_pass_rate": sum(1 for p in pairs if p["baseline"]) / n,
        "candidate_pass_rate": sum(1 for p in pairs if p["candidate"]) / n,
        **counts,
        "discordant": counts["wins"] + counts["losses"],
        "mcnemar_exact_p": p_value,
        "alpha": alpha,
        "verdict": verdict,
        "tags": tags,
        "pairs": pairs,
        "note": "evidence for review only; not a gate, approval or authority",
    }
