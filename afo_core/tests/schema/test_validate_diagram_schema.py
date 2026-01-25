"""Unit Tests for Excalidraw Diagram Schema Validation (PH-SE-05.02)

Tests for scripts/validate_diagram_schema.py - Visual Format & Schema Validation.

Trinity Score: Truth 100% | Goodness 100% | Beauty 95%
- Truth: Schema validation accuracy
- Goodness: Pillar node detection correctness
- Beauty: Naming convention enforcement

NOTE: This file is a thin re-export for backward compatibility.
      Tests have been split into separate files for 500-line rule compliance:
      - test_diagram_schema.py: Schema validation tests (Truth)
      - test_diagram_pillar.py: Pillar node validation tests (Goodness)
      - test_diagram_naming.py: Naming convention tests (Beauty)
      - test_diagram_integration.py: DiagramSchemaValidator integration tests
      - test_diagram_models.py: ValidationResult/Summary/Issue model tests
"""

from __future__ import annotations

# Re-export all test classes for backward compatibility
from tests.schema.test_diagram_integration import TestDiagramSchemaValidator
from tests.schema.test_diagram_models import (
    TestValidationIssue,
    TestValidationResult,
    TestValidationSummary,
)
from tests.schema.test_diagram_naming import TestNamingConventionValidation
from tests.schema.test_diagram_pillar import TestPillarNodeValidation
from tests.schema.test_diagram_schema import TestSchemaValidation

__all__ = [
    "TestSchemaValidation",
    "TestPillarNodeValidation",
    "TestNamingConventionValidation",
    "TestDiagramSchemaValidator",
    "TestValidationResult",
    "TestValidationSummary",
    "TestValidationIssue",
]
