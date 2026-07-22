"""TDD contracts for the local golden-dataset evaluation harness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()


def _write_runner(path: Path, body: str) -> str:
    path.write_text(body, encoding="utf-8")
    return f"{sys.executable} {path}"


def _write_dataset(path: Path, cases: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(case, sort_keys=True) for case in cases) + "\n",
        encoding="utf-8",
    )


def test_eval_records_deterministic_scoring_results_and_ledger(tmp_path: Path) -> None:
    dataset = tmp_path / "golden.jsonl"
    _write_dataset(
        dataset,
        [
            {"id": "exact", "input": {"actual": "ready"}, "expected": "ready", "scoring": "exact"},
            {
                "id": "contains",
                "input": {"actual": "ready to ship"},
                "expected": "ship",
                "scoring": "contains",
            },
            {
                "id": "json-path",
                "input": {"actual": {"items": [{"status": "ready"}]}},
                "expected": {"path": "$.items[0].status", "value": "ready"},
                "scoring": "json_path",
            },
            {
                "id": "custom",
                "input": {"actual": {"score": 9}},
                "expected": {"path": "$.score", "operator": "gte", "value": 8},
                "scoring": "custom",
            },
        ],
    )
    command = _write_runner(
        tmp_path / "runner.py",
        "import json, sys\ncase = json.load(sys.stdin)\nprint(json.dumps({'output': case['input']['actual']}))\n",
    )

    result = runner.invoke(
        app,
        ["eval", "--dataset", str(dataset), "--runner", command, "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0
    summary = json.loads(result.output)
    assert summary["status"] == "PASS"
    assert summary["pass_rate"] == 1.0
    report_path = tmp_path / summary["result_path"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert [case["passed"] for case in report["cases"]] == [True, True, True, True]
    assert report["ledger_path"] == ".hyodo/eval-runs.jsonl"
    ledger = tmp_path / report["ledger_path"]
    assert (
        json.loads(ledger.read_text(encoding="utf-8").splitlines()[-1])["run_id"]
        == report["run_id"]
    )


def test_eval_runner_failure_is_a_failed_run_not_a_skip(tmp_path: Path) -> None:
    dataset = tmp_path / "golden.jsonl"
    _write_dataset(dataset, [{"id": "case-1", "input": "x", "expected": "x", "scoring": "exact"}])
    command = _write_runner(tmp_path / "broken.py", "import sys\nsys.exit(7)\n")

    result = runner.invoke(
        app,
        ["eval", "--dataset", str(dataset), "--runner", command, "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 1
    summary = json.loads(result.output)
    assert summary["status"] == "FAIL"
    assert summary["runner_failure"]["returncode"] == 7
    report = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    assert report["status"] == "FAIL"
    assert report["runner_failure"]["case_id"] == "case-1"


def test_eval_missing_dataset_is_unobserved_input(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "eval",
            "--dataset",
            str(tmp_path / "missing.jsonl"),
            "--runner",
            f"{sys.executable} -c pass",
            "--root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 2
    assert json.loads(result.output)["status"] == "UNOBSERVED"
