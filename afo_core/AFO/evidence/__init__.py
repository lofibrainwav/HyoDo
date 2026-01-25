"""
Evidence Module - 고도화된 증거 체인 관리 시스템

Julie CPA의 증거 번들을 암호화하고 Trinity Score로 가중치를 부여하며
무결성을 보장하는 완전한 증거 관리 시스템
"""

from typing import Any

from .bundle import EvidenceBundle
from .chain import EvidenceChain
from .merkle import MerkleTree

__all__ = [
    "EvidenceChain",
    "MerkleTree",
    "EvidenceBundle",
    "evidence_bundle",
    "create_evidence_bundle",
    "add_evidence_to_bundle",
    "seal_current_bundle",
    "verify_bundle_integrity",
    "get_bundle_audit_trail",
    "get_bundle_stats",
]

# 글로벌 인스턴스
evidence_bundle = EvidenceBundle()


# 편의 함수들
def create_evidence_bundle() -> EvidenceBundle:
    """새로운 Evidence Bundle 생성"""
    return EvidenceBundle()


def add_evidence_to_bundle(evidence_data: dict[str, Any], source: str = "manual") -> str:
    """글로벌 번들에 증거 추가"""
    return evidence_bundle.add_evidence(evidence_data, source)


def seal_current_bundle() -> dict[str, Any]:
    """현재 번들 봉인"""
    return evidence_bundle.seal_bundle()


def verify_bundle_integrity() -> dict[str, Any]:
    """번들 무결성 검증"""
    return evidence_bundle.verify_integrity()


def get_bundle_audit_trail() -> dict[str, Any]:
    """감사 추적 조회"""
    return evidence_bundle.get_audit_trail()


def get_bundle_stats() -> dict[str, Any]:
    """번들 통계 조회"""
    return evidence_bundle.get_bundle_stats()
