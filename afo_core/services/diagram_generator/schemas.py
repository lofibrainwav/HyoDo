# Trinity Score: 96.0 (Phase 32 Diagram Generator Refactoring)
"""Excalidraw Schema Types and Data Models"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ============================================================================
# Excalidraw Schema Types (眞 - Truth)
# ============================================================================


class ElementType(str, Enum):
    """Excalidraw element types."""

    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    DIAMOND = "diamond"
    TEXT = "text"
    ARROW = "arrow"
    LINE = "line"
    FREEDRAW = "freedraw"
    IMAGE = "image"
    FRAME = "frame"


class StrokeStyle(str, Enum):
    """Stroke style options."""

    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"


class FillStyle(str, Enum):
    """Fill style options."""

    SOLID = "solid"
    HACHURE = "hachure"
    CROSS_HATCH = "cross-hatch"


# ============================================================================
# Excalidraw Element Factory (眞 - Truth)
# ============================================================================


@dataclass
class ExcalidrawElement:
    """Base Excalidraw element."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: ElementType = ElementType.RECTANGLE
    x: float = 0
    y: float = 0
    width: float = 200
    height: float = 100
    angle: float = 0
    strokeColor: str = "#1e1e1e"
    backgroundColor: str = "#ffffff"
    fillStyle: str = "solid"
    strokeWidth: int = 4
    strokeStyle: str = "solid"
    roughness: int = 1
    opacity: int = 100
    seed: int = field(default_factory=lambda: hash(uuid.uuid4()) % 2147483647)
    version: int = 1
    versionNonce: int = field(default_factory=lambda: hash(uuid.uuid4()) % 2147483647)
    isDeleted: bool = False
    groupIds: list[str] = field(default_factory=list)
    boundElements: list[dict[str, Any]] | None = None
    updated: int = field(default_factory=lambda: 1704067200000)  # 2024-01-01
    link: str | None = None
    locked: bool = False
    # Custom data for Trinity integration
    customData: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to Excalidraw JSON dict."""
        result = {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, ElementType) else self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "angle": self.angle,
            "strokeColor": self.strokeColor,
            "backgroundColor": self.backgroundColor,
            "fillStyle": self.fillStyle,
            "strokeWidth": self.strokeWidth,
            "strokeStyle": self.strokeStyle,
            "roughness": self.roughness,
            "opacity": self.opacity,
            "seed": self.seed,
            "version": self.version,
            "versionNonce": self.versionNonce,
            "isDeleted": self.isDeleted,
            "groupIds": self.groupIds,
            "boundElements": self.boundElements,
            "updated": self.updated,
            "link": self.link,
            "locked": self.locked,
        }
        if self.customData:
            result["customData"] = self.customData
        return result


@dataclass
class TextElement(ExcalidrawElement):
    """Text element."""

    type: ElementType = ElementType.TEXT
    text: str = ""
    fontSize: int = 20
    fontFamily: int = 1  # Virgil (hand-drawn)
    textAlign: str = "center"
    verticalAlign: str = "middle"
    baseline: int = 0
    containerId: str | None = None
    originalText: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to Excalidraw JSON dict."""
        result = super().to_dict()
        result.update(
            {
                "text": self.text,
                "fontSize": self.fontSize,
                "fontFamily": self.fontFamily,
                "textAlign": self.textAlign,
                "verticalAlign": self.verticalAlign,
                "baseline": self.baseline,
                "containerId": self.containerId,
                "originalText": self.originalText or self.text,
            }
        )
        return result


@dataclass
class ArrowElement(ExcalidrawElement):
    """Arrow element."""

    type: ElementType = ElementType.ARROW
    points: list[list[float]] = field(default_factory=lambda: [[0, 0], [100, 0]])
    lastCommittedPoint: list[float] | None = None
    startBinding: dict[str, Any] | None = None
    endBinding: dict[str, Any] | None = None
    startArrowhead: str | None = None
    endArrowhead: str = "arrow"

    def to_dict(self) -> dict[str, Any]:
        """Convert to Excalidraw JSON dict."""
        result = super().to_dict()
        result.update(
            {
                "points": self.points,
                "lastCommittedPoint": self.lastCommittedPoint,
                "startBinding": self.startBinding,
                "endBinding": self.endBinding,
                "startArrowhead": self.startArrowhead,
                "endArrowhead": self.endArrowhead,
            }
        )
        return result


# ============================================================================
# Result Models
# ============================================================================


@dataclass
class DiagramGeneratorResult:
    """Result of diagram generation."""

    success: bool
    elements: list[dict[str, Any]]
    excalidraw_json: dict[str, Any]
    file_path: str | None = None
    error: str | None = None
