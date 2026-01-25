# Trinity Score: 95.0 (Phase 29B Schema Validation Tests)
"""Unit Tests for Excalidraw Diagram Schema Validation - Schema Tests"""

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from validate_diagram_schema import ValidationSeverity, validate_excalidraw_schema

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def valid_excalidraw_json() -> dict:
    """Minimal valid Excalidraw JSON structure."""
    return {
        "type": "excalidraw",
        "version": 2,
        "elements": [
            {
                "id": "elem_001",
                "type": "rectangle",
                "x": 100,
                "y": 200,
                "width": 300,
                "height": 150,
            }
        ],
        "appState": {"viewBackgroundColor": "#ffffff"},
        "files": {},
    }


@pytest.fixture
def trinity_diagram_json() -> dict:
    """Excalidraw JSON with all 5 pillar nodes."""
    return {
        "type": "excalidraw",
        "version": 2,
        "elements": [
            {
                "id": "truth_node",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 180,
                "height": 80,
                "customData": {"pillar": "truth"},
            },
            {
                "id": "truth_text",
                "type": "text",
                "x": 130,
                "y": 130,
                "text": "Truth",
                "originalText": "Truth",
            },
            {
                "id": "goodness_node",
                "type": "rectangle",
                "x": 350,
                "y": 100,
                "width": 180,
                "height": 80,
                "customData": {"pillar": "goodness"},
            },
            {
                "id": "goodness_text",
                "type": "text",
                "x": 380,
                "y": 130,
                "text": "Goodness",
            },
            {
                "id": "beauty_node",
                "type": "rectangle",
                "x": 600,
                "y": 100,
                "width": 180,
                "height": 80,
                "customData": {"pillar": "beauty"},
            },
            {
                "id": "beauty_text",
                "type": "text",
                "x": 630,
                "y": 130,
                "text": "Beauty",
            },
            {
                "id": "serenity_node",
                "type": "rectangle",
                "x": 225,
                "y": 250,
                "width": 180,
                "height": 80,
                "customData": {"pillar": "serenity"},
            },
            {
                "id": "serenity_text",
                "type": "text",
                "x": 255,
                "y": 280,
                "text": "Serenity",
            },
            {
                "id": "eternity_node",
                "type": "rectangle",
                "x": 475,
                "y": 250,
                "width": 180,
                "height": 80,
                "customData": {"pillar": "eternity"},
            },
            {
                "id": "eternity_text",
                "type": "text",
                "x": 505,
                "y": 280,
                "text": "Eternity",
            },
            {
                "id": "arrow_01",
                "type": "arrow",
                "x": 280,
                "y": 140,
                "width": 70,
                "height": 0,
                "points": [[0, 0], [70, 0]],
            },
        ],
        "appState": {},
        "files": {},
    }


@pytest.fixture
def tmp_diagram_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with diagram files."""
    diagrams_dir = tmp_path / "diagrams"
    diagrams_dir.mkdir()
    return diagrams_dir


# ============================================================================
# Schema Validation Tests (Truth)
# ============================================================================


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
