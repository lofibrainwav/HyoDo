"""Chart Generation System - Refactored Wrapper.

This file is now a wrapper around the modularized chart_generation package.
Original code moved to: AFO/julie_cpa/agents/chart_generation/
"""

from .chart_generation import (
    CHART_TYPES,
    COLORS,
    CPAChartGenerationSystem,
    generate_tax_visualization_charts,
)

__all__ = [
    "CPAChartGenerationSystem",
    "generate_tax_visualization_charts",
    "CHART_TYPES",
    "COLORS",
]
