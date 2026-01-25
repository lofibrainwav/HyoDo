"""Unit Tests for Excalidraw Diagram Schema Validation - Integration

Integration tests for DiagramSchemaValidator class.
Split from test_validate_diagram_schema.py for 500-line rule compliance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from validate_diagram_schema import (
    DiagramSchemaValidator,
)

# Fixtures are defined in conftest.py


class TestDiagramSchemaValidator:
    """Integration tests for DiagramSchemaValidator class."""

    def test_validate_valid_file(self, valid_excalidraw_json: dict, tmp_diagram_dir: Path) -> None:
        """Validator should accept valid Excalidraw files."""
        file_path = tmp_diagram_dir / "valid_diagram.excalidraw"
        file_path.write_text(json.dumps(valid_excalidraw_json), encoding="utf-8")

        validator = DiagramSchemaValidator()
        result = validator.validate_file(file_path)

        assert result.is_valid is True
        assert result.schema_valid is True
        assert result.error_count == 0

    def test_validate_invalid_json(self, tmp_diagram_dir: Path) -> None:
        """Validator should reject invalid JSON."""
        file_path = tmp_diagram_dir / "invalid.excalidraw"
        file_path.write_text("{not valid json", encoding="utf-8")

        validator = DiagramSchemaValidator()
        result = validator.validate_file(file_path)

        assert result.is_valid is False
        assert result.schema_valid is False
        assert result.error_count >= 1

    def test_validate_directory(self, valid_excalidraw_json: dict, tmp_diagram_dir: Path) -> None:
        """Validator should validate all files in a directory."""
        # Create multiple diagram files
        for i in range(3):
            file_path = tmp_diagram_dir / f"diagram_{i}.excalidraw"
            file_path.write_text(json.dumps(valid_excalidraw_json), encoding="utf-8")

        validator = DiagramSchemaValidator()
        summary = validator.validate_directory(tmp_diagram_dir)

        assert summary.total_files == 3
        assert summary.passed_files == 3
        assert summary.failed_files == 0
        assert summary.all_passed is True

    def test_validate_directory_with_manifest(
        self, valid_excalidraw_json: dict, tmp_diagram_dir: Path
    ) -> None:
        """Validator should respect manifest file."""
        # Create files
        (tmp_diagram_dir / "included.excalidraw").write_text(
            json.dumps(valid_excalidraw_json), encoding="utf-8"
        )
        (tmp_diagram_dir / "excluded.excalidraw").write_text(
            json.dumps(valid_excalidraw_json), encoding="utf-8"
        )

        # Create manifest that only includes one file
        manifest_path = tmp_diagram_dir / "SSOT_VISUAL_MANIFEST.txt"
        manifest_path.write_text("# Manifest\nincluded.excalidraw\n", encoding="utf-8")

        validator = DiagramSchemaValidator()
        summary = validator.validate_directory(tmp_diagram_dir, manifest_path)

        assert summary.total_files == 1
        assert summary.passed_files == 1

    def test_validate_with_pillar_check(
        self, trinity_diagram_json: dict, tmp_diagram_dir: Path
    ) -> None:
        """Validator with pillar check should verify pillar nodes."""
        file_path = tmp_diagram_dir / "trinity.excalidraw"
        file_path.write_text(json.dumps(trinity_diagram_json), encoding="utf-8")

        validator = DiagramSchemaValidator(pillar_check=True)
        result = validator.validate_file(file_path)

        assert result.is_valid is True
        assert len(result.pillar_nodes_found) == 5

    def test_validate_with_strict_mode(
        self, valid_excalidraw_json: dict, tmp_diagram_dir: Path
    ) -> None:
        """Validator in strict mode should treat naming warnings as errors."""
        file_path = tmp_diagram_dir / "InvalidFileName.excalidraw"
        file_path.write_text(json.dumps(valid_excalidraw_json), encoding="utf-8")

        validator = DiagramSchemaValidator(strict=True)
        result = validator.validate_file(file_path)

        assert result.is_valid is False
        assert result.naming_valid is False

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """Validator should handle non-existent directory gracefully."""
        nonexistent = tmp_path / "does_not_exist"

        validator = DiagramSchemaValidator()
        summary = validator.validate_directory(nonexistent)

        assert summary.total_files == 0
        assert summary.all_passed is True

    def test_missing_manifest_file(
        self, valid_excalidraw_json: dict, tmp_diagram_dir: Path
    ) -> None:
        """Validator should warn when manifest declares missing file."""
        # Create manifest referencing non-existent file
        manifest_path = tmp_diagram_dir / "SSOT_VISUAL_MANIFEST.txt"
        manifest_path.write_text("missing_file.excalidraw\n", encoding="utf-8")

        validator = DiagramSchemaValidator()
        summary = validator.validate_directory(tmp_diagram_dir, manifest_path)

        assert summary.failed_files >= 1
        assert summary.total_errors >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
