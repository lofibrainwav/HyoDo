# Trinity Score: 95.0 (Established by Chancellor)
"""Unit tests for Strategist Glow - TrinityGlowManager (Serenity & Eternity)

TrinityGlowManager integration and convenience function tests.
Split from test_strategist_glow.py for 500-line rule compliance.
"""

from __future__ import annotations

from typing import Any

import pytest


class TestTrinityGlowManager:
    """Test TrinityGlowManager integration."""

    def test_create_from_trinity_scores(self) -> None:
        """Test creating glow result from scores."""
        from services.strategist_glow import TrinityGlowManager

        manager = TrinityGlowManager()
        scores = {
            "truth": 0.95,
            "goodness": 0.90,
            "beauty": 0.85,
            "serenity": 0.92,
            "eternity": 1.0,
        }
        result = manager.create_from_trinity_scores(scores)

        assert len(result.pillar_glows) == 5
        assert result.svg_filters != ""
        assert result.css_styles != ""
        assert len(result.badges) == 5
        assert "trinity_glow" in result.custom_data

    def test_create_from_trinity_scores_percent_scale(self) -> None:
        """Test creating glow result from percent scores."""
        from services.strategist_glow import TrinityGlowManager

        manager = TrinityGlowManager()
        scores = {
            "truth": 95.0,
            "goodness": 90.0,
            "beauty": 85.0,
            "serenity": 92.0,
            "eternity": 100.0,
        }
        result = manager.create_from_trinity_scores(scores, scale="percent")

        assert len(result.pillar_glows) == 5
        # Scores should be normalized to 0-1
        for glow in result.pillar_glows:
            assert 0.0 <= glow.score <= 1.0

    def test_inject_glow_into_element(self) -> None:
        """Test injecting glow data into element."""
        from services.strategist_glow import Pillar, TrinityGlowManager

        manager = TrinityGlowManager()
        element: dict[str, Any] = {"id": "test-elem", "type": "rectangle"}

        updated = manager.inject_glow_into_element(element, Pillar.TRUTH, 0.95, scale="unit")

        assert "customData" in updated
        assert "glow" in updated["customData"]
        assert "svgFilter" in updated["customData"]
        assert updated["customData"]["glow"]["pillar"] == "truth"

    def test_inject_glow_preserves_existing_data(self) -> None:
        """Test that existing customData is preserved."""
        from services.strategist_glow import Pillar, TrinityGlowManager

        manager = TrinityGlowManager()
        element: dict[str, Any] = {
            "id": "test-elem",
            "customData": {"existing_key": "existing_value"},
        }

        updated = manager.inject_glow_into_element(element, Pillar.TRUTH, 0.95)

        assert updated["customData"]["existing_key"] == "existing_value"
        assert "glow" in updated["customData"]

    def test_apply_theme(self) -> None:
        """Test theme switching."""
        from services.strategist_glow import ThemeMode, TrinityGlowManager

        manager = TrinityGlowManager()
        assert manager.config.theme == ThemeMode.DARK

        manager.apply_theme(ThemeMode.LIGHT)
        assert manager.config.theme == ThemeMode.LIGHT

    def test_custom_data_structure(self) -> None:
        """Test custom_data follows expected structure."""
        from services.strategist_glow import TrinityGlowManager

        manager = TrinityGlowManager()
        scores = {
            "truth": 0.95,
            "goodness": 0.90,
            "beauty": 0.85,
            "serenity": 0.92,
            "eternity": 1.0,
        }
        result = manager.create_from_trinity_scores(scores)

        custom_data = result.custom_data
        assert "trinity_glow" in custom_data
        assert "theme" in custom_data["trinity_glow"]
        assert "pillars" in custom_data["trinity_glow"]

        pillars = custom_data["trinity_glow"]["pillars"]
        assert "truth" in pillars
        assert "goodness" in pillars
        assert "beauty" in pillars
        assert "serenity" in pillars
        assert "eternity" in pillars


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_create_glow_from_scores(self) -> None:
        """Test create_glow_from_scores function."""
        from services.strategist_glow import ThemeMode, create_glow_from_scores

        scores = {
            "truth": 0.95,
            "goodness": 0.90,
            "beauty": 0.85,
            "serenity": 0.92,
            "eternity": 1.0,
        }
        result = create_glow_from_scores(scores, theme=ThemeMode.DARK)

        assert len(result.pillar_glows) == 5
        assert result.svg_filters != ""

    def test_get_pillar_css_class(self) -> None:
        """Test get_pillar_css_class function."""
        from services.strategist_glow import Pillar, get_pillar_css_class

        css_class = get_pillar_css_class(Pillar.TRUTH, 0.95)
        assert "glow-truth" in css_class
        assert "glow-level-critical" in css_class

    def test_get_pillar_css_class_with_string(self) -> None:
        """Test get_pillar_css_class with string input."""
        from services.strategist_glow import get_pillar_css_class

        css_class = get_pillar_css_class("goodness", 0.6)
        assert "glow-goodness" in css_class
        assert "glow-level-medium" in css_class


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
