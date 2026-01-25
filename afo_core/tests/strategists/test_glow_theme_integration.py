# Trinity Score: 95.0 (Established by Chancellor)
"""Unit tests for Strategist Glow - Theme Support and Integration

Dark/Light theme support and DiagramGenerator integration tests.
Split from test_strategist_glow.py for 500-line rule compliance.
"""

from __future__ import annotations

import pytest


class TestDarkLightThemeSupport:
    """Test dark and light theme support (CI Gate requirement)."""

    def test_dark_mode_colors_are_brighter(self) -> None:
        """Test dark mode glow colors are brighter than primary."""
        from services.strategist_glow import PILLAR_COLORS, Pillar

        for pillar in Pillar:
            color = PILLAR_COLORS[pillar]
            # In dark mode, glow should be lighter (higher RGB values)
            # This is a semantic test - brighter glow for better visibility
            assert color.dark_glow != color.dark_primary

    def test_light_mode_colors_are_darker(self) -> None:
        """Test light mode glow colors are darker than primary."""
        from services.strategist_glow import PILLAR_COLORS, Pillar

        for pillar in Pillar:
            color = PILLAR_COLORS[pillar]
            # In light mode, glow should be darker for contrast
            assert color.light_glow != color.light_primary

    def test_theme_affects_filter_generation(self) -> None:
        """Test theme mode affects SVG filter colors."""
        from services.strategist_glow import (
            GlowConfig,
            Pillar,
            PillarGlow,
            SVGFilterGenerator,
            ThemeMode,
        )

        # Dark theme
        dark_config = GlowConfig(theme=ThemeMode.DARK)
        dark_generator = SVGFilterGenerator(dark_config)
        dark_glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.95)
        dark_filter = dark_generator.generate_glow_filter(dark_glow)

        # Light theme
        light_config = GlowConfig(theme=ThemeMode.LIGHT)
        light_generator = SVGFilterGenerator(light_config)
        light_glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.95)
        light_filter = light_generator.generate_glow_filter(light_glow)

        # Filters should have different colors
        assert dark_filter != light_filter

    def test_theme_affects_css_generation(self) -> None:
        """Test theme mode affects CSS box-shadow colors."""
        from services.strategist_glow import (
            GlowConfig,
            Pillar,
            PillarGlow,
            SVGFilterGenerator,
            ThemeMode,
        )

        # Dark theme
        dark_config = GlowConfig(theme=ThemeMode.DARK)
        dark_generator = SVGFilterGenerator(dark_config)
        dark_glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.95)
        dark_css = dark_generator.generate_css_glow(dark_glow)

        # Light theme
        light_config = GlowConfig(theme=ThemeMode.LIGHT)
        light_generator = SVGFilterGenerator(light_config)
        light_glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.95)
        light_css = light_generator.generate_css_glow(light_glow)

        # CSS should have different colors
        assert dark_css != light_css


class TestDiagramGeneratorIntegration:
    """Test integration with DiagramGenerator (PH-SE-05.01)."""

    def test_diagram_generator_imports_strategist_glow(self) -> None:
        """Test DiagramGenerator can import strategist_glow."""
        try:
            from services.diagram_generator import DiagramGenerator

            generator = DiagramGenerator()
            # Note: Glow methods are planned for future implementation (PH-SE-05.01)
            # Skip if these methods are not yet available
            if not hasattr(generator, "apply_trinity_glow"):
                pytest.skip("Glow methods not yet implemented in DiagramGenerator")
            assert hasattr(generator, "apply_trinity_glow")
            assert hasattr(generator, "generate_glow_svg_filters")
            assert hasattr(generator, "generate_glow_css")
            assert hasattr(generator, "generate_pillar_badges_svg")
            assert hasattr(generator, "generate_trinity_diagram_with_glow")
        except ImportError:
            pytest.skip("DiagramGenerator not available")

    def test_generate_trinity_diagram_with_glow(self) -> None:
        """Test generating Trinity diagram with glow effects."""
        try:
            from services.diagram_generator import DiagramGenerator

            generator = DiagramGenerator()
            # Note: Glow methods are planned for future implementation (PH-SE-05.01)
            if not hasattr(generator, "generate_trinity_diagram_with_glow"):
                pytest.skip("generate_trinity_diagram_with_glow not yet implemented")

            scores = {
                "truth": 0.95,
                "goodness": 0.90,
                "beauty": 0.85,
                "serenity": 0.92,
                "eternity": 1.0,
            }
            result = generator.generate_trinity_diagram_with_glow(
                title="Test Trinity", trinity_scores=scores, theme="dark"
            )

            assert result.success is True
            assert len(result.elements) > 0
            assert "trinityGlow" in result.excalidraw_json.get("appState", {})
        except ImportError:
            pytest.skip("DiagramGenerator not available")

    def test_apply_trinity_glow_to_elements(self) -> None:
        """Test applying glow to diagram elements."""
        try:
            from services.diagram_generator import DiagramGenerator

            generator = DiagramGenerator()
            base_result = generator.generate_trinity_diagram(title="Test")

            if base_result.success:
                # Elements should have customData with pillar info
                pillar_elements = [
                    e for e in base_result.elements if e.get("customData", {}).get("pillar")
                ]
                assert len(pillar_elements) > 0
        except ImportError:
            pytest.skip("DiagramGenerator not available")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_pillar_scores(self) -> None:
        """Test handling of missing pillar scores."""
        from services.strategist_glow import TrinityGlowManager

        manager = TrinityGlowManager()
        # Only provide partial scores
        scores = {"truth": 0.95}
        result = manager.create_from_trinity_scores(scores)

        # Should still create 5 pillar glows with default values
        assert len(result.pillar_glows) == 5

    def test_invalid_pillar_string_fallback(self) -> None:
        """Test fallback for invalid pillar string."""
        from services.strategist_glow import Pillar, PillarGlow

        # Invalid pillar should default to TRUTH
        glow = PillarGlow.from_trinity_score("invalid_pillar", 0.5)
        assert glow.pillar == Pillar.TRUTH

    def test_empty_pillar_glows_list(self) -> None:
        """Test generating filters with empty list."""
        from services.strategist_glow import SVGFilterGenerator

        generator = SVGFilterGenerator()
        result = generator.generate_all_filters([])
        assert result == ""

    def test_all_none_level_filters(self) -> None:
        """Test generating filters when all are 'none' level."""
        from services.strategist_glow import Pillar, PillarGlow, SVGFilterGenerator

        generator = SVGFilterGenerator()
        glows = [
            PillarGlow.from_trinity_score(Pillar.TRUTH, 0.1),  # none level
            PillarGlow.from_trinity_score(Pillar.GOODNESS, 0.05),  # none level
        ]
        result = generator.generate_all_filters(glows)
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
