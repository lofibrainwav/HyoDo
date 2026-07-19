"""Tests for `hyodo safe --json` CLI output.

These pin the `--json` branch added to the `safe` command in
`hyodo/cli/main.py`: the emitted payload must be a single parseable JSON
document, and its `exit_code` must match the text-mode exit code for the same
scan result (0 default, 1 on `--strict` + high-severity finding, 2 on a
missing/unreadable path). The scan engine itself (`hyodo/safety.py`) is
covered by `tests/test_safety*.py` and is out of scope here.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()

# AKIA + 16 uppercase/digit chars — matches SECRET_PATTERNS["aws_access_key"].
FAKE_AWS_KEY = "AKIAABCDEFGHIJKLMNOP"


def _secret_file(tmp_path):
    sample = tmp_path / "leaked.txt"
    sample.write_text(f"aws_key = {FAKE_AWS_KEY}\n", encoding="utf-8")
    return sample


def test_safe_json_emits_parseable_json(tmp_path):
    sample = _secret_file(tmp_path)

    result = runner.invoke(app, ["safe", "--json", str(sample)])

    payload = json.loads(result.output)
    assert payload["source"].startswith("file:")
    assert any(f["category"] == "secret" and f["severity"] == "high" for f in payload["findings"])


def test_safe_json_exit_codes_match_text(tmp_path):
    sample = _secret_file(tmp_path)
    missing = tmp_path / "does-not-exist.txt"

    json_strict = runner.invoke(app, ["safe", "--json", "--strict", str(sample)])
    text_strict = runner.invoke(app, ["safe", "--strict", str(sample)])
    assert json_strict.exit_code == 1
    assert text_strict.exit_code == 1
    assert json_strict.exit_code == text_strict.exit_code

    json_default = runner.invoke(app, ["safe", "--json", str(sample)])
    text_default = runner.invoke(app, ["safe", str(sample)])
    assert json_default.exit_code == 0
    assert text_default.exit_code == 0
    assert json_default.exit_code == text_default.exit_code

    json_missing = runner.invoke(app, ["safe", "--json", str(missing)])
    text_missing = runner.invoke(app, ["safe", str(missing)])
    assert json_missing.exit_code == 2
    assert text_missing.exit_code == 2
    assert json_missing.exit_code == text_missing.exit_code

    # The payload's self-reported exit_code field must agree with the process exit code.
    assert json.loads(json_strict.output)["exit_code"] == json_strict.exit_code
    assert json.loads(json_default.output)["exit_code"] == json_default.exit_code
    assert json.loads(json_missing.output)["exit_code"] == json_missing.exit_code


def test_safe_json_no_extra_stdout(tmp_path):
    sample = _secret_file(tmp_path)

    result = runner.invoke(app, ["safe", "--json", str(sample)])

    # json.loads succeeding on the full output proves nothing else (banners,
    # panels, extra prints) shares stdout with the JSON document.
    payload = json.loads(result.output)
    assert isinstance(payload, dict)
    assert result.output.strip().startswith("{")
    assert result.output.strip().endswith("}")
