"""TDD contracts for eval runner isolation and result provenance.

External security review found two defects in ``hyodo eval``:

1. ``--root`` was only used to decide where to write results — the runner
   subprocess itself ran wherever the CLI process happened to start, so a
   result filed under one project's ``.hyodo/eval-runs`` could actually be
   the output of code executed in a completely different directory.
2. Result records carried no provenance — no git commit, no dirty flag, no
   execution cwd — so a saved eval result could not be tied back to the
   code state that produced it.

These tests pin both fixes: the runner must observe ``cwd == root``, and a
persisted result must carry git provenance when available, and an explicit
unobserved marker (never a silent empty string or false "clean") when it is
not.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
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


def _run_git(args: list[str], cwd: Path) -> None:
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr}"


def test_runner_subprocess_executes_with_cwd_set_to_root(tmp_path: Path) -> None:
    """(a) The runner must run in --root, not wherever the CLI happened to start."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    dataset = tmp_path / "golden.jsonl"
    observed_cwd = os.path.realpath(str(project_root))
    _write_dataset(
        dataset,
        [{"id": "cwd-case", "input": "x", "expected": observed_cwd, "scoring": "exact"}],
    )
    command = _write_runner(
        tmp_path / "runner.py",
        "import json, os, sys\n"
        "json.load(sys.stdin)\n"
        "print(json.dumps({'output': os.path.realpath(os.getcwd())}))\n",
    )

    # Invoke from an unrelated cwd on purpose: if the fix regresses to the old
    # "cwd wherever the process started" behavior, this must fail.
    previous_cwd = os.getcwd()
    os.chdir(elsewhere)
    try:
        result = runner.invoke(
            app,
            [
                "eval",
                "--dataset",
                str(dataset),
                "--runner",
                command,
                "--root",
                str(project_root),
                "--json",
            ],
        )
    finally:
        os.chdir(previous_cwd)

    assert result.exit_code == 0, result.output
    summary = json.loads(result.output)
    assert summary["status"] == "PASS"
    report = json.loads((project_root / summary["result_path"]).read_text(encoding="utf-8"))
    assert report["cases"][0]["actual"] == observed_cwd
    assert report["cases"][0]["passed"] is True


def test_result_provenance_records_git_head_sha_and_dirty_state(tmp_path: Path) -> None:
    """(b) provenance carries a real git HEAD sha and a real dirty flag."""
    project_root = tmp_path / "repo"
    project_root.mkdir()
    _run_git(["init"], cwd=project_root)
    _run_git(["config", "user.email", "test@example.com"], cwd=project_root)
    _run_git(["config", "user.name", "Test"], cwd=project_root)
    tracked = project_root / "tracked.txt"
    tracked.write_text("v1\n", encoding="utf-8")
    _run_git(["add", "tracked.txt"], cwd=project_root)
    _run_git(["commit", "-m", "initial"], cwd=project_root)

    expected_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    dataset = tmp_path / "golden.jsonl"
    _write_dataset(dataset, [{"id": "case-1", "input": "x", "expected": "x", "scoring": "exact"}])
    command = _write_runner(
        tmp_path / "runner.py",
        "import json, sys\ncase = json.load(sys.stdin)\n"
        "print(json.dumps({'output': case['input']}))\n",
    )

    clean_result = runner.invoke(
        app,
        [
            "eval",
            "--dataset",
            str(dataset),
            "--runner",
            command,
            "--root",
            str(project_root),
            "--json",
        ],
    )
    assert clean_result.exit_code == 0, clean_result.output
    clean_summary = json.loads(clean_result.output)
    clean_report = json.loads(
        (project_root / clean_summary["result_path"]).read_text(encoding="utf-8")
    )
    clean_provenance = clean_report["provenance"]
    assert clean_provenance["git_head_sha"] == expected_sha
    assert clean_provenance["git_dirty"] is False
    assert clean_provenance["git_reason"] is None
    # CLI resolves --root (Path(root).resolve()) before calling run_evaluation,
    # which on macOS also collapses /var -> /private/var symlinks.
    assert clean_provenance["run_cwd"] == str(project_root.resolve())

    # Dirty the working tree and run again — the same commit, but now dirty.
    tracked.write_text("v2 (uncommitted)\n", encoding="utf-8")
    dirty_result = runner.invoke(
        app,
        [
            "eval",
            "--dataset",
            str(dataset),
            "--runner",
            command,
            "--root",
            str(project_root),
            "--json",
        ],
    )
    assert dirty_result.exit_code == 0, dirty_result.output
    dirty_summary = json.loads(dirty_result.output)
    dirty_report = json.loads(
        (project_root / dirty_summary["result_path"]).read_text(encoding="utf-8")
    )
    dirty_provenance = dirty_report["provenance"]
    assert dirty_provenance["git_head_sha"] == expected_sha
    assert dirty_provenance["git_dirty"] is True


def test_result_provenance_is_unobserved_not_silently_clean_outside_a_git_repo(
    tmp_path: Path,
) -> None:
    """(c) Outside a git repo, provenance must say "unobserved", never fake-clean."""
    project_root = tmp_path / "not-a-repo"
    project_root.mkdir()
    # Guard the test's own premise: fail loudly here, not deep inside eval.py,
    # if the sandbox ever nests tmp_path inside a real git repository.
    probe = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert probe.returncode != 0, "test premise violated: tmp_path is inside a git repository"

    dataset = tmp_path / "golden.jsonl"
    _write_dataset(dataset, [{"id": "case-1", "input": "x", "expected": "x", "scoring": "exact"}])
    command = _write_runner(
        tmp_path / "runner.py",
        "import json, sys\ncase = json.load(sys.stdin)\n"
        "print(json.dumps({'output': case['input']}))\n",
    )

    result = runner.invoke(
        app,
        [
            "eval",
            "--dataset",
            str(dataset),
            "--runner",
            command,
            "--root",
            str(project_root),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    summary = json.loads(result.output)
    report = json.loads((project_root / summary["result_path"]).read_text(encoding="utf-8"))
    provenance = report["provenance"]
    assert provenance["git_head_sha"] is None
    assert provenance["git_dirty"] is None
    assert isinstance(provenance["git_reason"], str)
    assert provenance["git_reason"]
    assert provenance["run_cwd"] == str(project_root.resolve())
