"""Contracts for `hyodo eval-compare`: paired, same-dataset, never a gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.eval import EVAL_SCHEMA_VERSION, EvalInputError
from hyodo.eval_compare import compare_runs, load_run, mcnemar_exact_p

runner = CliRunner()
SHA = "a" * 64


def _run(passed: dict[str, bool], *, sha: str = SHA, tags=None, **extra) -> dict:
    return {
        "schema_version": EVAL_SCHEMA_VERSION,
        "run_id": extra.pop("run_id", "r"),
        "dataset_sha256": sha,
        "cases": [
            {"id": cid, "passed": ok, "tags": (tags or {}).get(cid, [])}
            for cid, ok in passed.items()
        ],
        **extra,
    }


def _write(tmp_path: Path, name: str, run: dict) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(run), encoding="utf-8")
    return path


def test_exact_mcnemar_matches_known_values() -> None:
    assert mcnemar_exact_p(0, 0) == 1.0
    assert mcnemar_exact_p(1, 0) == 1.0
    assert mcnemar_exact_p(6, 0) == pytest.approx(0.03125)
    assert mcnemar_exact_p(0, 6) == pytest.approx(0.03125)
    assert mcnemar_exact_p(8, 2) == pytest.approx(0.109375)


def test_pairs_count_wins_losses_and_tags() -> None:
    base = _run({"a": False, "b": True, "c": True, "d": False}, tags={"a": ["live"], "b": ["live"]})
    cand = _run({"a": True, "b": True, "c": False, "d": False})
    out = compare_runs(base, cand)
    assert (out["wins"], out["losses"], out["both_pass"], out["both_fail"]) == (1, 1, 1, 1)
    assert out["verdict"] == "NO_SIGNIFICANT_DIFFERENCE"
    assert out["tags"]["live"] == {"cases": 2, "baseline_pass": 1, "candidate_pass": 2}
    assert out["note"].startswith("evidence for review only")


def test_large_one_sided_gain_is_significant() -> None:
    ids = [f"c{i}" for i in range(8)]
    out = compare_runs(_run(dict.fromkeys(ids, False)), _run(dict.fromkeys(ids, True)))
    assert out["verdict"] == "CANDIDATE_BETTER"
    assert out["mcnemar_exact_p"] < 0.05


@pytest.mark.parametrize(
    ("base", "cand", "reason"),
    [
        (_run({"a": True}), _run({"a": True}, sha="b" * 64), "different datasets"),
        (_run({"a": True}), _run({"b": True}), "different case ids"),
    ],
)
def test_incomparable_runs_are_refused(base: dict, cand: dict, reason: str) -> None:
    with pytest.raises(EvalInputError, match=reason):
        compare_runs(base, cand)


@pytest.mark.parametrize(
    "run",
    [
        {"schema_version": "other", "dataset_sha256": SHA, "cases": [{"id": "a", "passed": True}]},
        _run({"a": True}, runner_failure={"code": "runner_exit"}),
        _run({}),
        {**_run({"a": True}), "cases": [{"id": "a", "passed": 1}]},
    ],
)
def test_incomplete_or_malformed_runs_are_unobserved(tmp_path: Path, run: dict) -> None:
    with pytest.raises(EvalInputError):
        load_run(_write(tmp_path, "r.json", run))


def test_cli_reports_and_never_gates(tmp_path: Path) -> None:
    base = _write(tmp_path, "b.json", _run({"a": False, "b": True}))
    cand = _write(tmp_path, "c.json", _run({"a": True, "b": False}))
    result = runner.invoke(
        app, ["eval-compare", "--baseline", str(base), "--candidate", str(cand), "--json"]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "hyodo.eval-compare/v1"
    assert payload["verdict"] == "NO_SIGNIFICANT_DIFFERENCE"


def test_cli_mismatch_is_unobserved_exit_2(tmp_path: Path) -> None:
    base = _write(tmp_path, "b.json", _run({"a": True}))
    cand = _write(tmp_path, "c.json", _run({"a": True}, sha="c" * 64))
    result = runner.invoke(app, ["eval-compare", "--baseline", str(base), "--candidate", str(cand)])
    assert result.exit_code == 2
    assert "UNOBSERVED" in result.output
