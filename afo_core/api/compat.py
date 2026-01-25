"""AFO Kingdom Compatibility Wrapper (Backward Compatibility)

이 파일은 모듈화된 compat 패키지로의 역호환성을 제공합니다.
기존 import 경로를 유지하면서 새로운 모듈 구조를 사용할 수 있습니다.

Author: AFO Kingdom Development Team
Date: 2026-01-17
Version: 3.0.0 (Modularized Edition)
"""

# 모듈화된 compat 패키지에서 임포트
from api.compat.facade import HTMLDataFacade
from api.compat.metrics import TrinityMetrics
from api.compat.models import HTMLSectionData
from api.compat.providers import PhilosophyDataProvider, PortDataProvider
from api.compat.settings import get_settings_safe

# 역호환성을 위한 전역 export
__all__ = [
    # Models
    "HTMLSectionData",
    # Providers
    "PhilosophyDataProvider",
    "PortDataProvider",
    # Facades
    "HTMLDataFacade",
    # Utilities
    "get_settings_safe",
    # Metrics
    "TrinityMetrics",
]

# 사용 편의한함: 기존 compat 사용자 코드를 최소한 변경으로 최신 버전 마이그레이션
# 1. compat 패키지로부터만 import (compat_wrapper.py에서)
# 2. 모든 하위 패키지 임포트는 compat 패키지를 통해
# 3. compat 패키지 내부 구현은 compat 패키지 내부에서 참조
