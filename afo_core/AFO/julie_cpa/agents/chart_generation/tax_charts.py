"""Tax Chart Generators.

세금 관련 차트 생성 함수들.
"""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .models import COLORS
from .utils import calculate_tax_rate, convert_plot_to_data


async def generate_tax_burden_trend_chart(
    historical_data: list[dict[str, Any]], output_format: str
) -> dict[str, Any]:
    """세금 부담 추이 그래프 생성."""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # 데이터 추출
    years = [d["year"] for d in historical_data]
    incomes = [d["income"] for d in historical_data]
    tax_burdens = [income * calculate_tax_rate(income) for income in incomes]

    # 세금 부담 추이 그래프
    ax1.plot(years, tax_burdens, "o-", color=COLORS["tax"], linewidth=3, markersize=8)
    ax1.fill_between(years, tax_burdens, alpha=0.3, color=COLORS["tax"])
    ax1.set_title("세금 부담 추이 (Tax Burden Trend)", fontsize=14, fontweight="bold")
    ax1.set_ylabel("세금 부담 ($)", fontsize=12)
    ax1.grid(True, alpha=0.3)

    # 세율 변화 그래프
    tax_rates = [burden / income for burden, income in zip(tax_burdens, incomes)]
    ax2.bar(years, tax_rates, color=COLORS["warning"], alpha=0.7)
    ax2.set_title("유효 세율 추이 (Effective Tax Rate)", fontsize=14, fontweight="bold")
    ax2.set_ylabel("세율 (%)", fontsize=12)
    ax2.set_ylim(0, 0.4)

    plt.tight_layout()

    chart_data = convert_plot_to_data(fig, output_format)
    plt.close(fig)

    return {
        "success": True,
        "chart_type": "tax_burden_trend",
        "title": "세금 부담 추이 분석",
        "description": "연도별 세금 부담 및 유효 세율 변화 추이",
        "data": chart_data,
        "insights": [
            f"평균 세금 부담: ${sum(tax_burdens) / len(tax_burdens):,.0f}",
            f"세율 범위: {min(tax_rates) * 100:.1f}% - {max(tax_rates) * 100:.1f}%",
            f"추세: {'상승' if tax_burdens[-1] > tax_burdens[0] else '하락'}",
        ],
    }


async def generate_deduction_efficiency_chart(
    historical_data: list[dict[str, Any]], output_format: str
) -> dict[str, Any]:
    """공제 효율성 비교 차트 생성."""

    recent_data = historical_data[-1] if historical_data else {}

    deductions = {
        "표준공제": 14600,
        "의료비": recent_data.get("medical_expenses", 2000),
        "주택담보이자": recent_data.get("mortgage_interest", 8000),
        "주세": recent_data.get("state_taxes", 5000),
        "기부금": recent_data.get("charitable", 3000),
        "사업비": recent_data.get("business_expenses", 12000),
    }

    marginal_rate = 0.25
    efficiency = {k: v * marginal_rate for k, v in deductions.items()}

    fig, ax = plt.subplots(figsize=(12, 6))

    deduction_names = list(deductions.keys())
    deduction_values = list(deductions.values())

    y_pos = np.arange(len(deduction_names))
    ax.barh(y_pos, deduction_values, color=COLORS["primary"], alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(deduction_names, fontsize=10)
    ax.set_xlabel("공제 금액 ($)", fontsize=12)
    ax.set_title("공제 효율성 비교", fontsize=14, fontweight="bold")

    plt.tight_layout()

    chart_data = convert_plot_to_data(fig, output_format)
    plt.close(fig)

    return {
        "success": True,
        "chart_type": "deduction_efficiency",
        "title": "공제 효율성 분석",
        "description": "각 공제 항목의 금액과 절세 효율성 비교",
        "data": chart_data,
        "insights": [
            f"가장 효과적인 공제: {max(efficiency, key=efficiency.get)}",
            f"총 공제 금액: ${sum(deductions.values()):,.0f}",
            f"총 절세 효과: ${sum(efficiency.values()):,.0f}",
        ],
    }


async def generate_business_vs_personal_chart(
    historical_data: list[dict[str, Any]], output_format: str
) -> dict[str, Any]:
    """사업 vs 개인 소득 비율 차트 생성."""

    business_incomes = []
    personal_incomes = []

    for data in historical_data:
        business = data.get("business_income", 0)
        personal = data.get("income", 0) - business
        business_incomes.append(business)
        personal_incomes.append(personal)

    years = [d["year"] for d in historical_data]

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(years, personal_incomes, label="개인 소득", color=COLORS["personal"], alpha=0.8)
    ax.bar(
        years,
        business_incomes,
        bottom=personal_incomes,
        label="사업 소득",
        color=COLORS["business"],
        alpha=0.8,
    )

    ax.set_title("사업 vs 개인 소득 분포", fontsize=14, fontweight="bold")
    ax.set_ylabel("소득 금액 ($)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    chart_data = convert_plot_to_data(fig, output_format)
    plt.close(fig)

    if business_incomes and personal_incomes:
        total_income = sum(
            business_incomes[i] + personal_incomes[i] for i in range(len(business_incomes))
        )
        avg_business_ratio = sum(business_incomes) / total_income * 100 if total_income > 0 else 0
    else:
        avg_business_ratio = 0

    return {
        "success": True,
        "chart_type": "business_vs_personal",
        "title": "사업 vs 개인 소득 분석",
        "description": "사업 소득과 개인 소득의 분포 및 추이 분석",
        "data": chart_data,
        "insights": [
            f"평균 사업 소득 비율: {avg_business_ratio:.1f}%",
            f"사업 소득 추세: {'상승' if business_incomes[-1] > business_incomes[0] else '하락'}",
            f"최근 사업 소득: ${business_incomes[-1]:,.0f}" if business_incomes else "데이터 없음",
        ],
    }
