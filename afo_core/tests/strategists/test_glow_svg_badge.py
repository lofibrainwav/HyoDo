# Trinity Score: 95.0 (Established by Chancellor)
"""Unit tests for Strategist Glow - SVG Filter and Badge Generation (Beauty)

SVG Glow filter and Badge rendering tests.
Split from test_strategist_glow.py for 500-line rule compliance.
"""

from __future__ import annotations

import pytest


class TestSVGFilterGenerator:
    """Test SVG Glow filter generation."""

    def test_generate_filter_id(self) -> None:
        """Test filter ID generation."""
        from services.strategist_glow import Pillar, SVGFilterGenerator

        generator = SVGFilterGenerator()
        filter_id = generator.generate_filter_id(Pillar.TRUTH, "high")
        assert filter_id == "glow-truth-high"

    def test_generate_glow_filter_structure(self) -> None:
        """Test SVG filter structure."""
        from services.strategist_glow import Pillar, PillarGlow, SVGFilterGenerator

        generator = SVGFilterGenerator()
        glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.95, scale="unit")
        svg_filter = generator.generate_glow_filter(glow)

        assert "<filter" in svg_filter
        assert "id=" in svg_filter
        assert "feGaussianBlur" in svg_filter
        assert "feFlood" in svg_filter
        assert "feMerge" in svg_filter

    def test_generate_glow_filter_none_level(self) -> None:
        """Test no filter for 'none' level."""
        from services.strategist_glow import Pillar, PillarGlow, SVGFilterGenerator

        generator = SVGFilterGenerator()
        glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.1, scale="unit")
        svg_filter = generator.generate_glow_filter(glow)

        assert svg_filter == ""

    def test_generate_all_filters(self) -> None:
        """Test generating all filters wrapped in <defs>."""
        from services.strategist_glow import Pillar, PillarGlow, SVGFilterGenerator

        generator = SVGFilterGenerator()
        glows = [
            PillarGlow.from_trinity_score(Pillar.TRUTH, 0.95, scale="unit"),
            PillarGlow.from_trinity_score(Pillar.GOODNESS, 0.90, scale="unit"),
            PillarGlow.from_trinity_score(Pillar.BEAUTY, 0.85, scale="unit"),
        ]
        svg_defs = generator.generate_all_filters(glows)

        assert "<defs>" in svg_defs
        assert "</defs>" in svg_defs
        assert "glow-truth" in svg_defs
        assert "glow-goodness" in svg_defs
        assert "glow-beauty" in svg_defs

    def test_generate_css_glow(self) -> None:
        """Test CSS box-shadow generation."""
        from services.strategist_glow import Pillar, PillarGlow, SVGFilterGenerator

        generator = SVGFilterGenerator()
        glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.95, scale="unit")
        css_shadow = generator.generate_css_glow(glow)

        # Should have multi-layer box-shadow
        assert "px" in css_shadow
        assert "#" in css_shadow  # Color values

    def test_generate_css_glow_none_level(self) -> None:
        """Test 'none' CSS for low score."""
        from services.strategist_glow import Pillar, PillarGlow, SVGFilterGenerator

        generator = SVGFilterGenerator()
        glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.1, scale="unit")
        css_shadow = generator.generate_css_glow(glow)

        assert css_shadow == "none"

    def test_generate_animation_keyframes_disabled(self) -> None:
        """Test animation keyframes when disabled."""
        from services.strategist_glow import GlowConfig, Pillar, SVGFilterGenerator

        config = GlowConfig(animation_enabled=False)
        generator = SVGFilterGenerator(config)
        keyframes = generator.generate_animation_keyframes(Pillar.TRUTH)

        assert keyframes == ""

    def test_generate_animation_keyframes_enabled(self) -> None:
        """Test animation keyframes when enabled."""
        from services.strategist_glow import GlowConfig, Pillar, SVGFilterGenerator

        config = GlowConfig(animation_enabled=True, animation_duration_ms=2000)
        generator = SVGFilterGenerator(config)
        keyframes = generator.generate_animation_keyframes(Pillar.TRUTH)

        assert "@keyframes" in keyframes
        assert "glow-pulse-truth" in keyframes
        assert "2000ms" in keyframes


class TestPillarBadge:
    """Test PillarBadge generation."""

    def test_from_pillar_glow(self) -> None:
        """Test badge creation from PillarGlow."""
        from services.strategist_glow import GlowConfig, Pillar, PillarBadge, PillarGlow

        config = GlowConfig()
        glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.95, scale="unit")
        badge = PillarBadge.from_pillar_glow(glow, config)

        assert badge.pillar == Pillar.TRUTH
        assert badge.score == 0.95
        assert badge.symbol == "\u771e"  # 眞
        assert badge.size == 24  # Default size

    def test_to_svg(self) -> None:
        """Test badge SVG generation."""
        from services.strategist_glow import GlowConfig, Pillar, PillarBadge, PillarGlow

        config = GlowConfig()
        glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.95, scale="unit")
        badge = PillarBadge.from_pillar_glow(glow, config)
        svg = badge.to_svg(100, 200)

        assert '<g class="pillar-badge"' in svg
        assert "translate(100" in svg
        assert "translate(100, 200)" in svg
        assert "<circle" in svg
        assert "\u771e" in svg  # Symbol 眞
        assert "95" in svg  # Score as percentage


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
