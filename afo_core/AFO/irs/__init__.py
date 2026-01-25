"""
IRS Source Registry Module

IRS 문서 자동 수집 및 인덱싱 시스템
"""

from typing import Any

from .crawler import IRSCrawler
from .integrations import IRSIntegrations
from .models import CollectionStats, IRSConfig
from .registry import IRSSourceRegistry

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

# 글로벌 인스턴스
irs_source_registry = IRSSourceRegistry()


# 편의 함수들
async def collect_irs_documents() -> dict[str, Any]:
    """IRS 문서 수집 실행"""
    return await irs_source_registry.collect_all_sources()


async def start_irs_monitor() -> None:
    """IRS 모니터링 시작"""
    await irs_source_registry.monitor_updates()


def get_irs_stats() -> dict[str, Any]:
    """IRS 통계 조회"""
    return irs_source_registry.get_collection_stats()
