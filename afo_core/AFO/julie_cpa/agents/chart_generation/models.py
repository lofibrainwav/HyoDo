"""Chart Generation Models and Constants.

차트 생성에 필요한 데이터 모델, 색상, 차트 유형 정의.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ============================================================================
# Constants
# ============================================================================

# CPA 특화 차트 유형
CHART_TYPES: dict[str, str] = {
    "tax_burden_trend": "세금 부담 추이 그래프",
    "deduction_efficiency": "공제 효율성 비교 차트",
    "business_vs_personal": "사업 vs 개인 소득 비율",
    "risk_heatmap": "세무 리스크 히트맵",
    "income_distribution": "소득 분포 파이 차트",
    "expense_breakdown": "비용 내역 트리맵",
    "depreciation_schedule": "감가상각 스케줄 차트",
    "tax_optimization_scenarios": "세금 최적화 시나리오 비교",
}

# AFO Kingdom 브랜딩 색상 팔레트
COLORS: dict[str, str] = {
    "primary": "#1f77b4",  # 파란색 - 신뢰
    "secondary": "#ff7f0e",  # 주황색 - 에너지
    "success": "#2ca02c",  # 초록색 - 성공
    "warning": "#d62728",  # 빨간색 - 경고
    "info": "#9467bd",  # 보라색 - 정보
    "tax": "#8c564b",  # 갈색 - 세금
    "business": "#e377c2",  # 분홍색 - 사업
    "personal": "#7f7f7f",  # 회색 - 개인
}


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ChartResult:
    """차트 생성 결과."""

    success: bool
    chart_type: str
    title: str
    description: str
    data: str  # Base64 encoded or SVG string
    insights: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class ChartMetadata:
    """차트 메타데이터."""

    client_id: str | None
    chart_types: list[str]
    output_format: str
    generation_timestamp: str
    phase: str = "phase_2_chart_generation"


@dataclass
class DashboardResult:
    """대시보드 생성 결과."""

    success: bool
    dashboard_type: str
    title: str
    description: str
    data: str
    included_charts: list[str]
    generation_timestamp: str
    error: str | None = None
