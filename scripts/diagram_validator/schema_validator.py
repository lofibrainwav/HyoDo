"""
Diagram Schema Validator - Excalidraw JSON schema validation (Truth)

Validates:
- Required top-level fields (type, version, elements)
- Element structure and types
- Numeric field types
- Stroke/fill styles
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.diagram_validator.constants import (
    VALID_ELEMENT_TYPES,
    VALID_FILL_STYLES,
    VALID_STROKE_STYLES,
)
from scripts.diagram_validator.models import ValidationIssue, ValidationSeverity


def validate_excalidraw_schema(json_data: dict[str, Any], file_path: Path) -> list[ValidationIssue]:
    """Validate Excalidraw JSON schema structure.

    Based on diagram_generator.py's _build_excalidraw_json structure.

    Args:
        json_data: Parsed JSON data
        file_path: Path to the file for error reporting

    Returns:
        List of validation issues
    """
    issues: list[ValidationIssue] = []
    file_str = str(file_path)

    # Required top-level fields
    required_fields = ["type", "version", "elements"]
    for req_field in required_fields:
        if req_field not in json_data:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing required top-level field: '{req_field}'",
                    file_path=file_str,
                )
            )

    # Validate 'type' field
    file_type = json_data.get("type")
    if file_type is not None and file_type != "excalidraw":
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Invalid type: '{file_type}', expected 'excalidraw'",
                file_path=file_str,
            )
        )

    # Validate 'version' field
    version = json_data.get("version")
    if version is not None:
        if not isinstance(version, int):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Version should be an integer, got: {type(version).__name__}",
                    file_path=file_str,
                )
            )
        elif version < 1:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Unusual version number: {version}",
                    file_path=file_str,
                )
            )

    # Validate 'elements' field
    elements = json_data.get("elements")
    if elements is not None:
        if not isinstance(elements, list):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="'elements' must be a list",
                    file_path=file_str,
                )
            )
        else:
            issues.extend(_validate_elements(elements, file_str))

    # Validate optional 'appState' field
    app_state = json_data.get("appState")
    if app_state is not None and not isinstance(app_state, dict):
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="'appState' should be an object",
                file_path=file_str,
            )
        )

    # Validate optional 'files' field
    files = json_data.get("files")
    if files is not None and not isinstance(files, dict):
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="'files' should be an object",
                file_path=file_str,
            )
        )

    return issues


def _validate_elements(elements: list[Any], file_str: str) -> list[ValidationIssue]:
    """Validate individual elements in the elements array.

    Args:
        elements: List of element dictionaries
        file_str: File path string for error reporting

    Returns:
        List of validation issues
    """
    issues: list[ValidationIssue] = []
    seen_ids: set[str] = set()

    for i, elem in enumerate(elements):
        if not isinstance(elem, dict):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Element at index {i} is not a dictionary",
                    file_path=file_str,
                )
            )
            continue

        elem_id = elem.get("id")
        elem_type = elem.get("type")

        # Required element fields
        if elem_id is None:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Element at index {i} missing required 'id' field",
                    file_path=file_str,
                )
            )
        else:
            # Check for duplicate IDs
            if elem_id in seen_ids:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Duplicate element ID: '{elem_id}'",
                        file_path=file_str,
                        element_id=elem_id,
                    )
                )
            seen_ids.add(elem_id)

        if elem_type is None:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Element at index {i} missing required 'type' field",
                    file_path=file_str,
                    element_id=elem_id,
                )
            )
        elif elem_type not in VALID_ELEMENT_TYPES:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Unknown element type: '{elem_type}'",
                    file_path=file_str,
                    element_id=elem_id,
                )
            )

        # Validate numeric fields
        for num_field in ["x", "y", "width", "height", "angle", "opacity"]:
            if num_field in elem:
                value = elem[num_field]
                if value is not None and not isinstance(value, int | float):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"Field '{num_field}' should be numeric, got: {type(value).__name__}",
                            file_path=file_str,
                            element_id=elem_id,
                        )
                    )

        # Validate stroke/fill styles
        stroke_style = elem.get("strokeStyle")
        if stroke_style is not None and stroke_style not in VALID_STROKE_STYLES:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Unknown strokeStyle: '{stroke_style}'",
                    file_path=file_str,
                    element_id=elem_id,
                )
            )

        fill_style = elem.get("fillStyle")
        if fill_style is not None and fill_style not in VALID_FILL_STYLES:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Unknown fillStyle: '{fill_style}'",
                    file_path=file_str,
                    element_id=elem_id,
                )
            )

        # Validate isDeleted field
        is_deleted = elem.get("isDeleted")
        if is_deleted is not None and not isinstance(is_deleted, bool):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="'isDeleted' should be a boolean",
                    file_path=file_str,
                    element_id=elem_id,
                )
            )

        # Validate text element specific fields
        if elem_type == "text":
            if "text" not in elem:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message="Text element missing 'text' field",
                        file_path=file_str,
                        element_id=elem_id,
                    )
                )

        # Validate arrow element specific fields
        if elem_type == "arrow":
            points = elem.get("points")
            if points is not None:
                if not isinstance(points, list):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message="Arrow 'points' should be a list",
                            file_path=file_str,
                            element_id=elem_id,
                        )
                    )
                elif len(points) < 2:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message="Arrow should have at least 2 points",
                            file_path=file_str,
                            element_id=elem_id,
                        )
                    )

    return issues
