"""
Change Detector - 문서 변경 감지 엔진

眞 (장영실 - Jang Yeong-sil): 아키텍처 설계
- 해시 기반 변경 감지
- 영향도 평가
- 변경사항 분류
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .hash_utils import HashUtils

logger = logging.getLogger(__name__)


@dataclass
class ChangeImpact:
    """변경 영향도"""

    category: str  # "critical", "high", "medium", "low"
    score: float  # 0.0 ~ 1.0
    areas: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "score": self.score,
            "areas": self.areas,
            "description": self.description,
        }


@dataclass
class ChangeSummary:
    """변경 요약"""

    change_id: str
    document_id: str
    previous_hash: str
    current_hash: str
    detected_at: str
    impact: ChangeImpact
    document_type: str = ""  # IRS 문서 타입 (예: "IRS Publication 17")
    changes: dict[str, Any] = field(default_factory=dict)
    evidence_bundle_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "document_id": self.document_id,
            "document_type": self.document_type,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "detected_at": self.detected_at,
            "impact": self.impact.to_dict(),
            "changes": self.changes,
            "evidence_bundle_id": self.evidence_bundle_id,
        }


class ChangeDetector:
    """변경 감지 엔진"""

    CRITICAL_KEYWORDS = {
        "energy_credit": ["energy", "credit", "2034", "2025", "expiration", "deadline"],
        "ev_credit": ["electric", "vehicle", "credit", "2025", "9", "30", "expiration"],
        "bonus_depreciation": ["bonus", "depreciation", "100%", "100", "january", "permanent"],
        "erc_refund": ["erc", "refund", "2024", "january", "31", "deadline"],
    }

    def __init__(self, hash_algorithm: str = "sha256") -> None:
        self.hash_algorithm = hash_algorithm
        logger.info("Change Detector 초기화 완료")

    def detect_change(
        self,
        previous_content: str,
        current_content: str,
        document_id: str,
    ) -> ChangeSummary | None:
        """
        변경 감지

        Args:
            previous_content: 이전 콘텐츠
            current_content: 현재 콘텐츠
            document_id: 문서 ID

        Returns:
            ChangeSummary 또는 None (변경 없음)
        """
        # 해시 계산
        previous_hash = HashUtils.calculate_hash(previous_content, self.hash_algorithm)
        current_hash = HashUtils.calculate_hash(current_content, self.hash_algorithm)

        # 해시 비교
        hash_comparison = HashUtils.compare_hashes(previous_hash, current_hash, self.hash_algorithm)

        if hash_comparison["equal"]:
            logger.info(f"✅ 변경 없음: {document_id}")
            return None

        # 변경 감지
        logger.warning(f"🚨 변경 감지: {document_id} (diff_bits={hash_comparison['diff_bits']})")

        # 영향도 평가
        impact = self._assess_impact(
            previous_content,
            current_content,
            document_id,
        )

        # 변경 요약 생성
        change_summary = ChangeSummary(
            change_id=f"change-{document_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            document_id=document_id,
            previous_hash=previous_hash,
            current_hash=current_hash,
            detected_at=datetime.now().isoformat(),
            impact=impact,
            changes={
                "hash_diff": hash_comparison,
            },
        )

        return change_summary

    def _assess_impact(
        self,
        previous_content: str,
        current_content: str,
        document_id: str,
    ) -> ChangeImpact:
        """
        영향도 평가

        Args:
            previous_content: 이전 콘텐츠
            current_content: 현재 콘텐츠
            document_id: 문서 ID

        Returns:
            ChangeImpact
        """
        # 키워드 기반 영향도 평가
        impact_areas = []
        impact_score = 0.0

        # 주요 키워드 검색
        for category, keywords in self.CRITICAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in current_content.lower():
                    impact_areas.append(f"{category}_{keyword}")

        # 영향도 계산
        impact_score = min(len(impact_areas) * 0.2, 1.0) if impact_areas else 0.1

        # 카테고리 결정
        if impact_score >= 0.8:
            category = "critical"
        elif impact_score >= 0.6:
            category = "high"
        elif impact_score >= 0.3:
            category = "medium"
        else:
            category = "low"

        impact = ChangeImpact(
            category=category,
            score=impact_score,
            areas=impact_areas,
            description=f"영향도: {category} (score: {impact_score:.2f})",
        )

        logger.debug(
            f"영향도 평가: {document_id}, category={category}, "
            f"score={impact_score:.2f}, areas={len(impact_areas)}"
        )

        return impact

    def batch_detect_changes(
        self,
        documents: dict[str, dict[str, str]],
    ) -> list[ChangeSummary]:
        """
        배치 변경 감지

        Args:
            documents: 문서 딕셔너리
                {
                    "document_id": {
                        "previous": "previous_content",
                        "current": "current_content",
                    },
                }

        Returns:
            ChangeSummary 리스트
        """
        results = []

        for doc_id, doc_contents in documents.items():
            previous_content = doc_contents.get("previous", "")
            current_content = doc_contents.get("current", "")

            if not previous_content or not current_content:
                logger.warning(f"⚠️ 콘텐츠 없음: {doc_id}")
                continue

            change_summary = self.detect_change(previous_content, current_content, doc_id)

            if change_summary:
                results.append(change_summary)

        logger.info(f"배치 변경 감지 완료: {len(results)}개 변경 감지")

        return results


# Convenience Functions
def detect_change(
    previous_content: str,
    current_content: str,
    document_id: str,
    hash_algorithm: str = "sha256",
) -> ChangeSummary | None:
    """변경 감지 (편의 함수)"""
    detector = ChangeDetector(hash_algorithm)
    return detector.detect_change(previous_content, current_content, document_id)


def batch_detect_changes(
    documents: dict[str, dict[str, str]],
    hash_algorithm: str = "sha256",
) -> list[ChangeSummary]:
    """배치 변경 감지 (편의 함수)"""
    detector = ChangeDetector(hash_algorithm)
    return detector.batch_detect_changes(documents)


# Alias for backward compatibility
ChangeDetection = ChangeSummary

__all__ = [
    "ChangeDetection",
    "ChangeImpact",
    "ChangeSummary",
    "ChangeDetector",
    "detect_change",
    "batch_detect_changes",
]
