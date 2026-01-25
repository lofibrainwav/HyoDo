"""
IRS Source Registry - 자동화된 IRS 문서 수집 및 인덱싱 시스템

이 파일은 하위 호환성을 위한 래퍼입니다.
실제 구현은 AFO.irs 모듈로 이동되었습니다.

Migration Guide:
    # Before
    from AFO.irs_source_registry import irs_source_registry

    # After (recommended)
    from AFO.irs import irs_source_registry
"""

from AFO.irs import (
    CollectionStats,
    IRSConfig,
    IRSCrawler,
    IRSIntegrations,
    IRSSourceRegistry,
    collect_irs_documents,
    get_irs_stats,
    irs_source_registry,
    start_irs_monitor,
)

__all__ = [
    "IRSSourceRegistry",
    "IRSCrawler",
    "IRSIntegrations",
    "IRSConfig",
    "CollectionStats",
    "irs_source_registry",
    "collect_irs_documents",
    "start_irs_monitor",
    "get_irs_stats",
]
