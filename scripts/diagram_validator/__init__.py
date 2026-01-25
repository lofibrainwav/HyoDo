"""
Diagram Validator Module - Excalidraw Diagram Schema Validation Engine

Visual Format & Schema Validation for AFO Kingdom.

Trinity Score: Truth 100% | Goodness 95% | Beauty 90%
- Truth (Schema Validation): JSON structure compliance
- Goodness (Semantic Check): Required pillar nodes existence
- Beauty (Naming Convention): File and node ID standards

Modules:
- constants: Configuration values and patterns
- models: Data classes for validation results
- schema_validator: Excalidraw JSON schema validation
- pillar_validator: AFO pillar node validation
- naming_validator: Naming convention validation
- validator: Main validator engine
- cli: Command-line interface
"""

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
