"""
Gateway API Pydantic Models
TICKET-115: Tax Analysis & Intelligence Endpoints (L3)
TICKET-110: IRS 모니터링 API
"""

from pydantic import BaseModel, Field


class TaxAnalysisRequest(BaseModel):
    """세무 문서 분석 요청 모델"""

    document_text: str = Field(
        ...,
        min_length=10,
        max_length=100000,
        description="분석할 세무 문서 텍스트",
        examples=["2025년 세무 보고서: 총 수입 $150,000, 사업 비용 $45,000..."],
    )
    document_type: str = Field(
        default="general",
        description="문서 유형",
        examples=["tax_return", "financial_statement", "irs_notice", "business_expense"],
    )
    analysis_focus: list[str] = Field(
        default_factory=lambda: ["compliance", "optimization"],
        description="분석 초점",
        examples=[["compliance", "optimization", "risk_assessment"]],
    )
    priority: str = Field(
        default="normal", description="처리 우선순위", examples=["low", "normal", "high", "urgent"]
    )


class TaxAnalysisResponse(BaseModel):
    """세무 문서 분석 응답 모델"""

    analysis_id: str = Field(..., description="분석 고유 ID")
    document_type: str = Field(..., description="감지된 문서 유형")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="준수 점수 (%)")
    risk_level: str = Field(..., description="위험 수준")
    optimization_opportunities: list[dict[str, object]] = Field(
        default_factory=list, description="최적화 기회 목록"
    )
    key_findings: list[str] = Field(default_factory=list, description="주요 발견사항")
    recommendations: list[str] = Field(default_factory=list, description="권장 조치사항")
    evidence_bundle_id: str = Field(..., description="증거 번들 ID")
    trinity_score: dict[str, float] = Field(..., description="Trinity Score 세부사항")
    processing_time: float = Field(..., description="처리 시간 (초)")
    analyzed_at: str = Field(..., description="분석 시각")


class TaxReviewRequest(BaseModel):
    """세무 보고서 리뷰 요청 모델"""

    tax_return_data: dict[str, object] = Field(
        ...,
        description="세무 보고서 데이터",
        examples=[
            {
                "filing_status": "SINGLE",
                "gross_income": 150000,
                "deductions": 25000,
                "credits": 5000,
            }
        ],
    )
    review_type: str = Field(
        default="comprehensive",
        description="리뷰 유형",
        examples=["comprehensive", "quick_check", "audit_prep"],
    )
    include_benchmarks: bool = Field(default=True, description="벤치마크 비교 포함 여부")


class TaxReviewResponse(BaseModel):
    """세무 보고서 리뷰 응답 모델"""

    review_id: str = Field(..., description="리뷰 고유 ID")
    overall_assessment: str = Field(..., description="전체 평가")
    compliance_status: str = Field(..., description="준수 상태")
    risk_areas: list[dict[str, object]] = Field(default_factory=list, description="위험 영역 목록")
    optimization_suggestions: list[dict[str, object]] = Field(
        default_factory=list, description="최적화 제안사항"
    )
    benchmark_comparison: dict[str, object] | None = Field(
        default=None, description="벤치마크 비교 결과"
    )
    evidence_bundle_id: str = Field(..., description="증거 번들 ID")
    reviewed_at: str = Field(..., description="리뷰 시각")


class TaxAuditRequest(BaseModel):
    """세무 감사 지원 요청 모델"""

    audit_scope: str = Field(
        ..., description="감사 범위", examples=["income_tax", "sales_tax", "payroll_tax", "all"]
    )
    time_period: str = Field(
        ..., description="감사 기간", examples=["2024", "2023-2024", "2022-2024"]
    )
    focus_areas: list[str] = Field(
        default_factory=lambda: ["documentation", "calculations", "compliance"],
        description="집중 영역",
    )
    include_mock_audit: bool = Field(default=True, description="모의 감사 포함 여부")


class TaxAuditResponse(BaseModel):
    """세무 감사 지원 응답 모델"""

    audit_id: str = Field(..., description="감사 고유 ID")
    audit_readiness_score: float = Field(..., ge=0.0, le=100.0, description="감사 준비도 점수")
    critical_findings: list[dict[str, object]] = Field(
        default_factory=list, description="중요 발견사항"
    )
    documentation_status: dict[str, object] = Field(default_factory=dict, description="문서화 상태")
    recommended_actions: list[str] = Field(default_factory=list, description="권장 조치사항")
    mock_audit_results: dict[str, object] | None = Field(default=None, description="모의 감사 결과")
    evidence_bundle_id: str = Field(..., description="증거 번들 ID")
    audited_at: str = Field(..., description="감사 시각")


class IRSUpdateResponse(BaseModel):
    """IRS 규정 변경 알림 응답 모델"""

    updates: list[dict[str, object]] = Field(
        default_factory=list, description="최근 IRS 규정 변경 목록"
    )
    last_updated: str = Field(..., description="마지막 업데이트 시각")
    total_changes: int = Field(..., description="총 변경사항 수")


class IRSImpactRequest(BaseModel):
    """규정 변경 영향 분석 요청 모델"""

    regulation_change: str = Field(
        ...,
        description="변경된 규정 설명",
        examples=["Section 179 deduction limit increased to $2.56M for 2026"],
    )
    client_profile: dict[str, object] = Field(
        ...,
        description="클라이언트 프로필",
        examples=[{"business_type": "LLC", "annual_revenue": 500000, "state": "CA"}],
    )
    analysis_depth: str = Field(
        default="standard", description="분석 깊이", examples=["basic", "standard", "comprehensive"]
    )


class IRSImpactResponse(BaseModel):
    """규정 변경 영향 분석 응답 모델"""

    impact_id: str = Field(..., description="영향 분석 고유 ID")
    overall_impact: str = Field(..., description="전체 영향 수준")
    financial_impact: dict[str, object] = Field(default_factory=dict, description="재무적 영향")
    compliance_changes: list[str] = Field(default_factory=list, description="준수사항 변경사항")
    action_items: list[dict[str, object]] = Field(
        default_factory=list, description="필요한 조치사항"
    )
    deadline_info: dict[str, object] | None = Field(default=None, description="마감일 정보")
    evidence_bundle_id: str = Field(..., description="증거 번들 ID")
    analyzed_at: str = Field(..., description="분석 시각")


class KingdomStatusResponse(BaseModel):
    """왕국 시스템 상태 응답 모델"""

    status: str = Field(..., description="전체 시스템 상태")
    version: str = Field(..., description="현재 버전")
    uptime: str = Field(..., description="가동 시간")
    services: dict[str, object] = Field(default_factory=dict, description="각 서비스 상태")
    trinity_score: dict[str, float] = Field(default_factory=dict, description="현재 Trinity Score")
    last_updated: str = Field(..., description="마지막 업데이트 시각")
