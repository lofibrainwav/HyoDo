"""Unit Tests for Excalidraw Diagram Schema Validation - Naming (Beauty)

Tests for AFO naming convention validation (Beauty layer).
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
    ValidationSeverity,
    validate_naming_conventions,
)

# Fixtures are defined in conftest.py


class TestNamingConventionValidation:
    """Tests for AFO naming convention validation."""

    def test_valid_file_name(self, valid_excalidraw_json: dict, tmp_path: Path) -> None:
        """Valid file name should pass validation."""
        file_path = tmp_path / "valid_diagram_name.excalidraw"

        issues = validate_naming_conventions(valid_excalidraw_json, file_path)

        # No naming errors for the file name
        file_name_errors = [
            i for i in issues if "File name" in i.message and i.severity == ValidationSeverity.ERROR
        ]
        assert len(file_name_errors) == 0

    def test_invalid_file_name_uppercase(self, valid_excalidraw_json: dict, tmp_path: Path) -> None:
        """File name with uppercase should produce a warning."""
        file_path = tmp_path / "InvalidDiagram.excalidraw"

        issues = validate_naming_conventions(valid_excalidraw_json, file_path)

        warnings = [
            i
            for i in issues
            if "File name" in i.message and i.severity == ValidationSeverity.WARNING
        ]
        assert len(warnings) >= 1

    def test_invalid_file_name_space(self, valid_excalidraw_json: dict, tmp_path: Path) -> None:
        """File name with space should produce a warning."""
        file_path = tmp_path / "invalid diagram.excalidraw"

        issues = validate_naming_conventions(valid_excalidraw_json, file_path)

        warnings = [
            i
            for i in issues
            if "File name" in i.message and i.severity == ValidationSeverity.WARNING
        ]
        assert len(warnings) >= 1

    def test_strict_mode_file_name_error(self, valid_excalidraw_json: dict, tmp_path: Path) -> None:
        """In strict mode, invalid file name should be an error."""
        file_path = tmp_path / "InvalidName.excalidraw"

        issues = validate_naming_conventions(valid_excalidraw_json, file_path, strict=True)

        errors = [
            i for i in issues if "File name" in i.message and i.severity == ValidationSeverity.ERROR
        ]
        assert len(errors) >= 1

    def test_valid_element_id(self, tmp_path: Path) -> None:
        """Valid element IDs should pass validation."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {"id": "valid_id_123", "type": "rectangle"},
                {"id": "another-valid-id", "type": "rectangle"},
            ],
        }
        file_path = tmp_path / "test.excalidraw"

        issues = validate_naming_conventions(json_data, file_path)

        id_errors = [i for i in issues if "Element ID" in i.message]
        assert len(id_errors) == 0

    def test_invalid_element_id_special_chars(self, tmp_path: Path) -> None:
        """Element ID with special characters should produce a warning."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {"id": "invalid@id#123", "type": "rectangle"},
            ],
        }
        file_path = tmp_path / "test.excalidraw"

        issues = validate_naming_conventions(json_data, file_path)

        warnings = [i for i in issues if "Element ID" in i.message]
        assert len(warnings) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
