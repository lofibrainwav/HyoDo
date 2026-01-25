"""Settings Module

안전한 설정 조회 유틸리티.
"""


def get_settings_safe() -> None:
    """안전한 설정 조회 함수 (fallback 지원)"""
    try:
        from AFO.config.settings import settings

        return settings
    except ImportError:
        return None
