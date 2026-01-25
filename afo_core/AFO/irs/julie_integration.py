"""Julie CPA Integration - Refactored Wrapper.

Original code moved to: AFO/irs/julie_integration/
"""

from .julie_integration import (
    AlertPriority,
    CustomerImpact,
    JulieAlert,
    JulieCPAIntegrator,
)

__all__ = ["JulieCPAIntegrator", "JulieAlert", "AlertPriority", "CustomerImpact"]
