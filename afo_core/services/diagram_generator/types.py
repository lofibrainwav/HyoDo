"""Diagram Generator Types (PH-SE-05.01)

Excalidraw schema types and Neo-Brutalism style configuration.

Trinity Score: 眞 100% | 善 95% | 美 90%
- 眞 (Truth): Type-safe Excalidraw element definitions
- 善 (Goodness): Immutable dataclass patterns
- 美 (Beauty): Neo-Brutalism style system
"""

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
# Neo-Brutalism Style Configuration (美 - Beauty)
# ============================================================================


@dataclass
class NeoBrutalismStyle:
    """네오 브루탈리즘 스타일 설정.

    굵은 선, 고대비 색상, 하드 섀도우 특징.
    """

    # Stroke settings
    stroke_width: int = 4
    stroke_color: str = "#1e1e1e"
    stroke_style: StrokeStyle = StrokeStyle.SOLID

    # Fill settings
    fill_style: FillStyle = FillStyle.SOLID
    background_color: str = "#ffffff"

    # Trinity Colors (眞善美孝永)
    truth_color: str = "#3b82f6"  # 眞 - Blue (Truth)
    goodness_color: str = "#22c55e"  # 善 - Green (Goodness)
    beauty_color: str = "#a855f7"  # 美 - Purple (Beauty)
    serenity_color: str = "#f59e0b"  # 孝 - Amber (Serenity)
    eternity_color: str = "#ef4444"  # 永 - Red (Eternity)

    # Typography
    font_family: int = 1  # Virgil (hand-drawn)
    font_size: int = 20

    # Opacity
    opacity: int = 100

    # Roughness (0 = clean, higher = more hand-drawn)
    roughness: int = 1

    def get_pillar_color(self, pillar: str) -> str:
        """Get color for a pillar (眞善美孝永)."""
        color_map = {
            "眞": self.truth_color,
            "truth": self.truth_color,
            "善": self.goodness_color,
            "goodness": self.goodness_color,
            "美": self.beauty_color,
            "beauty": self.beauty_color,
            "孝": self.serenity_color,
            "serenity": self.serenity_color,
            "永": self.eternity_color,
            "eternity": self.eternity_color,
        }
        return color_map.get(pillar.lower(), self.stroke_color)


# Default style instance
NEO_BRUTALISM = NeoBrutalismStyle()


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
    strokeColor: str = NEO_BRUTALISM.stroke_color
    backgroundColor: str = NEO_BRUTALISM.background_color
    fillStyle: str = NEO_BRUTALISM.fill_style.value
    strokeWidth: int = NEO_BRUTALISM.stroke_width
    strokeStyle: str = NEO_BRUTALISM.stroke_style.value
    roughness: int = NEO_BRUTALISM.roughness
    opacity: int = NEO_BRUTALISM.opacity
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
    fontSize: int = NEO_BRUTALISM.font_size
    fontFamily: int = NEO_BRUTALISM.font_family
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
# Result Types (re-exported from schemas for backward compatibility)
# ============================================================================

# DiagramGeneratorResult is defined in schemas.py to avoid circular imports
# Import it from there: from services.diagram_generator.schemas import DiagramGeneratorResult
