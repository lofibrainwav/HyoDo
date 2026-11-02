"""The read-only lens-evidence CLI consumes existing dashboard evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.dispatch import app
from hyodo.virtues import CANONICAL_VIRTUE_KEYS

runner = CliRunner()
SUBJECT_SHA = "a" * 40


def _write_envelope(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "hyodo.dashboard-evidence/v2",
                "measured_at": "2026-01-01T00:00:00Z",
                "provenance": {
                    "target_commit": SUBJECT_SHA,
                    "target_dirty": False,
                    "tool_version": "4.22.4",
                },
                "gates": {
                    "tests": {"status": "PASS", "pillar": "truth"},
                    "lint": {"status": "FAIL", "pillar": "beauty"},
                },
            }
        ),
        encoding="utf-8",
    )


def test_lens_evidence_cli_emits_six_receipts_without_running_project_gates(tmp_path: Path) -> None:
    evidence_file = tmp_path / "evidence.json"
    _write_envelope(evidence_file)

    result = runner.invoke(
        app,
        [
            "lens-evidence",
            "emit",
            "--file",
            str(evidence_file),
            "--subject-sha",
            SUBJECT_SHA,
        ],
    )

    assert result.exit_code == 0, result.output
    receipts = json.loads(result.stdout)
    assert [receipt["lens"] for receipt in receipts] == list(CANONICAL_VIRTUE_KEYS)
    assert all(receipt["schema_version"] == "hyodo.lens-evidence/v1" for receipt in receipts)
    assert all(receipt["authority"] == "UNOBSERVED" for receipt in receipts)


@pytest.mark.parametrize(
    "contents",
    [
        "not json",
        "[]",
        "{}",
        '{"schema_version":"hyodo.dashboard-evidence/v2","provenance":{},"gates":[]}',
        '{"schema_version":"hyodo.dashboard-evidence/v1","provenance":{},"gates":{}}',
    ],
)
def test_lens_evidence_cli_rejects_malformed_or_missing_envelopes(
    tmp_path: Path, contents: str
) -> None:
    evidence_file = tmp_path / "evidence.json"
    evidence_file.write_text(contents, encoding="utf-8")

    result = runner.invoke(
        app,
        ["lens-evidence", "emit", "--file", str(evidence_file), "--subject-sha", SUBJECT_SHA],
    )

    assert result.exit_code != 0
    assert result.stdout == ""


def test_lens_evidence_cli_rejects_missing_file_and_invalid_subject_sha(tmp_path: Path) -> None:
    missing = runner.invoke(
        app,
        [
            "lens-evidence",
            "emit",
            "--file",
            str(tmp_path / "missing.json"),
            "--subject-sha",
            SUBJECT_SHA,
        ],
    )
    assert missing.exit_code != 0
    assert missing.stdout == ""

    evidence_file = tmp_path / "evidence.json"
    _write_envelope(evidence_file)
    invalid_sha = runner.invoke(
        app,
        ["lens-evidence", "emit", "--file", str(evidence_file), "--subject-sha", "abc123"],
    )
    assert invalid_sha.exit_code != 0
    assert invalid_sha.stdout == ""
