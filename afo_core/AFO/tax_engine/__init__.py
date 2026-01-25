"""SSOT 기반 미국 세금 엔진 (2025년 연방세 + 캘리포니아 주세)

SSOT Sources:
- Federal: IRS Publication 17, Rev. Proc. 2024-40
- CA: FTB 2025 Tax Rate Schedules, EDD DE-4

이 모듈은 공식 세법 문서를 SSOT로 사용하여 정확한 세금 계산을 제공합니다.
"""

from .calculator import TaxCalculator
from .loader import TaxParameterLoader
from .validator import validate_tax_params_2025

__all__ = ["TaxCalculator", "TaxParameterLoader", "validate_tax_params_2025"]
