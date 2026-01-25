"""Collaboration Analysis.

협업 컨텍스트 분석 및 점수 분포 통계 계산.
"""

from __future__ import annotations

import math
from typing import Any


def analyze_score_distribution(scores: dict[str, float]) -> dict[str, Any]:
    """점수들의 통계적 분포를 분석합니다."""
    if not scores:
        return {}

    values = list(scores.values())
    avg = sum(values) / len(values)
    variance = sum((x - avg) ** 2 for x in values) / len(values)

    return {
        "average": avg,
        "variance": variance,
        "std_dev": math.sqrt(variance),
        "range": max(values) - min(values),
    }


def calculate_collaboration_intensity(scores: dict[str, float]) -> float:
    """점수 편차를 기반으로 협업의 밀도(Intensity)를 계산합니다."""
    # 편차가 작을수록(합의에 가까울수록) 강도가 높다고 가정
    dist = analyze_score_distribution(scores)
    if not dist:
        return 0.0

    # 0.0 ~ 1.0 사이로 정규화
    intensity = 1.0 / (1.0 + dist["std_dev"])
    return intensity
