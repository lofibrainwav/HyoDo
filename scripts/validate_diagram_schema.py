#!/usr/bin/env python3
"""Excalidraw Diagram Schema Validation Engine (PH-SE-05.02)

Visual Format & Schema Validation for AFO Kingdom.

⚠️ DEPRECATED: This file is a thin wrapper for backward compatibility.
   Use `scripts.diagram_validator` module directly for new code.

Trinity Score: Truth 100% | Goodness 95% | Beauty 90%
- Truth (Schema Validation): JSON structure compliance
- Goodness (Semantic Check): Required pillar nodes existence
- Beauty (Naming Convention): File and node ID standards

Usage:
    python scripts/validate_diagram_schema.py [--strict] [--pillar-check] [path]
    python -m scripts.diagram_validator.cli [options]

Exit Codes:
    0 - All validations passed
    1 - Validation failures detected
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to sys.path for module imports
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Re-export from modular structure for backward compatibility
from scripts.diagram_validator.cli import main, print_summary
from scripts.diagram_validator.constants import (
    FILE_NAMING_PATTERN,
    NODE_ID_PATTERN,
    PILLAR_NAMES,
    VALID_ELEMENT_TYPES,
    VALID_FILL_STYLES,
    VALID_STROKE_STYLES,
)
from scripts.diagram_validator.models import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidationSummary,
)
from scripts.diagram_validator.naming_validator import validate_naming_conventions
from scripts.diagram_validator.pillar_validator import validate_pillar_nodes
from scripts.diagram_validator.schema_validator import validate_excalidraw_schema
from scripts.diagram_validator.validator import DiagramSchemaValidator

__all__ = [
    # Constants
    "PILLAR_NAMES",
    "VALID_ELEMENT_TYPES",
    "VALID_STROKE_STYLES",
    "VALID_FILL_STYLES",
    "FILE_NAMING_PATTERN",
    "NODE_ID_PATTERN",
    # Models
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    "ValidationSummary",
    # Validators
    "validate_excalidraw_schema",
    "validate_pillar_nodes",
    "validate_naming_conventions",
    "DiagramSchemaValidator",
    # CLI
    "print_summary",
    "main",
]

if __name__ == "__main__":
    sys.exit(main())
