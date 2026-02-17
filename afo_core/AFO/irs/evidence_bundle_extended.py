"""
Evidence Bundle - Evidence Bundle 시스템 확장

美 (Shin Saimdang): Evidence Bundle 확장
- IRS 변경사항 추적
- 메타인지 기록
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .hash_utils import HashUtils

logger = logging.getLogger(__name__)


@dataclass
class ChangeLog:
    """변경 로그 엔트리"""

    change_id: str
    document_id: str
    change_type: str  # "create", "update", "delete"
    previous_hash: str
    current_hash: str
    timestamp: str
    severity: str
    summary: str
    impact_areas: list[str] = field(default_factory=list)
    evidence_bundle_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "document_id": self.document_id,
            "change_type": self.change_type,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "summary": self.summary,
            "impact_areas": self.impact_areas,
            "evidence_bundle_id": self.evidence_bundle_id,
        }


@dataclass
class IRSChangeLog:
    """IRS 변경 로그"""

    document_id: str
    previous_version: str | None = None
    current_version: str | None = None
    publication_date: str | None = None
    rev_proc: str | None = None
    change_summary: str = ""
    affected_sections: list[str] = field(default_factory=list)
    impact_severity: str = ""  # "critical", "high", "medium", "low"
    evidence_bundle_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "previous_version": self.previous_version,
            "current_version": self.current_version,
            "publication_date": self.publication_date,
            "rev_proc": self.rev_proc,
            "change_summary": self.change_summary,
            "affected_sections": self.affected_sections,
            "impact_severity": self.impact_severity,
            "evidence_bundle_id": self.evidence_bundle_id,
        }


@dataclass
class TrinityScore:
    """Trinity Score (眞善美孝永) - Phase-aware weights

    HYOGOOK V5 (Phase 127+): 仁25% 眞22% 善18% 忠15% 美15%
    Legacy (Phase ≤126): 眞18% 善18% 美12% 孝40% 永12%
    """

    truth: float = 0.0
    goodness: float = 0.0
    beauty: float = 0.0
    serenity: float = 0.0  # Legacy: 孝 / HYOGOOK V5: 仁(benevolence)
    eternity: float = 0.0  # Legacy: 永 / HYOGOOK V5: 忠(loyalty)
    total: float = 0.0
    calculated_at: str = ""
    formula_version: str = "hyogook_v5"  # "weighted_v1" or "hyogook_v5"

    def to_dict(self) -> dict[str, Any]:
        return {
            "truth": self.truth,
            "goodness": self.goodness,
            "beauty": self.beauty,
            "serenity": self.serenity,
            "eternity": self.eternity,
            "total": self.total,
            "calculated_at": self.calculated_at,
            "formula_version": self.formula_version,
        }


@dataclass
class EvidenceBundleExtended:
    """확장된 Evidence Bundle"""

    # 기본 필드 (기존재)
    bundle_id: str
    timestamp: str
    created_at: str

    # 확장 필드 (TICKET-033 관련)
    change_logs: list[ChangeLog] = field(default_factory=list)
    trinity_score: dict[str, float] = field(default_factory=dict)
    irs_related: IRSChangeLog | None = None

    def to_dict(self) -> dict[str, Any]:
        base_dict = {
            "bundle_id": self.bundle_id,
            "timestamp": self.timestamp,
            "created_at": self.created_at,
            "change_logs": [log.to_dict() for log in self.change_logs],
            "trinity_score": self.trinity_score,
            "irs_related": self.irs_related.to_dict() if self.irs_related else None,
        }

        return base_dict

    def add_change_log(self, change_log: ChangeLog) -> str:
        """
        변경 로그 추가

        Args:
            change_log: 추가할 변경 로그

        Returns:
            bundle_id
        """
        self.change_logs.append(change_log)
        logger.debug(f"변경 로그 추가: {change_log.change_id}")

        return self.bundle_id

    def calculate_trinity_score(self, use_hyogook_v5: bool = True) -> dict[str, float | str]:
        """
        Trinity Score 계산 (Phase-aware)

        HYOGOOK V5 (Phase 127+): F = (T+G+In+B+C) + ⁵√(T×G×In×B×C)
        Legacy (Phase ≤126): F = T×0.18 + G×0.18 + B×0.12 + S×0.40 + E×0.12
        """
        import math

        serenity_score: float = 0.0
        benevolence_score: float = 0.0
        eternity_score: float = 0.0
        loyalty_score: float = 0.0

        if use_hyogook_v5:
            # HYOGOOK V5 Weights: 仁25% 眞22% 善18% 忠15% 美15%
            truth_weight = 0.22
            goodness_weight = 0.18
            beauty_weight = 0.15
            benevolence_weight = 0.25
            loyalty_weight = 0.15

            truth_score = self.trinity_score.get("truth", 0.18)
            goodness_score = self.trinity_score.get("goodness", 0.18)
            beauty_score = self.trinity_score.get("beauty", 0.12)
            benevolence_score = self.trinity_score.get("benevolence", 0.25)
            loyalty_score = self.trinity_score.get("loyalty", 0.15)

            weighted_sum = (
                truth_score * truth_weight
                + goodness_score * goodness_weight
                + beauty_score * beauty_weight
                + benevolence_score * benevolence_weight
                + loyalty_score * loyalty_weight
            )
            # S = ⁵√(T × G × In × B × C) - 기하평균 (永)
            geometric_mean = math.pow(
                truth_score * goodness_score * benevolence_score * beauty_score * loyalty_score,
                1 / 5,
            )
            total = weighted_sum + geometric_mean
            version = "hyogook_v5"
        else:
            # Legacy WEIGHTED_V1: 眞18% 善18% 美12% 孝40% 永12%
            truth_weight = 0.18
            goodness_weight = 0.18
            beauty_weight = 0.12
            serenity_weight = 0.40
            eternity_weight = 0.12

            truth_score = self.trinity_score.get("truth", 0.18)
            goodness_score = self.trinity_score.get("goodness", 0.18)
            beauty_score = self.trinity_score.get("beauty", 0.12)
            serenity_score = self.trinity_score.get("serenity", 0.40)
            eternity_score = self.trinity_score.get("eternity", 0.12)

            total = (
                truth_score * truth_weight
                + goodness_score * goodness_weight
                + beauty_score * beauty_weight
                + serenity_score * serenity_weight
                + eternity_score * eternity_weight
            )
            version = "weighted_v1"

        return {
            "眞": truth_score,
            "善": goodness_score,
            "美": beauty_score,
            "孝": serenity_score if not use_hyogook_v5 else benevolence_score,
            "永": eternity_score if not use_hyogook_v5 else loyalty_score,
            "total": total,
            "formula_version": version,
        }

    def verify_integrity(self) -> bool:
        """무결성 검증"""
        integrity_hash = self._calculate_bundle_hash()
        previous_hash = None

        for log in self.change_logs:
            if previous_hash is not None and log.previous_hash != integrity_hash:
                logger.warning("무결성 검증 실패: 해시 불일치")
                return False
            previous_hash = log.current_hash

        logger.debug("무결성 검증 완료: 모든 해시 일치")
        return True

    def _calculate_bundle_hash(self) -> str:
        """
        번들 해시 계산

        Returns:
            SHA256 해시 문자열
        """
        bundle_data = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False)
        bundle_hash = HashUtils.calculate_hash(bundle_data)

        logger.debug(f"번들 해시: {bundle_hash[:16]}...")

        return bundle_hash

    def export_to_json(self, output_path: Path | str) -> str:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Evidence Bundle 내보내기 완료: {output_path}")

        return str(output_path)

    def import_from_json(self, json_data: str | dict[str, Any]) -> str:
        """
        JSON에서 로드

        Args:
            json_data: JSON 데이터 또는 파일 경로

        Returns:
            bundle_id
        """
        import json

        # JSON 파일 또는 문자열인지 확인
        if isinstance(json_data, dict):
            data = json_data
        else:
            # 파일 경로인 경우 로드
            with open(json_data, encoding="utf-8") as f:
                data = json.load(f)

        # JSON 출력
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        output_path = f"data/evidence_bundle_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)

        # 속성 업데이트
        self.bundle_id = data.get("bundle_id", str(uuid4()))
        self.timestamp = data.get("timestamp", datetime.now().isoformat())
        self.created_at = data.get("created_at", datetime.now().isoformat())

        # 로그 변환
        self.change_logs = []
        for log_data in data.get("change_logs", []):
            log = ChangeLog(**log_data)
            self.change_logs.append(log)

        # Trinity Score
        trinity_data = data.get("trinity_score", {})
        self.trinity_score = trinity_data

        logger.info(f"Evidence Bundle 로드 완료: {output_path}")
        logger.info(f"bundle_id: {self.bundle_id}")

        return self.bundle_id


class EvidenceBundleManager:
    """Evidence Bundle 관리자"""

    STORAGE_PATH = Path("data/irs_monitor/evidence_bundles")

    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or EvidenceBundleManager.STORAGE_PATH

    def create_bundle(self) -> str:
        bundle = EvidenceBundleExtended(
            bundle_id=str(uuid4()),
            timestamp=datetime.now().isoformat(),
            created_at=datetime.now().isoformat(),
            trinity_score={},
            change_logs=[],
        )

        logger.info(f"Evidence Bundle 생성: {bundle.bundle_id}")

        self.storage_path.mkdir(parents=True, exist_ok=True)
        bundle_file = self.storage_path / f"{bundle.bundle_id}.json"
        bundle.export_to_json(bundle_file)

        return bundle.bundle_id

    def get_bundle(self, bundle_id: str) -> EvidenceBundleExtended | None:
        """
        Evidence Bundle 조회

        Args:
            bundle_id: Bundle ID

        Returns:
            Evidence Bundle 또는 None
        """
        bundle_file = self.storage_path / f"{bundle_id}.json"

        if not bundle_file.exists():
            logger.warning(f"Bundle 파일이 존재하지 않음: {bundle_file}")
            return None

        try:
            with open(bundle_file, encoding="utf-8") as f:
                data = json.load(f)

            bundle = EvidenceBundleExtended(**data)

            logger.info(f"Evidence Bundle 로드 완료: {bundle_id}")

            return bundle
        except Exception as e:
            logger.error(f"Bundle 로드 실패: {e}")
            return None

    def list_bundles(self, limit: int = 10) -> list[str]:
        """
        Evidence Bundle 목록 조회

        Args:
            limit: 최대 반환 수

        Returns:
            Bundle ID 리스트
        """
        bundles = []

        if not self.storage_path.exists():
            logger.warning("저장소스가 없음")
            return bundles

        try:
            for bundle_file in sorted(self.storage_path.glob("*.json"))[:limit]:
                with open(bundle_file, encoding="utf-8") as f:
                    data = json.load(f)

                if data.get("bundle_id"):
                    bundles.append(data["bundle_id"])

            logger.info(f"목록 완료: {len(bundles)}개 Bundle")

            return bundles
        except Exception as e:
            logger.error(f"목록 조회 실패: {e}")
            return []


# Convenience Functions
def create_evidence_bundle() -> str:
    """Evidence Bundle 생성 (편의 함수)"""
    manager = EvidenceBundleManager()
    return manager.create_bundle()


def get_evidence_bundle(bundle_id: str) -> EvidenceBundleExtended | None:
    """Evidence Bundle 조회 (편의 함수)"""
    manager = EvidenceBundleManager()
    return manager.get_bundle(bundle_id)


__all__ = [
    "ChangeLog",
    "IRSChangeLog",
    "TrinityScore",
    "EvidenceBundleExtended",
    "EvidenceBundleManager",
    "create_evidence_bundle",
    "get_evidence_bundle",
]
