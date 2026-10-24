"""Regression coverage for the rm force-flag scanner's backtracking."""

import subprocess
import sys
import textwrap

import pytest

from hyodo.safety import scan_text


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("rm -rf /", True),
        ("rm -fr ~", True),
        ("rm -ffff /tmp/example", True),
        ("rm -r -f /", False),  # Preserve the existing optional-force-flag contract.
        ("rm -f -rf /", True),
        ("rm --force /", True),
        ("rm -FfR /", True),
        ("rm -FR /", False),
        ("rm -rf ./build", False),
        ("rm -rf build", False),
        ("rm -rf ", False),
    ],
)
def test_rm_force_flag_detection_contract(command: str, expected: bool) -> None:
    assert any(f.label == "rm_rf_root" for f in scan_text(command)) is expected


def test_long_force_flag_without_target_is_bounded() -> None:
    """A child process bounds failures without leaving a hung regex worker."""
    script = textwrap.dedent(
        """
        from hyodo.safety import scan_text

        flags = "f" * 100_000
        for command in ("rm -" + flags + " ", "rm -" + flags + " ./build"):
            assert not any(f.label == "rm_rf_root" for f in scan_text(command))
        assert any(f.label == "rm_rf_root" for f in scan_text("rm -" + flags + " /"))
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_long_generic_secret_remains_detectable() -> None:
    """The unrelated generic-key scanner must not acquire a length ceiling."""
    text = "api_key='" + "z" * 256 + "'"
    assert any(f.label == "generic_api_key_assignment" for f in scan_text(text))
