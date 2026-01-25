# Trinity Score: 95.0 (Established by Chancellor)
"""Unit tests for Strategist Glow - Schema Definitions (Truth)

Glow Schema, PillarEnum, ThemeMode, GlowIntensity, GlowConfig tests.
Split from test_strategist_glow.py for 500-line rule compliance.
"""

from __future__ import annotations

import pytest


class TestPillarEnum:
    """Test Pillar enumeration values."""

    def test_pillar_values(self) -> None:
        """Test all 5 pillars have correct values."""
        from services.strategist_glow import Pillar

        assert Pillar.TRUTH.value == "truth"
        assert Pillar.GOODNESS.value == "goodness"
        assert Pillar.BEAUTY.value == "beauty"
        assert Pillar.SERENITY.value == "serenity"
        assert Pillar.ETERNITY.value == "eternity"

    def test_pillar_count(self) -> None:
        """Test exactly 5 pillars exist."""
        from services.strategist_glow import Pillar

        assert len(Pillar) == 5


class TestThemeMode:
    """Test ThemeMode enumeration."""

    def test_theme_modes(self) -> None:
        """Test dark and light theme modes."""
        from services.strategist_glow import ThemeMode

        assert ThemeMode.DARK.value == "dark"
        assert ThemeMode.LIGHT.value == "light"


class TestPillarColor:
    """Test PillarColor dataclass."""

    def test_pillar_colors_exist(self) -> None:
        """Test all pillars have color definitions."""
        from services.strategist_glow import PILLAR_COLORS, Pillar

        for pillar in Pillar:
            assert pillar in PILLAR_COLORS
            color = PILLAR_COLORS[pillar]
            assert color.dark_primary.startswith("#")
            assert color.dark_glow.startswith("#")
            assert color.light_primary.startswith("#")
            assert color.light_glow.startswith("#")

    def test_truth_pillar_is_blue(self) -> None:
        """Test Truth pillar has blue color (semantic)."""
        from services.strategist_glow import PILLAR_COLORS, Pillar

        truth_color = PILLAR_COLORS[Pillar.TRUTH]
        assert truth_color.symbol == "\u771e"  # 眞
        # Blue range: #3b82f6 (dark), #2563eb (light)
        assert "3b82f6" in truth_color.dark_primary or "blue" in truth_color.dark_primary.lower()

    def test_goodness_pillar_is_green(self) -> None:
        """Test Goodness pillar has green color (semantic)."""
        from services.strategist_glow import PILLAR_COLORS, Pillar

        goodness_color = PILLAR_COLORS[Pillar.GOODNESS]
        assert goodness_color.symbol == "\u5584"  # 善
        # Green range: #22c55e (dark), #16a34a (light)
        assert (
            "22c55e" in goodness_color.dark_primary
            or "green" in goodness_color.dark_primary.lower()
        )

    def test_beauty_pillar_is_purple(self) -> None:
        """Test Beauty pillar has purple color (semantic)."""
        from services.strategist_glow import PILLAR_COLORS, Pillar

        beauty_color = PILLAR_COLORS[Pillar.BEAUTY]
        assert beauty_color.symbol == "\u7f8e"  # 美
        # Purple range: #a855f7 (dark), #9333ea (light)
        assert (
            "a855f7" in beauty_color.dark_primary or "purple" in beauty_color.dark_primary.lower()
        )


