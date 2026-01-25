"""
Diagram Pillar Validator - AFO pillar node validation (Goodness)

Validates:
- Required pillar nodes existence (truth, goodness, beauty, serenity, eternity)
- Pillar references in element text and customData
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.diagram_validator.constants import PILLAR_NAMES
from scripts.diagram_validator.models import ValidationIssue, ValidationSeverity


def validate_pillar_nodes(
    json_data: dict[str, Any], file_path: Path, required_pillars: list[str] | None = None
) -> tuple[list[ValidationIssue], list[str]]:
    """Validate that required pillar nodes exist in the diagram.

    Args:
        json_data: Parsed JSON data
        file_path: Path to the file for error reporting
        required_pillars: List of required pillar names (default: all 5 pillars)

    Returns:
        Tuple of (validation issues, found pillar names)
    """
    issues: list[ValidationIssue] = []
    file_str = str(file_path)
    found_pillars: set[str] = set()

    # Default to all five pillars
    if required_pillars is None:
        required_pillars = ["truth", "goodness", "beauty", "serenity", "eternity"]

    elements = json_data.get("elements", [])
    if not isinstance(elements, list):
        return issues, []

    # Search for pillar references in element text and customData
    for elem in elements:
        if not isinstance(elem, dict):
            continue

        # Check customData.pillar field (used by diagram_generator.py)
        custom_data = elem.get("customData", {})
        if isinstance(custom_data, dict):
            pillar_value = custom_data.get("pillar", "")
            if pillar_value:
                found_pillars.update(_identify_pillar(str(pillar_value)))

        # Check text content for pillar keywords
        text_content = elem.get("text", "")
        if text_content:
            found_pillars.update(_identify_pillar(str(text_content)))

        # Check originalText as well
        original_text = elem.get("originalText", "")
        if original_text:
            found_pillars.update(_identify_pillar(str(original_text)))

    # Check for missing required pillars
    for pillar in required_pillars:
        if pillar.lower() not in found_pillars:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Missing required pillar node: '{pillar}'",
                    file_path=file_str,
                )
            )

    return issues, list(found_pillars)


def _identify_pillar(text: str) -> set[str]:
    """Identify pillar references in text.

    Args:
        text: Text content to search

    Returns:
        Set of identified pillar names
    """
    found: set[str] = set()
    text_lower = text.lower()

    for pillar_name, aliases in PILLAR_NAMES.items():
        for alias in aliases:
            if alias in text_lower:
                found.add(pillar_name)
                break

    return found
