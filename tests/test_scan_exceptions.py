"""Contract tests for auditable local scan exceptions."""

from __future__ import annotations

from pathlib import Path

import pytest

from hyodo.exceptions import (
    EXCEPTIONS_APPROVED,
    EXCEPTIONS_UNAPPROVED,
    SCAN_EXCEPTIONS_DIGEST_ENV_VAR,
    SCAN_EXCEPTIONS_RELATIVE_PATH,
    ScanExceptionsConfigError,
    approve_scan_exceptions,
    is_general_path_excluded,
    load_scan_exceptions,
    parse_scan_exceptions,
    safety_exception_reason,
)

_FORCE_PUSH_EXCEPTION = """schema = "hyodo.scan-exceptions/v1"

[[safety_exceptions]]
path = "fixtures/**"
rule = "dangerous_command/git_push_force"
reason = "detection fixture"
"""


def _write_config(root: Path, body: str, *, approve: bool = True) -> None:
    path = root / SCAN_EXCEPTIONS_RELATIVE_PATH
    path.parent.mkdir(exist_ok=True)
    path.write_text(body, encoding="utf-8")
    if approve:
        digest = parse_scan_exceptions(root).digest
        assert digest is not None
        approve_scan_exceptions(root, digest, by="human:test")


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
        approve=False,
    )

    with pytest.raises(ScanExceptionsConfigError, match="relative glob"):
        load_scan_exceptions(tmp_path)


def _force_push_fixture(root: Path) -> Path:
    target = root / "fixtures" / "force-push.txt"
    target.parent.mkdir(exist_ok=True)
    target.write_text("git push --force", encoding="utf-8")
    return target


def test_repository_authored_exceptions_do_not_apply_themselves(tmp_path: Path) -> None:
    """A checkout cannot suppress its own safety findings."""
    _write_config(tmp_path, _FORCE_PUSH_EXCEPTION, approve=False)
    target = _force_push_fixture(tmp_path)

    config = load_scan_exceptions(tmp_path)

    assert config.status == EXCEPTIONS_UNAPPROVED
    assert config.withheld == 1
    assert config.safety == ()
    assert (
        safety_exception_reason(str(target), "dangerous_command/git_push_force", tmp_path, config)
        is None
    )


def test_approval_is_void_after_the_file_changes(tmp_path: Path) -> None:
    _write_config(tmp_path, _FORCE_PUSH_EXCEPTION)
    assert load_scan_exceptions(tmp_path).status == EXCEPTIONS_APPROVED

    _write_config(
        tmp_path,
        _FORCE_PUSH_EXCEPTION.replace('"fixtures/**"', '"**"'),
        approve=False,
    )

    config = load_scan_exceptions(tmp_path)
    assert config.status == EXCEPTIONS_UNAPPROVED
    assert config.safety == ()


def test_env_pin_approves_only_the_exact_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(tmp_path, _FORCE_PUSH_EXCEPTION, approve=False)
    digest = parse_scan_exceptions(tmp_path).digest
    assert digest is not None

    monkeypatch.setenv(SCAN_EXCEPTIONS_DIGEST_ENV_VAR, "sha256:" + "0" * 64)
    assert load_scan_exceptions(tmp_path).status == EXCEPTIONS_UNAPPROVED

    monkeypatch.setenv(SCAN_EXCEPTIONS_DIGEST_ENV_VAR, digest)
    assert load_scan_exceptions(tmp_path).status == EXCEPTIONS_APPROVED


def test_approval_does_not_follow_a_copy_of_the_tree(tmp_path: Path) -> None:
    original = tmp_path / "original"
    copy = tmp_path / "copy"
    original.mkdir()
    copy.mkdir()
    _write_config(original, _FORCE_PUSH_EXCEPTION)
    _write_config(copy, _FORCE_PUSH_EXCEPTION, approve=False)

    assert load_scan_exceptions(original).status == EXCEPTIONS_APPROVED
    assert load_scan_exceptions(copy).status == EXCEPTIONS_UNAPPROVED
