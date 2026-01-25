"""
Evidence Bundle - 고도화된 증거 번들 관리 시스템

Julie CPA의 증거 번들을 암호화하고 Trinity Score로 가중치를 부여하며
무결성을 보장하는 완전한 증거 관리 시스템
"""

import hashlib
import json
import logging
import time
from datetime import datetime

from .chain import EvidenceChain
from .merkle import MerkleTree
from .types import (
    AuditTrail,
    BundleMetadata,
    BundleStats,
    DateRange,
    EvidenceData,
    SealResult,
    VerificationResult,
)

logger = logging.getLogger(__name__)


class EvidenceBundle:
    """고도화된 Evidence Bundle 시스템"""

    def __init__(self) -> None:
        self.chain: list[EvidenceChain] = []
        self.pending_evidence: list[EvidenceData] = []
        self.bundle_metadata: BundleMetadata = {
            "bundle_id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
            "created_at": datetime.now().isoformat(),
            "version": "2.0.0",
            "trinity_score": 0.0,
            "total_evidence": 0,
            "merkle_root": "",
            "last_updated": datetime.now().isoformat(),
        }

        # Trinity Score 가중치 설정
        self.trinity_weights = {
            "眞": 0.35,  # Truth - 기술적 정확성
            "善": 0.35,  # Goodness - 윤리적 타당성
            "美": 0.20,  # Beauty - 구조적 일관성
            "孝": 0.08,  # Serenity - 평온한 검증
            "永": 0.02,  # Eternity - 장기적 유효성
        }

    def add_evidence(self, evidence_data: EvidenceData, source: str = "manual") -> str:
        """증거 추가 및 체인에 연결"""

        # 증거 메타데이터 강화
        enriched_evidence = {
            **evidence_data,
            "evidence_id": hashlib.sha256(f"{evidence_data}{time.time()}".encode()).hexdigest(),
            "added_at": datetime.now().isoformat(),
            "source": source,
            "validation_status": "pending",
            "trinity_score": 0.0,
            "integrity_hash": self._calculate_integrity_hash(evidence_data),
        }

        # Trinity Score 평가
        trinity_score = self._evaluate_evidence_trinity_score(enriched_evidence)
        enriched_evidence["trinity_score"] = trinity_score

        # 검증 상태 업데이트
        enriched_evidence["validation_status"] = (
            "verified" if trinity_score >= 0.7 else "pending_review"
        )

        # 대기열에 추가
        self.pending_evidence.append(enriched_evidence)

        # 번들 메타데이터 업데이트
        self.bundle_metadata["total_evidence"] = len(self.pending_evidence)
        self.bundle_metadata["last_updated"] = datetime.now().isoformat()

        return enriched_evidence["evidence_id"]

    def _calculate_integrity_hash(self, evidence_data: EvidenceData) -> str:
        """증거 데이터 무결성 해시 계산"""
        # 민감한 필드 제외하고 해시 계산
        sanitized_data = self._sanitize_evidence_data(evidence_data)
        data_string = json.dumps(sanitized_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def _sanitize_evidence_data(self, evidence_data: EvidenceData) -> EvidenceData:
        """민감한 정보 제거"""
        sanitized = evidence_data.copy()

        # 민감한 키들 제거 또는 마스킹
        sensitive_keys = ["password", "secret", "key", "token", "ssn", "ein"]
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "***REDACTED***"

        return sanitized

    def _evaluate_evidence_trinity_score(self, evidence: EvidenceData) -> float:
        """증거에 대한 Trinity Score 평가"""

        # 증거 품질 평가 기준
        quality_metrics = {
            "眞": self._evaluate_truth(evidence),  # 기술적 정확성
            "善": self._evaluate_goodness(evidence),  # 윤리적 타당성
            "美": self._evaluate_beauty(evidence),  # 구조적 일관성
            "孝": self._evaluate_serenity(evidence),  # 평온한 검증
            "永": self._evaluate_eternity(evidence),  # 장기적 유효성
        }

        # 가중치 적용
        trinity_score = sum(
            score * self.trinity_weights[pillar] for pillar, score in quality_metrics.items()
        )

        return round(trinity_score, 3)

    def _evaluate_truth(self, evidence: EvidenceData) -> float:
        """眞(Truth) - 기술적 정확성 평가"""
        score = 0.8  # 기본 점수

        # 데이터 완전성 확인
        required_fields = ["evidence_id", "source", "added_at"]
        if all(field in evidence for field in required_fields):
            score += 0.1

        # 해시 무결성 확인
        if evidence.get("integrity_hash"):
            score += 0.1

        return min(score, 1.0)

    def _evaluate_goodness(self, evidence: EvidenceData) -> float:
        """善(Goodness) - 윤리적 타당성 평가"""
        score = 0.9  # 기본 점수

        # 민감 정보 처리 확인
        if self._sanitize_evidence_data(evidence) != evidence:
            # 민감 정보가 적절히 처리됨
            score += 0.1

        # 출처 신뢰성 확인
        trusted_sources = ["irs", "aicpa", "court", "official"]
        source = evidence.get("source", "").lower()
        if any(trusted in source for trusted in trusted_sources):
            score += 0.1

        return min(score, 1.0)

    def _evaluate_beauty(self, evidence: EvidenceData) -> float:
        """美(Beauty) - 구조적 일관성 평가"""
        score = 0.85  # 기본 점수

        # 데이터 구조 일관성
        if isinstance(evidence, dict) and len(evidence) > 3:
            score += 0.1

        # 메타데이터 완전성
        metadata_fields = ["evidence_id", "added_at", "trinity_score"]
        if all(field in evidence for field in metadata_fields):
            score += 0.1

        return min(score, 1.0)

    def _evaluate_serenity(self, evidence: EvidenceData) -> float:
        """孝(Serenity) - 평온한 검증 평가"""
        score = 0.95  # 기본 점수 (증거 검증은 일반적으로 평온함)

        # 검증 상태 확인
        validation_status = evidence.get("validation_status", "unknown")
        if validation_status in ["verified", "approved"]:
            score += 0.05

        return min(score, 1.0)

    def _evaluate_eternity(self, evidence: EvidenceData) -> float:
        """永(Eternity) - 장기적 유효성 평가"""
        score = 0.8  # 기본 점수

        # 시간 기반 유효성 (최근 데이터 선호)
        added_at = evidence.get("added_at")
        if added_at:
            try:
                added_date = datetime.fromisoformat(added_at)
                days_old = (datetime.now() - added_date).days

                # 1년 이내 데이터는 높은 점수
                if days_old <= 365:
                    score += 0.1
                elif days_old <= 730:  # 2년 이내
                    score += 0.05

            except ValueError:
                pass  # 날짜 파싱 실패 시 기본 점수 유지

        # 데이터 영속성 (ID 존재 확인)
        if evidence.get("evidence_id"):
            score += 0.1

        return min(score, 1.0)

    def seal_bundle(self) -> SealResult:
        """Evidence Bundle 봉인 및 최종화"""

        if not self.pending_evidence:
            raise ValueError("No evidence to seal")

        # Merkle Tree 생성
        evidence_hashes = [ev["integrity_hash"] for ev in self.pending_evidence]
        merkle_tree = MerkleTree(evidence_hashes)

        # 증거 체인 생성
        previous_hash = self.chain[-1].hash if self.chain else None

        for evidence in self.pending_evidence:
            chain_link = EvidenceChain(evidence, previous_hash)
            self.chain.append(chain_link)
            previous_hash = chain_link.hash

        # 번들 메타데이터 최종화
        self.bundle_metadata.update(
            {
                "sealed_at": datetime.now().isoformat(),
                "merkle_root": merkle_tree.get_root(),
                "chain_length": len(self.chain),
                "final_trinity_score": self._calculate_bundle_trinity_score(),
                "status": "sealed",
            }
        )

        # 대기열 비우기
        self.pending_evidence.clear()

        return {
            "bundle_id": self.bundle_metadata["bundle_id"],
            "sealed_at": self.bundle_metadata["sealed_at"],
            "total_evidence": self.bundle_metadata["chain_length"],
            "merkle_root": self.bundle_metadata["merkle_root"],
            "trinity_score": self.bundle_metadata["final_trinity_score"],
            "status": "sealed",
        }

    def _calculate_bundle_trinity_score(self) -> float:
        """번들 전체 Trinity Score 계산"""

        if not self.chain:
            return 0.0

        # 각 증거의 Trinity Score 평균
        evidence_scores = [link.evidence_data.get("trinity_score", 0) for link in self.chain]
        average_score = sum(evidence_scores) / len(evidence_scores)

        # 체인 무결성 보너스
        integrity_bonus = min(len(self.chain) * 0.01, 0.1)  # 최대 10% 보너스

        return round(min(average_score + integrity_bonus, 1.0), 3)

    def verify_integrity(self) -> VerificationResult:
        """번들 무결성 검증"""

        verification_results = {
            "bundle_integrity": True,
            "chain_validity": True,
            "merkle_consistency": True,
            "evidence_count": len(self.chain),
            "verified_at": datetime.now().isoformat(),
            "issues": [],
        }

        # 체인 유효성 검증
        for i, link in enumerate(self.chain):
            # 해시 재계산
            recalculated_hash = link._calculate_hash()

            if recalculated_hash != link.hash:
                verification_results["chain_validity"] = False
                verification_results["issues"].append(f"Chain link {i} hash mismatch")

            # 이전 해시 연결성 검증
            if i > 0 and link.previous_hash != self.chain[i - 1].hash:
                verification_results["chain_validity"] = False
                verification_results["issues"].append(f"Chain link {i} previous hash mismatch")

        # Merkle Tree 일관성 검증
        if self.bundle_metadata.get("merkle_root"):
            current_hashes = [link.evidence_data["integrity_hash"] for link in self.chain]
            current_tree = MerkleTree(current_hashes)
            current_root = current_tree.get_root()

            if current_root != self.bundle_metadata["merkle_root"]:
                verification_results["merkle_consistency"] = False
                verification_results["issues"].append("Merkle root mismatch")

        # 전체 무결성
        verification_results["bundle_integrity"] = all(
            [verification_results["chain_validity"], verification_results["merkle_consistency"]]
        )

        return verification_results

    def get_audit_trail(self) -> AuditTrail:
        """감사 추적 생성"""

        return {
            "bundle_id": self.bundle_metadata["bundle_id"],
            "audit_timestamp": datetime.now().isoformat(),
            "chain_summary": {
                "total_links": len(self.chain),
                "date_range": self._get_chain_date_range(),
                "evidence_types": self._count_evidence_types(),
            },
            "trinity_metrics": {
                "bundle_score": self.bundle_metadata.get("final_trinity_score", 0),
                "evidence_scores": [
                    link.evidence_data.get("trinity_score", 0) for link in self.chain
                ],
            },
            "integrity_status": self.verify_integrity(),
            "merkle_root": self.bundle_metadata.get("merkle_root", ""),
            "last_updated": self.bundle_metadata.get("last_updated", ""),
        }

    def _get_chain_date_range(self) -> DateRange:
        """체인 날짜 범위 계산"""

        if not self.chain:
            return {"start": None, "end": None}

        timestamps = [link.timestamp for link in self.chain]
        return {"start": min(timestamps), "end": max(timestamps)}

    def _count_evidence_types(self) -> dict[str, int]:
        """증거 타입별 개수 계산"""

        type_counts: dict[str, int] = {}
        for link in self.chain:
            evidence_type = link.evidence_data.get("source", "unknown")
            type_counts[evidence_type] = type_counts.get(evidence_type, 0) + 1

        return type_counts

    def export_bundle(self, filepath: str) -> bool:
        """번들 내보내기 (JSON 형식)"""

        try:
            bundle_data = {
                "metadata": self.bundle_metadata,
                "chain": [
                    {
                        "hash": link.hash,
                        "timestamp": link.timestamp,
                        "previous_hash": link.previous_hash,
                        "evidence_data": link.evidence_data,
                        "nonce": link.nonce,
                    }
                    for link in self.chain
                ],
                "pending_evidence": self.pending_evidence,
                "export_timestamp": datetime.now().isoformat(),
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(bundle_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Bundle export failed: {e}")
            return False

    def import_bundle(self, filepath: str) -> bool:
        """번들 불러오기"""

        try:
            with open(filepath, encoding="utf-8") as f:
                bundle_data = json.load(f)

            # 메타데이터 복원
            self.bundle_metadata = bundle_data.get("metadata", {})

            # 체인 복원
            self.chain = []
            for link_data in bundle_data.get("chain", []):
                # EvidenceChain 객체 재생성
                link = EvidenceChain.__new__(EvidenceChain)
                link.hash = link_data["hash"]
                link.timestamp = link_data["timestamp"]
                link.previous_hash = link_data["previous_hash"]
                link.evidence_data = link_data["evidence_data"]
                link.nonce = link_data["nonce"]
                self.chain.append(link)

            # 대기 증거 복원
            self.pending_evidence = bundle_data.get("pending_evidence", [])

            return True

        except Exception as e:
            logger.error(f"Bundle import failed: {e}")
            return False

    def get_bundle_stats(self) -> BundleStats:
        """번들 통계 정보"""

        return {
            "bundle_id": self.bundle_metadata["bundle_id"],
            "status": self.bundle_metadata.get("status", "open"),
            "total_evidence": len(self.chain) + len(self.pending_evidence),
            "sealed_evidence": len(self.chain),
            "pending_evidence": len(self.pending_evidence),
            "trinity_score": self.bundle_metadata.get("final_trinity_score", 0),
            "merkle_root": self.bundle_metadata.get("merkle_root", ""),
            "created_at": self.bundle_metadata["created_at"],
            "last_updated": self.bundle_metadata.get("last_updated", ""),
            "evidence_sources": self._count_evidence_types() if self.chain else {},
        }
