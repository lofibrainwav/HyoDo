"""
Trinity Score Sharing System - Backward Compatibility

이 파일은 모듈화된 trinity_score_sharing 패키지로의 역호환성을 제공합니다.
기존 import 경로를 유지하면서 새로운 모듈 구조를 사용할 수 있습니다.
"""

# 모듈화된 패키지에서 Lazy Import (성능 최적화 - Phase 74)
# 필요할 때만 import하여 초기 로드 시간 단축

# 역호환성을 위한 글로벌 변수들
__all__ = [
    "get_trinity_sharing_stats",
    "get_session_trinity_metrics",
    # Classes are available via __getattr__ for lazy loading
]


# 헬퍼 함수들 (기존 인터페이스 유지) - Lazy Import 적용
def get_trinity_sharing_stats() -> None:
    """공유 시스템 통계 조회 (역호환성)"""
    # Lazy import for performance optimization
    from .trinity_score_sharing import TrinityScoreSharingSystem

    system = TrinityScoreSharingSystem()
    return system.get_sharing_stats()


def get_session_trinity_metrics(session_id: str) -> None:
    """세션 Trinity 메트릭 조회 (역호환성)"""
    # Lazy import for performance optimization
    from .trinity_score_sharing import TrinityScoreSharingSystem

    system = TrinityScoreSharingSystem()
    return system.get_session_trinity_metrics(session_id)


# Lazy import wrapper for backward compatibility
def __getattr__(name: str) -> None:
    """Lazy import for backward compatibility classes"""
    lazy_classes = {
        "TrinityScoreSharingSystem",
        "TrinityScoreOptimizer",
        "TrinityScoreUpdate",
        "CollaborationMetrics",
    }

    if name in lazy_classes:
        from .trinity_score_sharing import (
            CollaborationMetrics,
            TrinityScoreOptimizer,
            TrinityScoreSharingSystem,
            TrinityScoreUpdate,
        )

        # Use dictionary for class mapping
        class_map = {
            "TrinityScoreSharingSystem": TrinityScoreSharingSystem,
            "TrinityScoreOptimizer": TrinityScoreOptimizer,
            "TrinityScoreUpdate": TrinityScoreUpdate,
            "CollaborationMetrics": CollaborationMetrics,
        }

        return class_map[name]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
