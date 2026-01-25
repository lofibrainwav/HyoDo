# Trinity Score: 90.0 (Established by Chancellor)
"""
AICPA Module - 에이전트 군단
"""

from AFO.aicpa.report_generator import (
    generate_email_draft,
    generate_quickbooks_csv,
    generate_strategy_report,
    generate_turbotax_csv,
)
from AFO.aicpa.service import AICPAService, get_aicpa_service
from AFO.aicpa.tax_engine import (
    FilingStatus,
    TaxInput,
    TaxResult,
    calculate_ca_state_tax,
    calculate_federal_tax,
    calculate_tax,
    check_irmaa_risk,
    simulate_roth_ladder,
)

__all__ = [
    # Service
    "AICPAService",
    "FilingStatus",
    # Tax Engine
    "TaxInput",
    "TaxResult",
    "calculate_ca_state_tax",
    "calculate_federal_tax",
    "calculate_tax",
    "check_irmaa_risk",
    "generate_email_draft",
    "generate_quickbooks_csv",
    # Report Generator
    "generate_strategy_report",
    "generate_turbotax_csv",
    "get_aicpa_service",
    "simulate_roth_ladder",
]
