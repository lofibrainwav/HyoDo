"""
Evidence Bundle - 고도화된 증거 체인 관리 시스템

이 파일은 하위 호환성을 위한 래퍼입니다.
실제 구현은 AFO.evidence 모듈로 이동되었습니다.

Migration Guide:
    # Before
    from AFO.evidence_bundle import EvidenceBundle

    # After (recommended)
    from AFO.evidence import EvidenceBundle
"""

from AFO.evidence import (
    EvidenceBundle,
    EvidenceChain,
    MerkleTree,
    add_evidence_to_bundle,
    create_evidence_bundle,
    evidence_bundle,
    get_bundle_audit_trail,
    get_bundle_stats,
    seal_current_bundle,
    verify_bundle_integrity,
)

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
