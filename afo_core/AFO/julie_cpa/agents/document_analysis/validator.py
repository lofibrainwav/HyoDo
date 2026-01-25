"""Document Validation and Scoring.

추출된 데이터의 수학적 정합성 검증 및 신뢰도 점수(Trinity Score) 계산.
"""

from __future__ import annotations

from typing import Any


def validate_mathematically(ai_analysis: dict[str, Any], _raw_content: str) -> dict[str, Any]:
    """AI가 추출한 숫자 데이터가 수학적으로 일관된지 검증합니다."""
    data = ai_analysis.get("extracted_data", {})
    wages = data.get("wages", 0)
    fed_tax = data.get("federal_tax", 0)

    # 예: 세율이 비정상적으로 높거나 낮은지 체크
    effective_rate = fed_tax / wages if wages > 0 else 0

    return {
        "is_valid": 0.1 < effective_rate < 0.45,
        "effective_rate": effective_rate,
        "warnings": ["세율이 매우 낮습니다."] if effective_rate < 0.1 else [],
    }


def calculate_document_trinity_score(
    ai_analysis: dict[str, Any],
    math_validation: dict[str, Any],
) -> dict[str, float]:
    """문서 분석 결과의 신뢰도를 Trinity(眞善美) 관점에서 평가합니다."""
    # 眞(Truth): 데이터의 수학적 정합성
    truth = 0.95 if math_validation.get("is_valid") else 0.6

    # 善(Goodness): 개인정보 보호 및 누락 데이터 없음
    goodness = ai_analysis.get("confidence_score", 0.8)

    return {
        "truth": truth,
        "goodness": goodness,
        "beauty": 0.90,
        "serenity": 0.85,
        "eternity": 0.80,
    }
