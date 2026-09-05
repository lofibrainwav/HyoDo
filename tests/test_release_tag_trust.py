"""Unit tests for the release tag trust gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release" / "verify_git_tag.py"
SPEC = importlib.util.spec_from_file_location("verify_git_tag", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
verify_git_tag = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_git_tag)


def _ref(*, object_type: str = "tag", sha: str = "tag-object-sha") -> dict:
    return {"ref": "refs/tags/v4.12.0", "object": {"type": object_type, "sha": sha}}


def _tag(
    *,
    verified: bool = True,
    reason: str = "valid",
    tag_name: str = "v4.12.0",
    target_type: str = "commit",
    target_sha: str = "release-commit",
) -> dict:
    return {
        "tag": tag_name,
        "object": {"type": target_type, "sha": target_sha},
        "verification": {"verified": verified, "reason": reason},
    }


def test_verified_annotated_tag_passes() -> None:
    ok, message, target = verify_git_tag.evaluate_tag_trust(
        _ref(),
        _tag(),
        expected_tag="v4.12.0",
        expected_commit="release-commit",
    )

    assert ok is True
    assert message == "verified annotated tag"
    assert target == "release-commit"


def test_lightweight_tag_fails_closed() -> None:
    ok, message, target = verify_git_tag.evaluate_tag_trust(
        _ref(object_type="commit", sha="release-commit"),
        {},
        expected_tag="v4.12.0",
        expected_commit="release-commit",
    )

    assert ok is False
    assert "lightweight" in message
    assert target is None


def test_unsigned_annotated_tag_fails_closed() -> None:
    ok, message, target = verify_git_tag.evaluate_tag_trust(
        _ref(),
        _tag(verified=False, reason="unsigned"),
        expected_tag="v4.12.0",
        expected_commit="release-commit",
    )

    assert ok is False
    assert "reason=unsigned" in message
    assert target == "release-commit"


def test_tag_name_mismatch_fails_closed() -> None:
    ok, message, _ = verify_git_tag.evaluate_tag_trust(
        _ref(),
        _tag(tag_name="v4.11.0"),
        expected_tag="v4.12.0",
        expected_commit="release-commit",
    )

    assert ok is False
    assert "name mismatch" in message


def test_nested_tag_fails_closed() -> None:
    ok, message, _ = verify_git_tag.evaluate_tag_trust(
        _ref(),
        _tag(target_type="tag"),
        expected_tag="v4.12.0",
    )

    assert ok is False
    assert "directly to a commit" in message


def test_verified_tag_target_must_match_checkout() -> None:
    ok, message, target = verify_git_tag.evaluate_tag_trust(
        _ref(),
        _tag(target_sha="different-commit"),
        expected_tag="v4.12.0",
        expected_commit="release-commit",
    )

    assert ok is False
    assert "checked-out release commit" in message
    assert target == "different-commit"
