"""A capped directory scan must not read as a clean pass.

`hyodo safe <dir>` defaults to `--max-files 40`. When a directory has more
scannable files than the cap, `run_safety_scan` correctly reports
`coverage: PARTIAL`, but the CLI verdict line still opened with
`HYODO PASS`, indistinguishable from a real full-coverage pass. A reader
(or a CI gate reading only the last line) could not tell 40/161 files
observed apart from 161/161. This pins the fix: a PARTIAL-coverage verdict
must not start with `HYODO PASS`, must say how many files were left
unobserved, and must point at `--max-files 0`. Full-coverage and
missing-path outcomes, and the existing exit-code contract, must be
unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()


def _make_dir_with_n_files(tmp_path: Path, n: int) -> Path:
    target = tmp_path / "corpus"
    target.mkdir()
    for i in range(n):
        (target / f"file_{i}.py").write_text(f"value = {i}\n", encoding="utf-8")
    return target


def test_capped_directory_scan_verdict_is_not_pass(tmp_path):
    target = _make_dir_with_n_files(tmp_path, 5)

    result = runner.invoke(app, ["safe", str(target), "--max-files", "2"])

    assert result.exit_code == 0  # default mode still an early-warning, not a gate failure
    verdict_line = result.output.splitlines()[-1]
    assert not verdict_line.startswith("HYODO PASS")
    assert "HYODO PARTIAL" in verdict_line
    # Must say how many files were left unscanned, not just the ratio.
    assert "3" in verdict_line  # 5 total - 2 scanned = 3 unscanned
    assert "--max-files 0" in verdict_line


def test_capped_directory_scan_json_verdict_is_not_pass(tmp_path):
    target = _make_dir_with_n_files(tmp_path, 5)

    result = runner.invoke(app, ["safe", "--json", str(target), "--max-files", "2"])

    payload = json.loads(result.output)
    assert payload["coverage"] == "PARTIAL"
    assert not payload["verdict"].startswith("HYODO PASS")
    assert "HYODO PARTIAL" in payload["verdict"]
    assert result.exit_code == 0


def test_uncapped_directory_scan_still_passes(tmp_path):
    target = _make_dir_with_n_files(tmp_path, 5)

    result = runner.invoke(app, ["safe", str(target), "--max-files", "0"])

    assert result.exit_code == 0
    verdict_line = result.output.splitlines()[-1]
    assert verdict_line.startswith("HYODO PASS")


def test_single_file_scan_is_unaffected(tmp_path):
    sample = tmp_path / "clean.py"
    sample.write_text("value = 1\n", encoding="utf-8")

    result = runner.invoke(app, ["safe", str(sample)])

    assert result.exit_code == 0
    verdict_line = result.output.splitlines()[-1]
    assert verdict_line.startswith("HYODO PASS")


def test_missing_path_is_unaffected(tmp_path):
    result = runner.invoke(app, ["safe", str(tmp_path / "does-not-exist")])

    assert result.exit_code == 2
    verdict_line = result.output.splitlines()[-1]
    assert verdict_line.startswith("HYODO UNOBSERVED")
