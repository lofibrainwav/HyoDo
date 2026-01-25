"""Gemini Financial Predictor Package.

AI 증강 재무 예측 시스템.
수학적 정밀도와 Gemini AI의 통찰력을 결합한 하이브리드 분석 제공.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .ai_engine import GeminiAIEngine
from .integrator import (
    calculate_trinity_score,
    generate_strategic_recommendations,
    integrate_predictions,
)
from .mathematical import calculate_confidence_intervals, generate_mathematical_forecast


class GeminiFinancialPredictor:
    """Gemini API 기반 재무 예측 AI 어시스턴트 (Facade)."""

    def __init__(self) -> None:
        self.ai_engine = GeminiAIEngine()

    async def predict_financial_scenarios(
        self,
        client_data: dict[str, Any],
        historical_data: list[dict[str, Any]],
        prediction_type: str,
        gemini_client=None,
    ) -> dict[str, Any]:
        """종합 재무 예측을 수행합니다 (Hybrid Approach)."""

        # 1. 수학적 예측 수행
        math_forecast = generate_mathematical_forecast(historical_data, prediction_type)

        # 2. AI 분석 수행
        ai_prediction = await self.ai_engine.perform_analysis(
            client_data, historical_data, math_forecast, prediction_type
        )

        # 3. 통합 및 하이브리드 모델 생성
        hybrid_result = integrate_predictions(math_forecast, ai_prediction)

        # 4. Trinity Score 및 추천 사항 추가
        scores = calculate_trinity_score(hybrid_result, client_data)
        recommendations = generate_strategic_recommendations(hybrid_result)

        return {
            "success": True,
            "prediction_type": prediction_type,
            "timestamp": datetime.now().isoformat(),
            "projections": hybrid_result.get("final_projections"),
            "insights": hybrid_result.get("insights"),
            "confidence": hybrid_result.get("combined_confidence"),
            "trinity_scores": scores,
            "recommendations": recommendations,
        }

    async def get_prediction_explanation(
        self,
        scenario_name: str,
        prediction_context: dict[str, Any],
        gemini_client=None,
    ) -> str:
        """예측 결과에 대한 상세 설명을 제공합니다."""
        return await self.ai_engine.get_explanation(scenario_name, prediction_context)


__all__ = ["GeminiFinancialPredictor"]
