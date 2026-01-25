"""Unit Tests for Excalidraw Diagram Schema Validation - Models

Tests for ValidationResult, ValidationSummary, ValidationIssue dataclasses.
Split from test_validate_diagram_schema.py for 500-line rule compliance.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from validate_diagram_schema import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidationSummary,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_error_count(self, tmp_path: Path) -> None:
        """Error count should correctly count ERROR severity issues."""
        result = ValidationResult(
            file_path=tmp_path / "test.excalidraw",
            is_valid=False,
            issues=[
                ValidationIssue(severity=ValidationSeverity.ERROR, message="Error 1"),
                ValidationIssue(severity=ValidationSeverity.ERROR, message="Error 2"),
                ValidationIssue(severity=ValidationSeverity.WARNING, message="Warning"),
            ],
        )

        assert result.error_count == 2
        assert result.warning_count == 1

    def test_warning_count(self, tmp_path: Path) -> None:
        """Warning count should correctly count WARNING severity issues."""
        result = ValidationResult(
            file_path=tmp_path / "test.excalidraw",
            is_valid=True,
            issues=[
                ValidationIssue(severity=ValidationSeverity.WARNING, message="Warning 1"),
                ValidationIssue(severity=ValidationSeverity.WARNING, message="Warning 2"),
            ],
        )

        assert result.warning_count == 2
        assert result.error_count == 0


class TestValidationSummary:
    """Tests for ValidationSummary dataclass."""

    def test_all_passed_true(self) -> None:
        """all_passed should be True when no files fail."""
        summary = ValidationSummary(total_files=3, passed_files=3, failed_files=0)
        assert summary.all_passed is True

    def test_all_passed_false(self) -> None:
        """all_passed should be False when any files fail."""
        summary = ValidationSummary(total_files=3, passed_files=2, failed_files=1)
        assert summary.all_passed is False


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_str_representation(self) -> None:
        """ValidationIssue should have readable string representation."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Test error message",
            file_path="test.excalidraw",
            element_id="elem_001",
        )

        str_repr = str(issue)
        assert "[ERROR]" in str_repr
        assert "test.excalidraw" in str_repr
        assert "elem_001" in str_repr
        assert "Test error message" in str_repr

    def test_str_without_location(self) -> None:
        """ValidationIssue string without location info."""
        issue = ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message="Generic warning",
        )

        str_repr = str(issue)
        assert "[WARNING]" in str_repr
        assert "Generic warning" in str_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