class TestGlowIntensity:
    """Test GlowIntensity calculation."""

    def test_from_score_unit_scale(self) -> None:
        """Test GlowIntensity from unit scale (0-1)."""
        from services.strategist_glow import GlowIntensity

        intensity = GlowIntensity.from_score(0.95, scale="unit")
        assert intensity.normalized == 0.95
        assert intensity.level == "critical"
        assert intensity.blur_radius > 0
        assert 0 <= intensity.opacity <= 1

    def test_from_score_percent_scale(self) -> None:
        """Test GlowIntensity from percent scale (0-100)."""
        from services.strategist_glow import GlowIntensity

        intensity = GlowIntensity.from_score(95.0, scale="percent")
        assert intensity.normalized == 0.95
        assert intensity.level == "critical"

    def test_intensity_level_none(self) -> None:
        """Test 'none' level for very low scores."""
        from services.strategist_glow import GlowIntensity

        intensity = GlowIntensity.from_score(0.1, scale="unit")
        assert intensity.level == "none"

    def test_intensity_level_low(self) -> None:
        """Test 'low' level for low scores."""
        from services.strategist_glow import GlowIntensity

        intensity = GlowIntensity.from_score(0.3, scale="unit")
        assert intensity.level == "low"

    def test_intensity_level_medium(self) -> None:
        """Test 'medium' level for medium scores."""
        from services.strategist_glow import GlowIntensity

        intensity = GlowIntensity.from_score(0.6, scale="unit")
        assert intensity.level == "medium"

    def test_intensity_level_high(self) -> None:
        """Test 'high' level for high scores."""
        from services.strategist_glow import GlowIntensity

        intensity = GlowIntensity.from_score(0.85, scale="unit")
        assert intensity.level == "high"

    def test_intensity_level_critical(self) -> None:
        """Test 'critical' level for very high scores."""
        from services.strategist_glow import GlowIntensity

        intensity = GlowIntensity.from_score(0.95, scale="unit")
        assert intensity.level == "critical"

    def test_intensity_clamping(self) -> None:
        """Test score clamping to valid range."""
        from services.strategist_glow import GlowIntensity

        # Over 1.0
        intensity_high = GlowIntensity.from_score(1.5, scale="unit")
        assert intensity_high.normalized == 1.0

        # Below 0.0
        intensity_low = GlowIntensity.from_score(-0.5, scale="unit")
        assert intensity_low.normalized == 0.0


class TestPillarGlow:
    """Test PillarGlow dataclass."""

    def test_from_trinity_score_with_pillar_enum(self) -> None:
        """Test PillarGlow creation with Pillar enum."""
        from services.strategist_glow import Pillar, PillarGlow

        glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.90, scale="unit")
        assert glow.pillar == Pillar.TRUTH
        assert glow.score == 0.90
        assert glow.intensity.level in ("high", "critical")

    def test_from_trinity_score_with_string(self) -> None:
        """Test PillarGlow creation with string pillar name."""
        from services.strategist_glow import Pillar, PillarGlow

        glow = PillarGlow.from_trinity_score("goodness", 0.85, scale="unit")
        assert glow.pillar == Pillar.GOODNESS
        assert glow.score == 0.85

    def test_from_trinity_score_with_chinese_symbol(self) -> None:
        """Test PillarGlow creation with Chinese character."""
        from services.strategist_glow import Pillar, PillarGlow

        glow = PillarGlow.from_trinity_score("\u7f8e", 0.75, scale="unit")  # 美
        assert glow.pillar == Pillar.BEAUTY
        assert glow.score == 0.75

    def test_to_custom_data(self) -> None:
        """Test customData conversion for Excalidraw."""
        from services.strategist_glow import Pillar, PillarGlow

        glow = PillarGlow.from_trinity_score(Pillar.TRUTH, 0.95, scale="unit")
        custom_data = glow.to_custom_data()

        assert "glow" in custom_data
        assert custom_data["glow"]["pillar"] == "truth"
        assert custom_data["glow"]["symbol"] == "\u771e"  # 眞
        assert custom_data["glow"]["score"] == pytest.approx(0.95, rel=0.01)
        assert custom_data["glow"]["level"] == "critical"
        assert "blur_radius" in custom_data["glow"]
        assert "opacity" in custom_data["glow"]
        assert "spread" in custom_data["glow"]


class TestGlowConfig:
    """Test GlowConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        from services.strategist_glow import GlowConfig, ThemeMode

        config = GlowConfig()
        assert config.theme == ThemeMode.DARK
        assert config.animation_enabled is False
        assert config.badge_enabled is True
        assert config.glow_enabled is True
        assert config.badge_size == 24

    def test_get_pillar_colors_dark_theme(self) -> None:
        """Test pillar colors in dark theme."""
        from services.strategist_glow import GlowConfig, Pillar, ThemeMode

        config = GlowConfig(theme=ThemeMode.DARK)
        primary, glow = config.get_pillar_colors(Pillar.TRUTH)

        assert primary.startswith("#")
        assert glow.startswith("#")

    def test_get_pillar_colors_light_theme(self) -> None:
        """Test pillar colors in light theme."""
        from services.strategist_glow import GlowConfig, Pillar, ThemeMode

        config = GlowConfig(theme=ThemeMode.LIGHT)
        primary, glow = config.get_pillar_colors(Pillar.TRUTH)

        assert primary.startswith("#")
        assert glow.startswith("#")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
