# Trinity Score: 95.0 (Phase 32 Diagram Generator Refactoring)
"""Neo-Brutalism Style Configuration and Theme Management"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
    stroke_style: str = "solid"

    # Fill settings
    fill_style: str = "solid"
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
# Style Utilities
# ============================================================================


def apply_style_to_element(
    element: Any, style: NeoBrutalismStyle, pillar: str | None = None
) -> Any:
    """Apply style configuration to an element.

    Args:
        element: Element to style
        style: Style configuration
        pillar: Trinity pillar for color (optional)

    Returns:
        Styled element
    """
    # Apply basic styling
    element.strokeColor = style.stroke_color
    element.strokeWidth = style.stroke_width
    element.strokeStyle = style.stroke_style
    element.fillStyle = style.fill_style
    element.roughness = style.roughness
    element.opacity = style.opacity

    # Apply pillar-specific background color
    if pillar:
        element.backgroundColor = style.get_pillar_color(pillar)
    else:
        element.backgroundColor = style.background_color

    return element


def create_element_style_config(
    style: NeoBrutalismStyle,
    pillar: str | None = None,
    custom_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create style configuration dict for element creation.

    Args:
        style: Base style configuration
        pillar: Trinity pillar for color
        custom_overrides: Custom style overrides

    Returns:
        Style configuration dict
    """
    config = {
        "strokeColor": style.stroke_color,
        "strokeWidth": style.stroke_width,
        "strokeStyle": style.stroke_style,
        "fillStyle": style.fill_style,
        "roughness": style.roughness,
        "opacity": style.opacity,
        "backgroundColor": style.background_color,
    }

    # Apply pillar color
    if pillar:
        config["backgroundColor"] = style.get_pillar_color(pillar)

    # Apply custom overrides
    if custom_overrides:
        config.update(custom_overrides)

    return config
