"""
IRS Monitor Agent - 실시간 IRS 문서 모니터링 시스템

眞 (장영실 - Jang Yeong-sil): 아키텍처 설계
- IRS Monitor Agent 기본 구조
- 주요 문서 URL 모니터링
- 해시 기반 변경 감지
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MonitorConfig:
    """Monitor 설정"""

    # IRS URLs
    critical_documents: dict[str, str] = field(
        default_factory=lambda: {
            "publication_17": "https://www.irs.gov/pub/irs-pdf/p17.pdf",
            "rev_proc_2024_40": "https://www.irs.gov/pub/irs-drop/revproc/2024-40.pdf",
            "ftb_guidelines": "https://www.ftb.ca.gov/forms/2024/2024-1001.pdf",
        }
    )

    regular_documents: dict[str, str] = field(
        default_factory=lambda: {
            "notices": "https://www.irs.gov/newsroom/notices",
            "revenue_procedures": "https://www.irs.gov/businesses/corporations/revenue-procedures",
            "tax_legislation": "https://www.congress.gov/browse?collectionCode=PLAW&year=2025",
        }
    )

    # Monitoring Intervals
    critical_interval_hours: int = 6
    regular_interval_hours: int = 24

    # Hash Configuration
    hash_algorithm: str = "sha256"
    hash_encoding: str = "utf-8"

    # Thresholds
    max_retries: int = 3
    timeout_seconds: int = 30
    download_timeout_seconds: int = 300

    # Storage
    storage_path: str = "data/irs_monitor"
    history_retention_days: int = 365


@dataclass
class DocumentHash:
    """문서 해시 정보"""

    document_id: str
    document_url: str
    hash: str
    last_modified: str
    last_check: str
    size_bytes: int
    category: str  # "critical" or "regular"
    detected_changes: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_url": self.document_url,
            "hash": self.hash,
            "last_modified": self.last_modified,
            "last_check": self.last_check,
            "size_bytes": self.size_bytes,
            "category": self.category,
            "detected_changes": self.detected_changes,
        }


@dataclass
class ChangeDetection:
    """변경 감지 정보"""

    detection_id: str
    document_id: str
    previous_hash: str
    current_hash: str
    detected_at: str
    severity: str  # "critical", "high", "medium", "low"
    impact_areas: list[str] = field(default_factory=list)
    summary: str = ""
    evidence_bundle_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "document_id": self.document_id,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "detected_at": self.detected_at,
            "severity": self.severity,
            "impact_areas": self.impact_areas,
            "summary": self.summary,
            "evidence_bundle_id": self.evidence_bundle_id,
        }


class IRSMonitorAgent:
    """IRS Monitor Agent - 실시간 IRS 문서 모니터링"""

    def __init__(self, config: MonitorConfig | None = None) -> None:
        self.config = config or MonitorConfig()
        self.document_hashes: dict[str, DocumentHash] = {}
        self.change_detections: list[ChangeDetection] = []

        logger.info("IRS Monitor Agent 초기화 완료")
        logger.info(f"Critical Documents: {len(self.config.critical_documents)}개")
        logger.info(f"Regular Documents: {len(self.config.regular_documents)}개")

    def _calculate_hash(self, content: str | bytes) -> str:
        """문서 해시 계산 (SHA256)"""
        if isinstance(content, str):
            content = content.encode(self.config.hash_encoding)

        hash_obj = hashlib.new(self.config.hash_algorithm)
        hash_obj.update(content)
        return hash_obj.hexdigest()

    def _get_document_category(self, document_id: str) -> str:
        """문서 카테고리 반환"""
        if document_id in self.config.critical_documents:
            return "critical"
        elif document_id in self.config.regular_documents:
            return "regular"
        else:
            return "unknown"

    async def check_document_hash(self, document_id: str, document_url: str) -> DocumentHash | None:
        """단일 문서 해시 확인"""
        logger.info(f"문서 해시 확인 중: {document_id}")

        try:
            # TODO: 실제 다운로드 로직 구현 (crawler.py 통합)
            # 현재는 시뮬레이션
            content = f"simulated_content_{document_id}_{datetime.now().isoformat()}"

            current_hash = self._calculate_hash(content)
            category = self._get_document_category(document_id)

            # 기존 해시 확인
            previous_hash_obj = self.document_hashes.get(document_id)

            # 변경 감지 변수 초기화
            change_detection: ChangeDetection | None = None

            if previous_hash_obj:
                # 변경 감지
                if previous_hash_obj.hash != current_hash:
                    logger.warning(
                        f"🚨 변경 감지: {document_id} (이전: {previous_hash_obj.hash[:16]}..., 현재: {current_hash[:16]}...)"
                    )

                    change_detection = ChangeDetection(
                        detection_id=f"change-{document_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        document_id=document_id,
                        previous_hash=previous_hash_obj.hash,
                        current_hash=current_hash,
                        detected_at=datetime.now().isoformat(),
                        severity="critical" if category == "critical" else "medium",
                        summary=f"문서 {document_id} 변경 감지",
                    )

                    self.change_detections.append(change_detection)
                else:
                    logger.info(f"✅ 변경 없음: {document_id}")
            else:
                # 최초 등록
                logger.info(f"📝 최초 등록: {document_id}")

            # DocumentHash 생성
            detected_changes_list = (
                [change_detection.to_dict()] if change_detection is not None else []
            )

            document_hash = DocumentHash(
                document_id=document_id,
                document_url=document_url,
                hash=current_hash,
                last_modified=datetime.now().isoformat(),
                last_check=datetime.now().isoformat(),
                size_bytes=len(content),
                category=category,
                detected_changes=detected_changes_list,
            )

            self.document_hashes[document_id] = document_hash

            return document_hash

        except Exception as e:
            logger.error(f"❌ 문서 해시 확인 실패: {document_id}: {e}")
            return None

    async def check_all_documents(self) -> dict[str, Any]:
        """모든 문서 해시 확인"""
        logger.info("=" * 60)
        logger.info("IRS Monitor Agent: 모든 문서 해시 확인 시작")
        logger.info("=" * 60)

        start_time = datetime.now()
        all_documents = {
            **self.config.critical_documents,
            **self.config.regular_documents,
        }

        results = {
            "total_documents": len(all_documents),
            "checked_documents": 0,
            "failed_documents": 0,
            "changes_detected": len(self.change_detections),
            "document_hashes": [],
            "change_detections": [],
            "duration_seconds": 0.0,
            "timestamp": datetime.now().isoformat(),
        }

        # 모든 문서 확인
        tasks = [
            self.check_document_hash(doc_id, doc_url) for doc_id, doc_url in all_documents.items()
        ]

        checked_hashes = await asyncio.gather(*tasks)

        for hash_obj in checked_hashes:
            if hash_obj:
                results["checked_documents"] += 1
                results["document_hashes"].append(hash_obj.to_dict())
            else:
                results["failed_documents"] += 1

        # 변경 감지 결과
        for change_detection in self.change_detections:
            results["change_detections"].append(change_detection.to_dict())

        end_time = datetime.now()
        results["duration_seconds"] = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info("IRS Monitor Agent: 모든 문서 해시 확인 완료")
        logger.info(f"총 문서: {results['total_documents']}개")
        logger.info(f"확인 완료: {results['checked_documents']}개")
        logger.info(f"실패: {results['failed_documents']}개")
        logger.info(f"변경 감지: {results['changes_detected']}개")
        logger.info(f"소요 시간: {results['duration_seconds']:.2f}초")
        logger.info("=" * 60)

        return results

    async def start_monitoring(self, interval_hours: int | None = None) -> None:
        """모니터링 시작 (무한 루프)"""
        interval_hours = interval_hours or self.config.critical_interval_hours

        logger.info(f"IRS Monitor Agent 시작: {interval_hours}시간 간격")
        logger.info("Ctrl+C로 종료")

        try:
            while True:
                await self.check_all_documents()

                logger.info(
                    f"다음 확인까지 대기: {interval_hours}시간 ({timedelta(hours=interval_hours)})"
                )
                await asyncio.sleep(timedelta(hours=interval_hours).total_seconds())

        except KeyboardInterrupt:
            logger.info("IRS Monitor Agent 종료 요청")
        except Exception as e:
            logger.error(f"IRS Monitor Agent 오류: {e}")
            raise

    def get_detection_summary(self) -> dict[str, Any]:
        """변경 감지 요약 반환"""
        return {
            "total_detections": len(self.change_detections),
            "critical_detections": sum(
                1 for d in self.change_detections if d.severity == "critical"
            ),
            "high_detections": sum(1 for d in self.change_detections if d.severity == "high"),
            "medium_detections": sum(1 for d in self.change_detections if d.severity == "medium"),
            "low_detections": sum(1 for d in self.change_detections if d.severity == "low"),
            "detections": [d.to_dict() for d in self.change_detections],
        }


# Convenience Functions
async def check_irs_documents(config: MonitorConfig | None = None) -> dict[str, Any]:
    """IRS 문서 해시 확인 (편의 함수)"""
    agent = IRSMonitorAgent(config)
    return await agent.check_all_documents()


async def start_irs_monitoring(
    config: MonitorConfig | None = None, interval_hours: int | None = None
) -> None:
    """IRS 모니터링 시작 (편의 함수)"""
    agent = IRSMonitorAgent(config)
    await agent.start_monitoring(interval_hours)


__all__ = [
    "MonitorConfig",
    "DocumentHash",
    "ChangeDetection",
    "IRSMonitorAgent",
    "check_irs_documents",
    "start_irs_monitoring",
]
