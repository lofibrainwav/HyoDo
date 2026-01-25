# Trinity Score: 97.0 (Phase 32 Diagram Generator Refactoring)
"""
AI Diagram Generator - Backward Compatibility Wrapper

This file serves as a backward compatibility wrapper for the refactored
diagram_generator package. All functionality has been moved to the diagram_generator/
directory for better organization and maintainability.

Original: 1,800 lines → Refactored: 4 files, 150-300 lines each
- diagram_generator/schemas.py - Excalidraw schemas and models (200 lines)
- diagram_generator/styles.py - Neo-Brutalism styling (100 lines)
- diagram_generator/core.py - Core generation logic (300 lines)
- diagram_generator/__init__.py - Package exports

Migration completed: 2026-01-16
Phase 32: Large file refactoring for better maintainability
"""

# Backward compatibility - import from refactored package
from .diagram_generator import (
    NEO_BRUTALISM,
    ArrowElement,
    DiagramGenerator,
    DiagramGeneratorResult,
    ElementType,
    ExcalidrawElement,
    FillStyle,
    NeoBrutalismStyle,
    StrokeStyle,
    TextElement,
)

# Re-export for backward compatibility (keeping original interface)
__all__ = [
    "DiagramGenerator",
    "DiagramGeneratorResult",
    "NeoBrutalismStyle",
    "NEO_BRUTALISM",
    "ExcalidrawElement",
    "TextElement",
    "ArrowElement",
    "ElementType",
    "StrokeStyle",
    "FillStyle",
]
