"""TDD contracts for the local golden-dataset evaluation harness."""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()


def _write_runner(path: Path, body: str) -> str:
    path.write_text(body, encoding="utf-8")
    # shlex.quote handles paths with spaces (e.g. pipx venv under
    # "~/Library/Application Support/..." on macOS).
    return f"{shlex.quote(sys.executable)} {shlex.quote(str(path))}"


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


def _invalid_id_case(bad_id: object) -> dict[str, object]:
    return {"id": bad_id, "input": "a", "expected": "a", "scoring": "exact"}


def test_eval_invalid_id_names_the_offending_value_and_stays_unobserved(tmp_path: Path) -> None:
    dataset = tmp_path / "golden.jsonl"
    _write_dataset(dataset, [_invalid_id_case(["not", "a", "string"])])
    args = [
        "eval",
        "--dataset",
        str(dataset),
        "--runner",
        f"{sys.executable} -c pass",
        "--root",
        str(tmp_path),
    ]

    human = runner.invoke(app, args)
    machine = runner.invoke(app, [*args, "--json"])

    # Fail-visible semantics are unchanged: UNOBSERVED, exit 2, never PASS.
    assert human.exit_code == 2
    assert machine.exit_code == 2
    assert json.loads(machine.output)["status"] == "UNOBSERVED"
    reason = json.loads(machine.output)["reason"]
    assert reason.startswith("dataset line 1 has invalid id")
    assert "['not', 'a', 'string'] (list)" in reason
    assert "non-empty string" in reason
    # Bracketed values must survive Rich markup in the human surface.
    assert "['not', 'a', 'string'] (list)" in human.output.replace("\n", "")


def test_eval_invalid_id_variants_are_not_repaired(tmp_path: Path) -> None:
    for bad_id, shown in [(42, "42 (int)"), ("   ", "'   ' (str)"), (None, "None (NoneType)")]:
        dataset = tmp_path / "golden.jsonl"
        _write_dataset(dataset, [_invalid_id_case(bad_id)])
        result = runner.invoke(
            app,
            [
                "eval",
                "--dataset",
                str(dataset),
                "--runner",
                f"{sys.executable} -c pass",
                "--root",
                str(tmp_path),
                "--json",
            ],
        )
        assert result.exit_code == 2
        assert shown in json.loads(result.output)["reason"]


def test_eval_invalid_id_value_is_bounded(tmp_path: Path) -> None:
    dataset = tmp_path / "golden.jsonl"
    _write_dataset(dataset, [_invalid_id_case(["x" * 500])])
    result = runner.invoke(
        app,
        [
            "eval",
            "--dataset",
            str(dataset),
            "--runner",
            f"{sys.executable} -c pass",
            "--root",
            str(tmp_path),
            "--json",
        ],
    )
    assert result.exit_code == 2
    assert len(json.loads(result.output)["reason"]) < 200
