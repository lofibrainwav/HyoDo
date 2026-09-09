"""Compact check output must preserve the sampled measurement boundary."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app


@pytest.mark.parametrize("general", [False, True], ids=["fallback", "explicit"])
@pytest.mark.parametrize("output", ["--json", "--quiet"])
@pytest.mark.parametrize("exit_code", [0, 1, 2], ids=["pass", "fail", "empty"])
def test_sampled_check_discloses_scope(
    tmp_path: Path, general: bool, output: str, exit_code: int
) -> None:
    if exit_code != 2:
        (tmp_path / "sample.sh").write_text("echo ok\n" if exit_code == 0 else "if then\n")
    args = ["check", str(tmp_path), output]
    if general:
        args.append("--general")

    result = CliRunner().invoke(app, args)

    assert result.exit_code == exit_code, result.output
    if output == "--json":
        payload = json.loads(result.output)
        assert payload["status"] == {0: "PASS", 1: "FAIL", 2: "UNOBSERVED"}[exit_code]
        assert payload["sampled"] is True
        assert payload["scope"] == "sampled_syntax"
        assert "50 files per language" in payload["limitation"]
        assert "not a full-project validation" in payload["limitation"]
        disclosure = payload["verdict"]
    else:
        disclosure = result.output
    assert "sampled" in disclosure.lower()
    assert "50 files per language" in disclosure
    assert "not a full-project validation" in disclosure


@pytest.mark.parametrize("output", ["--json", "--quiet"])
def test_byog_check_is_not_labelled_sampled(tmp_path: Path, output: str) -> None:
    config_dir = tmp_path / ".hyodo"
    config_dir.mkdir()
    (config_dir / "gates.toml").write_text(
        'schema = "hyodo.gates/v1"\n[gates.ok]\npillar = "goodness"\ncommand = "true"\n'
    )

    result = CliRunner().invoke(app, ["check", str(tmp_path), output])

    assert result.exit_code == 0, result.output
    assert "sampled" not in result.output.lower()
    assert "not a full-project validation" not in result.output
    if output == "--json":
        assert json.loads(result.output)["gates_ran"] == 1
