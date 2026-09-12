from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from hyodo.access_ledger import (
    ACCESS_LEDGER_PATH,
    AccessEntry,
    read_access_log_result,
    record_access_result,
)


def entry() -> AccessEntry:
    return AccessEntry(
        timestamp="2026-09-12T00:00:00+00:00",
        tool_name="hyodo_check",
        root="/tmp/project",
        exit_code=0,
        duration_ms=12,
    )


def test_absent_ledger_is_distinct_from_observed_empty(tmp_path: Path) -> None:
    result = read_access_log_result(tmp_path)
    assert result.state == "ABSENT"
    assert result.entries == []
    assert result.reason is None


def test_successful_write_is_observed(tmp_path: Path) -> None:
    write = record_access_result(entry(), root=tmp_path)
    assert write.state == "OBSERVED"
    result = read_access_log_result(tmp_path)
    assert result.state == "OBSERVED"
    assert [item.tool_name for item in result.entries] == ["hyodo_check"]


def test_write_failure_is_explicit_and_non_fatal(tmp_path: Path) -> None:
    with patch("pathlib.Path.open", side_effect=OSError("read only")):
        result = record_access_result(entry(), root=tmp_path)
    assert result.state == "UNOBSERVED"
    assert result.reason == "write_failed"


def test_corrupt_rows_are_not_healthy_empty(tmp_path: Path) -> None:
    path = tmp_path / ACCESS_LEDGER_PATH
    path.parent.mkdir(parents=True)
    path.write_text("not-json\n", encoding="utf-8")
    result = read_access_log_result(tmp_path)
    assert result.state == "UNOBSERVED"
    assert result.reason == "corrupt_lines"
    assert result.corrupt_lines == 1
    assert result.entries == []


def test_valid_rows_survive_beside_corrupt_rows(tmp_path: Path) -> None:
    record_access_result(entry(), root=tmp_path)
    path = tmp_path / ACCESS_LEDGER_PATH
    path.write_text(path.read_text(encoding="utf-8") + "broken\n", encoding="utf-8")
    result = read_access_log_result(tmp_path)
    assert result.state == "UNOBSERVED"
    assert result.corrupt_lines == 1
    assert len(result.entries) == 1


def test_unreadable_ledger_is_unobserved(tmp_path: Path) -> None:
    path = tmp_path / ACCESS_LEDGER_PATH
    path.parent.mkdir(parents=True)
    path.write_text("{}\n", encoding="utf-8")
    with patch("pathlib.Path.read_text", side_effect=OSError("unreadable")):
        result = read_access_log_result(tmp_path)
    assert result.state == "UNOBSERVED"
    assert result.reason == "read_failed"
