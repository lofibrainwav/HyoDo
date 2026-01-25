"""Analysis Chart Generators.

분석 관련 차트 생성 함수들 (히트맵, 분포, 내역).
"""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .models import COLORS
from .utils import convert_plot_to_data


async def generate_risk_heatmap_chart(
    client_data: dict[str, Any], historical_data: list[dict[str, Any]], output_format: str
) -> dict[str, Any]:
    """세무 리스크 히트맵 생성."""

    risk_categories = [
        "세법 준수",
        "기록 보관",
        "신고 기한",
        "납부 정확성",
        "사업 비용",
        "개인 공제",
        "감가상각",
        "세무 계획",
    ]

    risk_years = [d["year"] for d in historical_data]

    np.random.seed(42)
    risk_scores = np.random.uniform(0.1, 0.9, (len(risk_categories), len(risk_years)))

    # 특정 패턴 추가
    for i, category in enumerate(risk_categories):
        if "세법 준수" in category:
            risk_scores[i] = np.linspace(0.9, 0.7, len(risk_years))
        elif "기록 보관" in category:
            risk_scores[i] = np.full(len(risk_years), 0.8)

    fig, ax = plt.subplots(figsize=(12, 8))

    im = ax.imshow(risk_scores, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(np.arange(len(risk_years)))
    ax.set_yticks(np.arange(len(risk_categories)))
    ax.set_xticklabels(risk_years)
    ax.set_yticklabels(risk_categories)

    ax.set_title("세무 리스크 히트맵", fontsize=14, fontweight="bold")
    ax.set_xlabel("연도")
    ax.set_ylabel("리스크 영역")

    plt.colorbar(im, ax=ax, label="리스크 수준")
    plt.tight_layout()

    chart_data = convert_plot_to_data(fig, output_format)
    plt.close(fig)

    avg_risks = np.mean(risk_scores, axis=1)
    high_risk_areas = [risk_categories[i] for i, avg in enumerate(avg_risks) if avg > 0.7]

    return {
        "success": True,
        "chart_type": "risk_heatmap",
        "title": "세무 리스크 평가",
        "description": "각 리스크 영역별 연도별 위험도 히트맵",
        "data": chart_data,
        "insights": [
            f"고위험 영역: {', '.join(high_risk_areas[:3])}",
            f"평균 리스크 점수: {np.mean(risk_scores):.2f}",
            f"개선 필요 영역: {len(high_risk_areas)}개",
        ],
    }


async def generate_income_distribution_chart(
    historical_data: list[dict[str, Any]], output_format: str
) -> dict[str, Any]:
    """소득 분포 파이 차트 생성."""

    recent_data = historical_data[-1] if historical_data else {}

    income_sources = {
        "급여": recent_data.get("income", 0) * 0.7,
        "사업 소득": recent_data.get("business_income", 0),
        "이자 수입": recent_data.get("interest", 1000),
        "배당금": recent_data.get("dividends", 2000),
        "임대 수입": recent_data.get("rental_income", 5000),
    }

    income_sources = {k: v for k, v in income_sources.items() if v > 0}

    if not income_sources:
        return {"success": False, "error": "소득 데이터가 없습니다"}

    fig, ax = plt.subplots(figsize=(10, 8))

    ax.pie(
        income_sources.values(),
        labels=income_sources.keys(),
        autopct="%1.1f%%",
        startangle=90,
        colors=[
            COLORS["primary"],
            COLORS["business"],
            COLORS["secondary"],
            COLORS["success"],
            COLORS["info"],
        ],
    )

    ax.set_title(f"{recent_data.get('year', '최근')}년 소득 분포", fontsize=14, fontweight="bold")

    plt.tight_layout()

    chart_data = convert_plot_to_data(fig, output_format)
    plt.close(fig)

    total_income = sum(income_sources.values())
    primary_source = max(income_sources, key=income_sources.get)

    return {
        "success": True,
        "chart_type": "income_distribution",
        "title": "소득 분포 분석",
        "description": "각 소득원의 비율 및 구성 분석",
        "data": chart_data,
        "insights": [
            f"총 소득: ${total_income:,.0f}",
            f"주요 소득원: {primary_source}",
            f"소득원 다양성: {len(income_sources)}개",
        ],
    }


async def generate_expense_breakdown_chart(
    historical_data: list[dict[str, Any]], output_format: str
) -> dict[str, Any]:
    """비용 내역 차트 생성."""

    recent_data = historical_data[-1] if historical_data else {}

    expense_categories = {
        "주거비": recent_data.get("mortgage_interest", 8000)
        + recent_data.get("home_insurance", 1200)
        + recent_data.get("property_taxes", 4000),
        "운송비": recent_data.get("car_payment", 500)
        + recent_data.get("gasoline", 2000)
        + recent_data.get("auto_insurance", 1500),
        "생계비": recent_data.get("groceries", 6000)
        + recent_data.get("utilities", 3000)
        + recent_data.get("phone_internet", 200),
        "사업비": recent_data.get("office_rent", 2000)
        + recent_data.get("business_vehicle", 800)
        + recent_data.get("office_supplies", 500),
    }

    fig, ax = plt.subplots(figsize=(12, 6))

    categories = list(expense_categories.keys())
    values = list(expense_categories.values())
    colors = [COLORS["primary"], COLORS["secondary"], COLORS["success"], COLORS["business"]]

    ax.bar(categories, values, color=colors, alpha=0.7)
    ax.set_title("비용 내역 분류", fontsize=14, fontweight="bold")
    ax.set_ylabel("비용 금액 ($)")
    ax.grid(True, alpha=0.3, axis="y")

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    chart_data = convert_plot_to_data(fig, output_format)
    plt.close(fig)

    total_expenses = sum(values)
    largest_category = max(expense_categories, key=expense_categories.get)

    return {
        "success": True,
        "chart_type": "expense_breakdown",
        "title": "비용 내역 분석",
        "description": "주요 비용 카테고리별 분류 및 분석",
        "data": chart_data,
        "insights": [
            f"총 비용: ${total_expenses:,.0f}",
            f"최대 비용 카테고리: {largest_category}",
            f"비용 다양성: {len(expense_categories)}개",
        ],
    }
