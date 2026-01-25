# Trinity Score: 98.0 (Phase 32 Diagram Generator Package)
"""Diagram Generator Package - Refactored for Better Organization"""

from .core import (
    DiagramGenerator,
    generate_trinity_diagram,
    parse_and_generate_diagram,
)
from .schemas import (
    ArrowElement,
    DiagramGeneratorResult,
    ElementType,
    ExcalidrawElement,
    FillStyle,
    StrokeStyle,
    TextElement,
)
from .styles import NEO_BRUTALISM, NeoBrutalismStyle

# Re-export main classes and functions for backward compatibility
__all__ = [
    "DiagramGenerator",
    "DiagramGeneratorResult",
    "ExcalidrawElement",
    "TextElement",
    "ArrowElement",
    "ElementType",
    "StrokeStyle",
    "FillStyle",
    "NeoBrutalismStyle",
    "NEO_BRUTALISM",
    # Convenience functions
    "generate_trinity_diagram",
    "parse_and_generate_diagram",
]
