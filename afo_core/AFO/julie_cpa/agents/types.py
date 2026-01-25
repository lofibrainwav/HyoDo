"""
Julie CPA Agent Type Definitions (DEBT-005: Type Coverage Improvement)

TypedDict definitions for common data structures used across Julie CPA agents.
Replaces dict[str, Any] with specific types for better type safety.

Trinity Score: 眞 100% (Type Safety)
"""

from __future__ import annotations

from typing import Any, TypedDict


# === Client Data Types ===
class ClientData(TypedDict, total=False):
    """Client information for tax analysis."""

    client_id: str
    name: str
    current_age: int
    filing_status: str
    annual_income: float
    deductions: float
    credits: float


class TaxDocument(TypedDict, total=False):
    """Tax document structure."""

    document_id: str
    document_type: str
    tax_year: int
    content: str
    metadata: dict[str, Any]


# === Workflow Phase Types ===
class ProcessingPhase(TypedDict, total=False):
    """Workflow processing phase tracking."""

    phase: str
    agent: str
    status: str
    trinity_score: float
    timestamp: str
    gate_decision: str | None
    certification_status: str | None
    confidence: float | None
    prediction_horizon: int | None


class AIEnhancement(TypedDict, total=False):
    """AI enhancement tracking."""

    type: str
    insights: int
    recommendations: int
    scenarios: int


# === Analysis Result Types ===
class DraftAnalysis(TypedDict, total=False):
    """Draft analysis from Associate agent."""

    assumptions: list[str]
    calculations: dict[str, float]
    confidence_level: float
    ai_insights: list[str]
    mathematical_validation: dict[str, Any]
    enhanced_confidence: float


class EvidenceLink(TypedDict, total=False):
    """Evidence link structure."""

    source: str
    url: str
    relevance: float
    citation: str


class MathematicalValidation(TypedDict, total=False):
    """Mathematical validation result."""

    is_valid: bool
    accuracy: float
    discrepancies: list[str]


class ClientAnalysis(TypedDict, total=False):
    """Claude client analysis result."""

    key_insights: list[str]
    compliance: dict[str, Any]
    risk_factors: list[str]


class HybridPrediction(TypedDict, total=False):
    """Gemini hybrid prediction result."""

    integrated_forecast_revenues: list[float]
    growth_rate: float
    confidence: float


class RiskScenario(TypedDict, total=False):
    """Risk scenario from prediction."""

    scenario_id: str
    description: str
    probability: float
    impact: str


class ConfidenceAssessment(TypedDict, total=False):
    """Confidence assessment result."""

    overall_confidence: float
    data_quality: float
    model_reliability: float


# === Agent Result Types ===
class AssociateResult(TypedDict, total=False):
    """Julie Associate Agent result."""

    draft_analysis: DraftAnalysis
    evidence_links: list[EvidenceLink]
    trinity_score: float


class ClaudeResult(TypedDict, total=False):
    """Claude Tax Assistant result."""

    client_analysis: ClientAnalysis
    ai_recommendations: list[str]
    evidence_links: list[EvidenceLink]
    trinity_score: float
    confidence_level: float
    mathematical_validation: MathematicalValidation


class ManagerResult(TypedDict, total=False):
    """Julie Manager Agent result."""

    gate_decision: str
    strategic_recommendations: list[str]
    trinity_score: float
    prediction_context: dict[str, Any] | None


class GeminiResult(TypedDict, total=False):
    """Gemini Financial Predictor result."""

    hybrid_prediction: HybridPrediction
    risk_scenarios: list[RiskScenario]
    strategic_recommendations: list[str]
    prediction_horizon: int
    trinity_score: float
    confidence_assessment: ConfidenceAssessment


class AuditorResult(TypedDict, total=False):
    """Julie Auditor Agent result."""

    certification_status: str
    compliance_notes: list[str]
    final_trinity_score: float


# === Final Result Types ===
class TrinityScores(TypedDict, total=False):
    """Individual Trinity scores from each agent."""

    associate: float
    claude: float
    manager: float
    gemini: float
    auditor: float


class ProcessingMetadata(TypedDict, total=False):
    """Processing metadata for workflow."""

    phase: str
    agents_used: list[str]
    ai_enhancements: list[str]
    confidence_level: str


class PredictionSummary(TypedDict, total=False):
    """Summary of prediction results."""

    prediction_horizon: int
    expected_growth: float
    risk_scenarios_count: int
    confidence_level: float


class FinalResults(TypedDict, total=False):
    """Final synthesized results."""

    overall_trinity_score: float
    individual_scores: TrinityScores
    key_insights: list[str]
    strategic_recommendations: list[str]
    certification_status: str
    compliance_status: str
    mathematical_validation: MathematicalValidation
    prediction_summary: PredictionSummary | None
    processing_metadata: ProcessingMetadata


class WorkflowResult(TypedDict, total=False):
    """Complete workflow result."""

    workflow_type: str
    client_id: str
    analysis_type: str
    processing_phases: list[ProcessingPhase]
    ai_enhancements: list[AIEnhancement]
    final_results: FinalResults
    trinity_score: float
    processing_timestamp: str
    status: str
    completion_timestamp: str
    error: str | None
    failure_timestamp: str | None


# === Historical Data Type ===
class HistoricalDataPoint(TypedDict):
    """Historical financial data point."""

    year: int
    income: float
    expenses: float
    investments: float
