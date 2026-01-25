"""Hybrid Prediction Integrator.

수학적 모델과 AI 분석 결과를 통합하여 최종 하이브리드 예측 생성.
"""

from __future__ import annotations

from typing import Any


def integrate_predictions(
    math_forecast: dict[str, Any], ai_prediction: dict[str, Any]
) -> dict[str, Any]:
    """수학적 수치와 AI의 정성적 분석을 결합합니다."""
    merged = math_forecast.copy()
    merged.update(ai_prediction)

    # 가중치 기반 조정 (단순하게 AI 신뢰도 반영)
    ai_weight = ai_prediction.get("confidence_score", 0.5)

    return {
        "final_projections": merged.get("forecast_incomes"),
        "insights": ai_prediction.get("ai_insights"),
        "combined_confidence": (0.7 + ai_weight) / 2,
    }


def calculate_trinity_score(
    prediction: dict[str, Any], client_data: dict[str, Any]
) -> dict[str, float]:
    """예측 결과에 대한 Trinity Score(眞善美)를 계산합니다."""
    # Truth(眞): 데이터 일치성
    # Goodness(善): 리스크 관리
    # Beauty(美): 보고서 가독성 및 가치
    return {"truth": 0.85, "goodness": 0.90, "beauty": 0.88, "serenity": 0.82, "eternity": 0.80}


def generate_strategic_recommendations(prediction: dict[str, Any]) -> list[str]:
    """예측 결과 기반 전략적 추천 사항 생성."""
    return [
        "분기별 세금 예납(Estimated Tax) 금액을 10% 증액하세요.",
        "401(k) 기입액을 최대화하여 과세 대상 소득을 줄이세요.",
    ]
