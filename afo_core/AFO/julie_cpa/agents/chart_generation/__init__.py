"""Chart Generation Package.

CPA 특화 차트 생성 시스템을 위한 모듈화된 패키지.

Modules:
    models: 데이터 모델 및 상수
    utils: 유틸리티 함수
    tax_charts: 세금 관련 차트 생성
    analysis_charts: 분석 차트 생성
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import matplotlib.pyplot as plt
import seaborn as sns

from .analysis_charts import (
    generate_expense_breakdown_chart,
    generate_income_distribution_chart,
    generate_risk_heatmap_chart,
)

# 모듈 임포트
from .models import CHART_TYPES, COLORS, ChartMetadata, ChartResult, DashboardResult
from .tax_charts import (
    generate_business_vs_personal_chart,
    generate_deduction_efficiency_chart,
    generate_tax_burden_trend_chart,
)
from .utils import convert_plot_to_data


class CPAChartGenerationSystem:
    """CPA 특화 차트 생성 시스템.

    Phase 2: 멀티모달 협업 플랫폼의 시각화 컴포넌트
    재무 데이터 자동 시각화 및 보고서 생성

    이 클래스는 분리된 모듈들을 조합하여 차트를 생성합니다.
    """

    def __init__(self) -> None:
        """초기화."""
        plt.style.use("seaborn-v0_8")
        sns.set_palette("husl")

        self.chart_types = CHART_TYPES
        self.colors = COLORS

    async def generate_tax_charts(
        self,
        client_data: dict[str, Any],
        historical_data: list[dict[str, Any]],
        chart_types: list[str] = None,
        output_format: str = "png",
    ) -> dict[str, Any]:
        """세금 데이터 기반 차트 자동 생성."""

        if chart_types is None:
            chart_types = ["tax_burden_trend", "deduction_efficiency", "business_vs_personal"]

        chart_results = {
            "success": True,
            "charts": {},
            "metadata": {
                "client_id": client_data.get("client_id"),
                "chart_types": chart_types,
                "output_format": output_format,
                "generation_timestamp": datetime.now().isoformat(),
                "phase": "phase_2_chart_generation",
            },
        }

        # 각 차트 유형별 생성
        for chart_type in chart_types:
            if chart_type in self.chart_types:
                print(f"📊 Phase 2.2: {self.chart_types[chart_type]} 생성 중")
                try:
                    chart_data = await self._generate_specific_chart(
                        chart_type, client_data, historical_data, output_format
                    )
                    chart_results["charts"][chart_type] = chart_data
                except Exception as e:
                    chart_results["charts"][chart_type] = {"success": False, "error": str(e)}

        # 종합 대시보드 생성
        try:
            dashboard = await self._generate_dashboard(
                chart_results["charts"], client_data, output_format
            )
            chart_results["dashboard"] = dashboard
        except Exception as e:
            chart_results["dashboard"] = {"success": False, "error": str(e)}

        return chart_results

    async def _generate_specific_chart(
        self,
        chart_type: str,
        client_data: dict[str, Any],
        historical_data: list[dict[str, Any]],
        output_format: str,
    ) -> dict[str, Any]:
        """특정 유형의 차트 생성."""

        if chart_type == "tax_burden_trend":
            return await generate_tax_burden_trend_chart(historical_data, output_format)
        elif chart_type == "deduction_efficiency":
            return await generate_deduction_efficiency_chart(historical_data, output_format)
        elif chart_type == "business_vs_personal":
            return await generate_business_vs_personal_chart(historical_data, output_format)
        elif chart_type == "risk_heatmap":
            return await generate_risk_heatmap_chart(client_data, historical_data, output_format)
        elif chart_type == "income_distribution":
            return await generate_income_distribution_chart(historical_data, output_format)
        elif chart_type == "expense_breakdown":
            return await generate_expense_breakdown_chart(historical_data, output_format)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

    async def _generate_dashboard(
        self, charts: dict[str, Any], client_data: dict[str, Any], output_format: str
    ) -> dict[str, Any]:
        """종합 대시보드 생성."""

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(
            f"AFO CPA 대시보드 - {client_data.get('client_id', 'Client')}\n"
            f"생성일: {datetime.now().strftime('%Y-%m-%d')}",
            fontsize=16,
            fontweight="bold",
        )

        axes_flat = axes.flatten()
        chart_titles = ["세금 부담 추이", "공제 효율성", "소득 분포", "리스크 히트맵"]

        for i, title in enumerate(chart_titles):
            ax = axes_flat[i]
            ax.text(
                0.5,
                0.5,
                f"{title}\n\n차트 데이터 준비 중...",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "lightblue", "alpha": 0.5},
            )
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.axis("off")

        plt.tight_layout()

        dashboard_data = convert_plot_to_data(fig, output_format)
        plt.close(fig)

        return {
            "success": True,
            "dashboard_type": "comprehensive_cpa_dashboard",
            "title": "AFO CPA 종합 대시보드",
            "description": "세무 데이터의 종합 시각화 대시보드",
            "data": dashboard_data,
            "included_charts": list(charts.keys()),
            "generation_timestamp": datetime.now().isoformat(),
        }


# 편의 함수
async def generate_tax_visualization_charts(
    client_data: dict[str, Any],
    historical_data: list[dict[str, Any]],
    chart_types: list[str] = None,
    output_format: str = "png",
) -> dict[str, Any]:
    """세금 데이터 시각화 차트 생성 편의 함수."""
    chart_system = CPAChartGenerationSystem()
    return await chart_system.generate_tax_charts(
        client_data, historical_data, chart_types, output_format
    )


# 공개 API
__all__ = [
    "CPAChartGenerationSystem",
    "generate_tax_visualization_charts",
    "CHART_TYPES",
    "COLORS",
    "ChartResult",
    "ChartMetadata",
    "DashboardResult",
]
