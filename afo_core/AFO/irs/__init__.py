"""
IRS Source Registry Module

IRS 문서 자동 수집 및 인덱싱 시스템
"""

from typing import Any

# Legacy modules (existing)
from .crawler import IRSCrawler
from .integrations import IRSIntegrations
from .models import CollectionStats, IRSConfig
from .registry import IRSSourceRegistry

# New monitoring modules (TICKET-114)
from .document_crawler import DownloadResult, IRSDocumentCrawler, IRS_BASE_URL
from .hash_verifier import HashAlgorithm, HashResult, HashVerifier
from .change_detector import (
    ChangeImpact,
    ChangeSummary,
    ChangeDetector,
    detect_change,
    batch_detect_changes,
)
from .notification_service import NotificationChannel, Notification, NotificationService
from .irs_monitor_agent import (
    MonitorConfig,
    DocumentHash,
    ChangeDetection,
    IRSMonitorAgent,
    check_irs_documents,
    start_irs_monitoring,
)

__all__ = [
    # Legacy
    "IRSSourceRegistry",
    "IRSCrawler",
    "IRSIntegrations",
    "IRSConfig",
    "CollectionStats",
    "irs_source_registry",
    "collect_irs_documents",
    "start_irs_monitor",
    "get_irs_stats",
    # New Crawler
    "DownloadResult",
    "IRSDocumentCrawler",
    "IRS_BASE_URL",
    # Hash Verifier
    "HashAlgorithm",
    "HashResult",
    "HashVerifier",
    # Change Detector
    "ChangeImpact",
    "ChangeSummary",
    "ChangeDetector",
    "detect_change",
    "batch_detect_changes",
    # Notification
    "NotificationChannel",
    "Notification",
    "NotificationService",
    # Monitor Agent
    "MonitorConfig",
    "DocumentHash",
    "ChangeDetection",
    "IRSMonitorAgent",
    "check_irs_documents",
    "start_irs_monitoring",
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
