"""
Diagram Naming Validator - Naming convention validation (Beauty)

Validates:
- File naming conventions (lowercase_with_underscores.excalidraw)
- Element ID conventions (alphanumeric, underscore, hyphen)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.diagram_validator.constants import FILE_NAMING_PATTERN, NODE_ID_PATTERN
from scripts.diagram_validator.models import ValidationIssue, ValidationSeverity


def validate_naming_conventions(
    json_data: dict[str, Any], file_path: Path, strict: bool = False
) -> list[ValidationIssue]:
    """Validate AFO naming conventions for files and node IDs.

    Args:
        json_data: Parsed JSON data
        file_path: Path to the file for error reporting
        strict: If True, treat warnings as errors

    Returns:
        List of validation issues
    """
    issues: list[ValidationIssue] = []
    file_str = str(file_path)

    # Validate file naming
    file_name = file_path.name
    if not FILE_NAMING_PATTERN.match(file_name):
        severity = ValidationSeverity.ERROR if strict else ValidationSeverity.WARNING
        issues.append(
            ValidationIssue(
                severity=severity,
                message=f"File name '{file_name}' does not follow AFO naming convention "
                "(expected: lowercase_with_underscores.excalidraw)",
                file_path=file_str,
            )
        )

    # Validate element IDs
    elements = json_data.get("elements", [])
    if isinstance(elements, list):
        for elem in elements:
            if not isinstance(elem, dict):
                continue

            elem_id = elem.get("id")
            if elem_id and not NODE_ID_PATTERN.match(str(elem_id)):
                severity = ValidationSeverity.ERROR if strict else ValidationSeverity.WARNING
                issues.append(
                    ValidationIssue(
                        severity=severity,
                        message=f"Element ID '{elem_id}' contains invalid characters "
                        "(expected: alphanumeric, underscore, or hyphen only)",
                        file_path=file_str,
                        element_id=elem_id,
                    )
                )

    return issues
