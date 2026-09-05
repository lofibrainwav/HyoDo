"""Tests for the status-aware mutmut receipt summarizer."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mutation-score.py"
SPEC = importlib.util.spec_from_file_location("mutation_score", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
mutation_score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mutation_score)


def _write_meta(root: Path, source: str, codes: dict[str, int | None]) -> None:
    path = root / f"{source}.meta"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"exit_code_by_key": codes}), encoding="utf-8")


def _complete_metadata(root: Path) -> None:
    for source in mutation_score.TARGETS:
        _write_meta(root, source, {})


def test_status_mapping_keeps_timeout_and_no_tests_distinct(tmp_path: Path) -> None:
    _complete_metadata(tmp_path)
    _write_meta(
        tmp_path,
        "hyodo/__init__.py",
        {
            "killed-1": 1,
            "killed-3": 3,
            "survived": 0,
            "no-tests-5": 5,
            "no-tests-33": 33,
            "timeout-neg24": -24,
            "timeout-36": 36,
            "skipped": 34,
            "typecheck": 37,
            "segfault": -11,
            "interrupted": 2,
            "suspicious": 35,
            "unknown": 999,
            "not-checked": None,
        },
    )

    rows, total = mutation_score.summarize(tmp_path)
    row = dict(rows)["hyodo/__init__.py"]

    assert row["generated"] == 14
    assert row["killed"] == 2
    assert row["survived"] == 1
    assert row["no_tests"] == 2
    assert row["timeout"] == 2
    assert row["suspicious"] == 2
    assert row["not_checked"] == 1
    assert total["generated"] == 14


def test_missing_target_metadata_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing mutmut metadata"):
        mutation_score.summarize(tmp_path)
