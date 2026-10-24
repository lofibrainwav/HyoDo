"""A strict handoff consumer cannot interpret partial observation as success."""

import json

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app


@pytest.mark.parametrize("json_mode", [False, True])
def test_strict_partial_scan_exits_two(tmp_path, json_mode):
    for i in range(41):
        (tmp_path / f"{i:02}.py").write_text("# no secrets\n")
    args = ["safe", str(tmp_path), "--strict", "--max-files", "40"]
    if json_mode:
        args.append("--json")
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 2, result.output
    if json_mode:
        payload = json.loads(result.output)
        assert payload["coverage"] == "PARTIAL"
        assert payload["exit_code"] == 2


def test_strict_full_scan_can_pass(tmp_path):
    (tmp_path / "ok.py").write_text("# no secrets\n")
    result = CliRunner().invoke(app, ["safe", str(tmp_path), "--strict", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["coverage"] == "FULL"


def test_advisory_partial_remains_advisory(tmp_path):
    for i in range(2):
        (tmp_path / f"{i}.py").write_text("# no secrets\n")
    result = CliRunner().invoke(app, ["safe", str(tmp_path), "--max-files", "1", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output)["coverage"] == "PARTIAL"
