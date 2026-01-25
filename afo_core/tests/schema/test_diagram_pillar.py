"""Unit Tests for Excalidraw Diagram Schema Validation - Pillar (Goodness)

Tests for pillar node semantic validation (Goodness layer).
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
    validate_pillar_nodes,
)

# Fixtures are defined in conftest.py


class TestPillarNodeValidation:
    """Tests for pillar node semantic validation."""

    def test_all_pillars_present(self, trinity_diagram_json: dict, tmp_path: Path) -> None:
        """Diagram with all 5 pillars should pass validation."""
        file_path = tmp_path / "test.excalidraw"

        issues, found_pillars = validate_pillar_nodes(trinity_diagram_json, file_path)

        # No warnings for missing pillars
        warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        assert len(warnings) == 0

        # All pillars should be found
        assert "truth" in found_pillars
        assert "goodness" in found_pillars
        assert "beauty" in found_pillars
        assert "serenity" in found_pillars
        assert "eternity" in found_pillars

    def test_missing_pillar_warning(self, tmp_path: Path) -> None:
        """Missing pillar node should produce a warning."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {
                    "id": "truth_node",
                    "type": "rectangle",
                    "customData": {"pillar": "truth"},
                },
            ],
        }
        file_path = tmp_path / "test.excalidraw"

        issues, found_pillars = validate_pillar_nodes(json_data, file_path)

        warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        # Should warn about missing goodness, beauty, serenity, eternity
        assert len(warnings) >= 4

        # Only truth should be found
        assert "truth" in found_pillars
        assert "goodness" not in found_pillars

    def test_pillar_detection_via_custom_data(self, tmp_path: Path) -> None:
        """Pillar should be detected via customData.pillar field."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {
                    "id": "node1",
                    "type": "rectangle",
                    "customData": {"pillar": "beauty"},
                },
            ],
        }
        file_path = tmp_path / "test.excalidraw"

        issues, found_pillars = validate_pillar_nodes(
            json_data, file_path, required_pillars=["beauty"]
        )

        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) == 0
        assert "beauty" in found_pillars

    def test_pillar_detection_via_text_content(self, tmp_path: Path) -> None:
        """Pillar should be detected via text content."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {
                    "id": "text1",
                    "type": "text",
                    "text": "Goodness Node",
                },
            ],
        }
        file_path = tmp_path / "test.excalidraw"

        issues, found_pillars = validate_pillar_nodes(
            json_data, file_path, required_pillars=["goodness"]
        )

        warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        assert len(warnings) == 0
        assert "goodness" in found_pillars

    def test_custom_required_pillars(self, tmp_path: Path) -> None:
        """Should allow specifying custom required pillars."""
        json_data = {
            "type": "excalidraw",
            "version": 2,
            "elements": [
                {
                    "id": "node1",
                    "type": "rectangle",
                    "customData": {"pillar": "truth"},
                },
            ],
        }
        file_path = tmp_path / "test.excalidraw"

        # Only require 'truth'
        issues, found_pillars = validate_pillar_nodes(
            json_data, file_path, required_pillars=["truth"]
        )

        warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        assert len(warnings) == 0
        assert "truth" in found_pillars


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
