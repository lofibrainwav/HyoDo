"""Contract tests for auditable local scan exceptions."""

from __future__ import annotations

from pathlib import Path

import pytest

from hyodo.exceptions import (
    SCAN_EXCEPTIONS_RELATIVE_PATH,
    ScanExceptionsConfigError,
    is_general_path_excluded,
    load_scan_exceptions,
    safety_exception_reason,
)


def _write_config(root: Path, body: str) -> None:
    path = root / SCAN_EXCEPTIONS_RELATIVE_PATH
    path.parent.mkdir()
    path.write_text(body, encoding="utf-8")


def test_missing_config_is_empty_policy(tmp_path: Path) -> None:
    config = load_scan_exceptions(tmp_path)

    assert config.general == ()
    assert config.safety == ()


def test_general_exception_requires_reason_and_matches_relative_path(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        """schema = "hyodo.scan-exceptions/v1"

[[general_exceptions]]
path = "01-Research/legal/**"
reason = "private legal working material"
""",
    )
    target = tmp_path / "01-Research" / "legal" / "memo.js"
    target.parent.mkdir(parents=True)
    target.write_text("not valid JavaScript", encoding="utf-8")

    config = load_scan_exceptions(tmp_path)

    assert is_general_path_excluded(target, tmp_path, config)


def test_safety_exception_requires_path_rule_and_reason(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        """schema = "hyodo.scan-exceptions/v1"

[[safety_exceptions]]
path = "fixtures/**"
rule = "dangerous_command/git_push_force"
reason = "detection fixture"
""",
    )
    target = tmp_path / "fixtures" / "force-push.txt"
    target.parent.mkdir()
    target.write_text("git push --force", encoding="utf-8")

    config = load_scan_exceptions(tmp_path)

    assert (
        safety_exception_reason(str(target), "dangerous_command/git_push_force", tmp_path, config)
        == "detection fixture"
    )
    assert (
        safety_exception_reason(str(target), "dangerous_command/rm_rf_root", tmp_path, config)
        is None
    )


def test_malformed_config_is_fail_closed(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        """schema = "hyodo.scan-exceptions/v1"

[[safety_exceptions]]
path = "../outside/**"
rule = "dangerous_command/git_push_force"
reason = "invalid"
""",
    )

    with pytest.raises(ScanExceptionsConfigError, match="relative glob"):
        load_scan_exceptions(tmp_path)
