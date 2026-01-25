"""
Evidence Types - TypedDict definitions for Evidence Bundle system

DEBT-005: Type Coverage Improvement
Trinity Score: 眞 100% (Type Safety)
"""

from __future__ import annotations

from typing import TypedDict


class EvidenceData(TypedDict, total=False):
    """Individual evidence item structure."""

    evidence_id: str
    source: str
    added_at: str
    validation_status: str  # "pending", "verified", "pending_review"
    trinity_score: float
    integrity_hash: str
    type: str
    reference: str


class BundleMetadata(TypedDict, total=False):
    """Evidence bundle metadata structure."""

    bundle_id: str
    created_at: str
    version: str
    trinity_score: float
    total_evidence: int
    merkle_root: str
    last_updated: str
    sealed_at: str
    chain_length: int
    final_trinity_score: float
    status: str  # "open", "sealed"


class SealResult(TypedDict):
    """Result from seal_bundle operation."""

    bundle_id: str
    sealed_at: str
    total_evidence: int
    merkle_root: str
    trinity_score: float
    status: str


class VerificationResult(TypedDict):
    """Result from verify_integrity operation."""

    bundle_integrity: bool
    chain_validity: bool
    merkle_consistency: bool
    evidence_count: int
    verified_at: str
    issues: list[str]


class DateRange(TypedDict):
    """Date range for chain."""

    start: str | None
    end: str | None


class ChainSummary(TypedDict):
    """Chain summary for audit trail."""

    total_links: int
    date_range: DateRange
    evidence_types: dict[str, int]


class TrinityMetrics(TypedDict):
    """Trinity score metrics for audit trail."""

    bundle_score: float
    evidence_scores: list[float]


class AuditTrail(TypedDict):
    """Audit trail structure."""

    bundle_id: str
    audit_timestamp: str
    chain_summary: ChainSummary
    trinity_metrics: TrinityMetrics
    integrity_status: VerificationResult
    merkle_root: str
    last_updated: str


class BundleStats(TypedDict):
    """Bundle statistics structure."""

    bundle_id: str
    status: str
    total_evidence: int
    sealed_evidence: int
    pending_evidence: int
    trinity_score: float
    merkle_root: str
    created_at: str
    last_updated: str
    evidence_sources: dict[str, int]


class QualityMetrics(TypedDict):
    """Quality metrics for Trinity Score evaluation (眞善美孝永)."""

    truth: float  # 眞 Truth
    goodness: float  # 善 Goodness
    beauty: float  # 美 Beauty
    serenity: float  # 孝 Serenity
    eternity: float  # 永 Eternity
