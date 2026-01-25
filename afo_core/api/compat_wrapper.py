"""AFO Kingdom Compatibility Wrapper (Backward Compatibility)

이 파일은 모듈화된 compat 패키지로의 역호환성을 제공합니다.
기존 import 경로를 깨끊는 새로운 compat_wrapper 패키지로 호환성을 보장합니다.

Author: AFO Kingdom Development Team
Date: 2026-01-17
Version: 3.0.0 (Backward Compatibility Edition)
"""

# 모듈화된 compat 패키지에서 임포트
from .facade import HTMLDataFacade
from .metrics import TrinityMetrics
from .models import HTMLSectionData
from .providers import PhilosophyDataProvider, PortDataProvider
from .settings import get_settings_safe

# 역호환성을 위한 글로벌 변수들
__all__ = [
    # Convenience exports (기존 호환성 유지)
    "HTMLSectionData",
    "PhilosophyDataProvider",
    "PortDataProvider",
    "HTMLDataFacade",
    "get_settings_safe",
    "TrinityMetrics",
    # Core classes (새 패키지 구조)
    "HTMLDataFacade",
    "TrinityMetrics",
]

# 사용 편의한함: 기존 compat 사용자 코드는 compat.py가 아직 참조함
# compat_wrapper는 새 패키지 구조의 진입점 역할을 함
# compat.py는 import error 발생시 compat_wrapper로 자동 fallback됨
