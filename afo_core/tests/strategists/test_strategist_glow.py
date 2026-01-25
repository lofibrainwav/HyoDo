# Trinity Score: 95.0 (Established by Chancellor)
"""Unit tests for Strategist Glow (PH-SE-05.03)

Trinity Layer & Strategist Glow visualization tests.
Tests Glow Schema, SVG filter generation, badge rendering, and theme support.

Trinity Score: 100% | 95% | 95%
- (Truth): Accurate schema and filter validation
- (Goodness): Theme compatibility verification
- (Beauty): Visual consistency tests

NOTE: This file is a thin re-export for backward compatibility.
      Tests have been split into separate files for 500-line rule compliance:
      - test_glow_schema.py: Pillar, ThemeMode, GlowIntensity, GlowConfig tests
      - test_glow_svg_badge.py: SVGFilterGenerator, PillarBadge tests
      - test_glow_manager.py: TrinityGlowManager, convenience function tests
      - test_glow_theme_integration.py: Theme support, DiagramGenerator integration tests
"""

from __future__ import annotations

# Re-export all test classes for backward compatibility
from tests.strategists.test_glow_manager import (
    TestConvenienceFunctions,
    TestTrinityGlowManager,
)
from tests.strategists.test_glow_schema import (
    TestGlowConfig,
    TestGlowIntensity,
    TestPillarColor,
    TestPillarEnum,
    TestPillarGlow,
    TestThemeMode,
)
from tests.strategists.test_glow_svg_badge import (
    TestPillarBadge,
    TestSVGFilterGenerator,
)
from tests.strategists.test_glow_theme_integration import (
    TestDarkLightThemeSupport,
    TestDiagramGeneratorIntegration,
    TestEdgeCases,
)

__all__ = [
    # Schema
    "TestPillarEnum",
    "TestThemeMode",
    "TestPillarColor",
    "TestGlowIntensity",
    "TestPillarGlow",
    "TestGlowConfig",
    # SVG & Badge
    "TestSVGFilterGenerator",
    "TestPillarBadge",
    # Manager
    "TestTrinityGlowManager",
    "TestConvenienceFunctions",
    # Theme & Integration
    "TestDarkLightThemeSupport",
    "TestDiagramGeneratorIntegration",
    "TestEdgeCases",
]
