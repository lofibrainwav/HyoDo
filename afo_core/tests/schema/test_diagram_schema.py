"""Unit Tests for Excalidraw Diagram Schema Validation - Schema (Truth)

Tests for schema validation (Truth layer).
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
    validate_excalidraw_schema,
)

# Fixtures are defined in conftest.py


class TestSchemaValidation:
    """Tests for Excalidraw JSON schema validation."""

    def test_valid_schema_passes(self, valid_excalidraw_json: dict, tmp_path: Path) -> None:
        """Valid Excalidraw JSON should pass schema validation."""
        file_path = tmp_path / "test.excalidraw"
        issues = validate_excalidraw_schema(valid_excalidraw_json, file_path)

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) == 0, f"Unexpected errors: {errors}"

    def test_missing_type_field(self, tmp_path: Path) -> None:
        """Missing 'type' field should produce an error."""
        json_data = {"version": 2, "elements": []}
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) >= 1
        assert any("type" in i.message for i in errors)

    def test_missing_version_field(self, tmp_path: Path) -> None:
        """Missing 'version' field should produce an error."""
        json_data = {"type": "excalidraw", "elements": []}
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) >= 1
        assert any("version" in i.message for i in errors)

    def test_missing_elements_field(self, tmp_path: Path) -> None:
        """Missing 'elements' field should produce an error."""
        json_data = {"type": "excalidraw", "version": 2}
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) >= 1
        assert any("elements" in i.message for i in errors)

    def test_invalid_type_value(self, tmp_path: Path) -> None:
        """Invalid 'type' value should produce an error."""
        json_data = {"type": "not-excalidraw", "version": 2, "elements": []}
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) >= 1
        assert any("not-excalidraw" in i.message for i in errors)

    def test_elements_not_list(self, tmp_path: Path) -> None:
        """Non-list 'elements' field should produce an error."""
        json_data = {"type": "excalidraw", "version": 2, "elements": "not-a-list"}
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) >= 1
        assert any("list" in i.message.lower() for i in errors)

    def test_element_missing_id(self, tmp_path: Path) -> None:
        """Element without 'id' should produce an error."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [{"type": "rectangle", "x": 0, "y": 0}],
        }
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) >= 1
        assert any("id" in i.message for i in errors)

    def test_element_missing_type(self, tmp_path: Path) -> None:
        """Element without 'type' should produce an error."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [{"id": "elem1", "x": 0, "y": 0}],
        }
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) >= 1
        assert any("type" in i.message for i in errors)

    def test_duplicate_element_ids(self, tmp_path: Path) -> None:
        """Duplicate element IDs should produce an error."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {"id": "same_id", "type": "rectangle"},
                {"id": "same_id", "type": "ellipse"},
            ],
        }
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) >= 1
        assert any("duplicate" in i.message.lower() for i in errors)

    def test_unknown_element_type_warning(self, tmp_path: Path) -> None:
        """Unknown element type should produce a warning (not error)."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [{"id": "elem1", "type": "custom_unknown_type"}],
        }
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        assert len(warnings) >= 1
        assert any("unknown" in i.message.lower() for i in warnings)

    def test_arrow_with_insufficient_points_warning(self, tmp_path: Path) -> None:
        """Arrow with less than 2 points should produce a warning."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {"id": "arrow1", "type": "arrow", "points": [[0, 0]]},
            ],
        }
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        assert len(warnings) >= 1
        assert any("2 points" in i.message for i in warnings)

    def test_text_element_missing_text_field(self, tmp_path: Path) -> None:
        """Text element without 'text' field should produce a warning."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [{"id": "text1", "type": "text", "x": 0, "y": 0}],
        }
        file_path = tmp_path / "test.excalidraw"

        issues = validate_excalidraw_schema(json_data, file_path)

        warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        assert len(warnings) >= 1
        assert any("text" in i.message.lower() for i in warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
