"""Trinity Glow Effects for Diagram Generation

Applies Trinity Score-based visual glow effects to diagram elements.

Trinity Score: 眞 95% | 善 90% | 美 100%
- 眞 (Truth): Accurate score-to-glow mapping
- 善 (Goodness): Safe integration with strategist_glow
- 美 (Beauty): Visual excellence with pillar colors
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .types import ArrowElement, ExcalidrawElement, TextElement


class TrinityGlowEffects:
    """Trinity Glow 효과 적용기.

    다이어그램 요소에 5기둥 기반 glow 효과를 적용합니다.
    """

    def apply_trinity_glow(
        self,
        elements: list[ExcalidrawElement | TextElement | ArrowElement],
        trinity_scores: dict[str, float],
        scale: Literal["unit", "percent"] = "unit",
    ) -> list[ExcalidrawElement | TextElement | ArrowElement]:
        """Apply Trinity Glow effects to elements based on pillar scores.

        Maps each element's pillar to its corresponding Trinity score
        and injects Glow customData.

        Args:
            elements: List of diagram elements
            trinity_scores: {"truth": 0.95, "goodness": 0.90, ...}
            scale: Score scale ("unit" = 0-1, "percent" = 0-100)

        Returns:
            Updated elements with Glow customData injected
        """
        from services.strategist_glow import TrinityGlowManager

        glow_manager = TrinityGlowManager()

        for element in elements:
            if not hasattr(element, "customData"):
                continue

            # Check if element has a pillar assignment
            pillar = element.customData.get("pillar")
            if not pillar:
                continue

            # Map pillar symbol to score key
            pillar_map = {
                "\u771e": "truth",  # 眞
                "\u5584": "goodness",  # 善
                "\u7f8e": "beauty",  # 美
                "\u5b5d": "serenity",  # 孝
                "\u6c38": "eternity",  # 永
            }
            score_key = pillar_map.get(
                pillar, pillar.lower() if isinstance(pillar, str) else "truth"
            )
            score = trinity_scores.get(score_key, 0.8)

            # Inject glow data
            element_dict = element.to_dict()
            updated = glow_manager.inject_glow_into_element(element_dict, pillar, score, scale)

            # Merge back to element
            element.customData.update(updated.get("customData", {}))

        return elements

    def generate_glow_svg_filters(
        self,
        trinity_scores: dict[str, float],
        theme: Literal["dark", "light"] = "dark",
        scale: Literal["unit", "percent"] = "unit",
    ) -> str:
        """Generate SVG filter definitions for Trinity Glow.

        Args:
            trinity_scores: 5-pillar scores
            theme: Color theme mode
            scale: Score scale

        Returns:
            SVG <defs> element containing glow filters
        """
        from services.strategist_glow import GlowConfig, ThemeMode, TrinityGlowManager

        config = GlowConfig(theme=ThemeMode.DARK if theme == "dark" else ThemeMode.LIGHT)
        manager = TrinityGlowManager(config)

        result = manager.create_from_trinity_scores(trinity_scores, scale)
        return result.svg_filters

    def generate_glow_css(
        self,
        trinity_scores: dict[str, float],
        theme: Literal["dark", "light"] = "dark",
        scale: Literal["unit", "percent"] = "unit",
        with_animations: bool = False,
    ) -> str:
        """Generate CSS styles for Trinity Glow.

        Args:
            trinity_scores: 5-pillar scores
            theme: Color theme mode
            scale: Score scale
            with_animations: Include pulse animations

        Returns:
            CSS stylesheet for glow effects
        """
        from services.strategist_glow import GlowConfig, ThemeMode, TrinityGlowManager

        config = GlowConfig(
            theme=ThemeMode.DARK if theme == "dark" else ThemeMode.LIGHT,
            animation_enabled=with_animations,
        )
        manager = TrinityGlowManager(config)

        result = manager.create_from_trinity_scores(trinity_scores, scale)
        return result.css_styles

    def generate_pillar_badges_svg(
        self,
        trinity_scores: dict[str, float],
        positions: dict[str, tuple[float, float]] | None = None,
        theme: Literal["dark", "light"] = "dark",
        scale: Literal["unit", "percent"] = "unit",
    ) -> str:
        """Generate SVG badges for each pillar score.

        Args:
            trinity_scores: 5-pillar scores
            positions: {"truth": (x, y), ...} badge positions
            theme: Color theme mode
            scale: Score scale

        Returns:
            SVG group containing pillar badges
        """
        from services.strategist_glow import GlowConfig, ThemeMode, TrinityGlowManager

        config = GlowConfig(theme=ThemeMode.DARK if theme == "dark" else ThemeMode.LIGHT)
        manager = TrinityGlowManager(config)

        result = manager.create_from_trinity_scores(trinity_scores, scale)

        # Default positions if not provided
        default_positions = {
            "truth": (50, 50),
            "goodness": (100, 50),
            "beauty": (150, 50),
            "serenity": (200, 50),
            "eternity": (250, 50),
        }
        positions = positions or default_positions

        svg_badges = []
        for badge in result.badges:
            pos = positions.get(badge.pillar.value, (0, 0))
            svg_badges.append(badge.to_svg(pos[0], pos[1]))

        return f'<g class="pillar-badges">\n{"".join(svg_badges)}\n</g>'

    def build_excalidraw_json_with_glow(
        self,
        base_json: dict[str, Any],
        trinity_scores: dict[str, float],
        theme: Literal["dark", "light"] = "dark",
    ) -> dict[str, Any]:
        """Build Excalidraw JSON with embedded Glow metadata.

        Args:
            base_json: Base Excalidraw JSON structure
            trinity_scores: 5-pillar scores
            theme: Color theme

        Returns:
            Complete Excalidraw JSON with Glow metadata
        """
        from services.strategist_glow import GlowConfig, ThemeMode, TrinityGlowManager

        config = GlowConfig(theme=ThemeMode.DARK if theme == "dark" else ThemeMode.LIGHT)
        manager = TrinityGlowManager(config)
        glow_result = manager.create_from_trinity_scores(trinity_scores)

        # Add glow metadata to appState
        base_json["appState"]["trinityGlow"] = {
            "enabled": True,
            "theme": theme,
            "scores": trinity_scores,
            "svgFilters": glow_result.svg_filters,
            "cssStyles": glow_result.css_styles,
            "customData": glow_result.custom_data,
        }

        # Set background color based on theme
        base_json["appState"]["viewBackgroundColor"] = "#1a1a2e" if theme == "dark" else "#ffffff"

        return base_json
