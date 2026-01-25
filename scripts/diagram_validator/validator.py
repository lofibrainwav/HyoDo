"""
Diagram Validator - Main validation engine

Contains the DiagramSchemaValidator class that orchestrates
all validation types (schema, naming, pillar).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from scripts.diagram_validator.models import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidationSummary,
)
from scripts.diagram_validator.naming_validator import validate_naming_conventions
from scripts.diagram_validator.pillar_validator import validate_pillar_nodes
from scripts.diagram_validator.schema_validator import validate_excalidraw_schema

logger = logging.getLogger(__name__)


class DiagramSchemaValidator:
    """Excalidraw Diagram Schema Validation Engine.

    Integrates with verify_visual_sync.py for comprehensive diagram validation.
    """

    def __init__(
        self,
        strict: bool = False,
        pillar_check: bool = False,
        required_pillars: list[str] | None = None,
    ) -> None:
        """Initialize the validator.

        Args:
            strict: If True, treat naming warnings as errors
            pillar_check: If True, validate pillar nodes existence
            required_pillars: List of required pillar names for pillar_check
        """
        self.strict = strict
        self.pillar_check = pillar_check
        self.required_pillars = required_pillars

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a single Excalidraw file.

        Args:
            file_path: Path to the .excalidraw file

        Returns:
            ValidationResult with detailed issues
        """
        result = ValidationResult(file_path=file_path, is_valid=True)

        # Read and parse JSON
        try:
            content = file_path.read_text(encoding="utf-8")
            json_data = json.loads(content)
        except json.JSONDecodeError as e:
            result.is_valid = False
            result.schema_valid = False
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid JSON: {e}",
                    file_path=str(file_path),
                    line_number=e.lineno,
                )
            )
            return result
        except OSError as e:
            result.is_valid = False
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Failed to read file: {e}",
                    file_path=str(file_path),
                )
            )
            return result

        # Schema validation (Truth)
        schema_issues = validate_excalidraw_schema(json_data, file_path)
        result.issues.extend(schema_issues)
        if any(i.severity == ValidationSeverity.ERROR for i in schema_issues):
            result.schema_valid = False

        # Naming convention validation (Beauty)
        naming_issues = validate_naming_conventions(json_data, file_path, self.strict)
        result.issues.extend(naming_issues)
        if any(i.severity == ValidationSeverity.ERROR for i in naming_issues):
            result.naming_valid = False

        # Pillar node validation (Goodness) - optional
        if self.pillar_check:
            pillar_issues, found_pillars = validate_pillar_nodes(
                json_data, file_path, self.required_pillars
            )
            result.issues.extend(pillar_issues)
            result.pillar_nodes_found = found_pillars
            if any(i.severity == ValidationSeverity.ERROR for i in pillar_issues):
                result.semantic_valid = False

        # Determine overall validity
        result.is_valid = result.error_count == 0

        return result

    def validate_directory(
        self, directory: Path, manifest_path: Path | None = None
    ) -> ValidationSummary:
        """Validate all Excalidraw files in a directory.

        Args:
            directory: Directory to scan for .excalidraw files
            manifest_path: Optional path to SSOT_VISUAL_MANIFEST.txt

        Returns:
            ValidationSummary with all results
        """
        summary = ValidationSummary()

        if not directory.exists():
            logger.warning(f"Directory not found: {directory}, skipping validation")
            return summary

        # Load manifest if provided
        manifest_files: set[str] | None = None
        if manifest_path and manifest_path.exists():
            manifest_files = self._load_manifest(manifest_path)

        # Find all .excalidraw files
        excalidraw_files = sorted(directory.rglob("*.excalidraw"))

        for file_path in excalidraw_files:
            # If manifest exists, optionally filter to manifest files
            if manifest_files is not None:
                rel_path = str(file_path.relative_to(directory))
                if rel_path not in manifest_files:
                    logger.debug(f"Skipping {rel_path} (not in manifest)")
                    continue

            result = self.validate_file(file_path)
            summary.results.append(result)
            summary.total_files += 1
            summary.total_errors += result.error_count
            summary.total_warnings += result.warning_count

            if result.is_valid:
                summary.passed_files += 1
            else:
                summary.failed_files += 1

        # Check manifest integrity - all manifest files should exist
        if manifest_files is not None:
            for manifest_file in manifest_files:
                full_path = directory / manifest_file
                if not full_path.exists():
                    summary.total_errors += 1
                    # Create a placeholder result for missing file
                    missing_result = ValidationResult(
                        file_path=full_path,
                        is_valid=False,
                        issues=[
                            ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                message=f"Manifest declares file but it is missing: {manifest_file}",
                                file_path=str(full_path),
                            )
                        ],
                    )
                    summary.results.append(missing_result)
                    summary.total_files += 1
                    summary.failed_files += 1

        return summary

    def _load_manifest(self, manifest_path: Path) -> set[str]:
        """Load file list from SSOT_VISUAL_MANIFEST.txt.

        Args:
            manifest_path: Path to manifest file

        Returns:
            Set of file names from manifest
        """
        manifest_files: set[str] = set()

        try:
            content = manifest_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    manifest_files.add(line)
        except OSError as e:
            logger.warning(f"Failed to read manifest: {e}")

        return manifest_files
