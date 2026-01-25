"""
Evolution Types - TypedDict definitions for Auto Monitor system

DEBT-005: Type Coverage Improvement
Trinity Score: 眞 100% (Type Safety)
"""

from __future__ import annotations

from typing import TypedDict


class TrinityHealth(TypedDict, total=False):
    """Trinity health status."""

    score: float


class OrganHealth(TypedDict, total=False):
    """Organ health status."""

    status: str
    latency: float


class HealthMetrics(TypedDict, total=False):
    """Health metrics collected from monitoring."""

    trinity: TrinityHealth
    organs: dict[str, OrganHealth]
    status: str
    timestamp: str
    system_load: float
    memory_usage: float
    disk_usage: float
    network_status: str
    error: str


class StrategyAnalysis(TypedDict, total=False):
    """Analysis result from a single strategist."""

    technical_accuracy: float
    security_score: float
    ux_score: float
    issues_detected: list[str]
    recommendations: list[str]


class CouncilInsights(TypedDict, total=False):
    """Insights from Council of Minds analysis."""

    truth_analysis: StrategyAnalysis
    goodness_analysis: StrategyAnalysis
    beauty_analysis: StrategyAnalysis


class CouncilAnalysis(TypedDict, total=False):
    """Analysis result from Council of Minds."""

    analysis: str
    issues: list[str]
    recommendations: list[str]
    trinity_score: float
    council_insights: CouncilInsights
    analyzed_at: str
    error: str


class MonitoringCycleResult(TypedDict, total=False):
    """Result from a monitoring cycle."""

    success: bool
    metrics: HealthMetrics
    issues_count: int
    tickets_generated: int
    cycle_completed_at: str
    error: str
    cycle_failed_at: str


class IssueData(TypedDict, total=False):
    """Issue data for ticket generation."""

    title: str
    description: str
    severity: str
    category: str
    trinity_impact: float
    recommendations: list[str]
