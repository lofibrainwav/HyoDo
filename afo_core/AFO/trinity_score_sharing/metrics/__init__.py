"""Trinity Score Sharing Metrics

협업 메트릭 계산 및 분석 함수들.
"""

from typing import Dict


def calculate_collaboration_intensity(scores: dict[str, float]) -> float:
    """협업 강도 계산"""

    if len(scores) <= 1:
        return 0.0

    # 점수 편차의 역수로 협업 강도 계산
    score_values = list(scores.values())
    variance = calculate_variance(score_values)

    # 분산이 작을수록 협업 강도가 높음
    intensity = max(0.0, 1.0 - variance)

    return intensity


def calculate_variance(values: list[float]) -> float:
    """분산 계산"""

    if not values:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)

    return variance


def analyze_score_distribution(scores: dict[str, float]) -> dict[str, float]:
    """점수 분포 분석"""

    if not scores:
        return {"mean": 0.0, "variance": 0.0, "min": 0.0, "max": 0.0}

    score_values = list(scores.values())
    mean = sum(score_values) / len(score_values)
    variance = calculate_variance(score_values)

    return {
        "mean": mean,
        "variance": variance,
        "min": min(score_values),
        "max": max(score_values),
        "range": max(score_values) - min(score_values),
        "agent_count": len(scores),
    }


def analyze_collaboration_context(
    scores: dict[str, float], history_length: int
) -> dict[str, float]:
    """협업 컨텍스트 분석"""

    if not scores:
        return {"collaboration_level": 0.0, "diversity_index": 0.0}

    score_values = list(scores.values())

    # 협업 레벨 계산 (히스토리 길이 기반)
    collaboration_level = min(1.0, history_length / 20.0)  # 20개 업데이트로 최대

    # 다양성 지수 계산
    if len(score_values) > 1:
        variance = calculate_variance(score_values)
        diversity_index = min(1.0, variance * 10)  # 0-1 범위로 정규화
    else:
        diversity_index = 0.0

    return {
        "collaboration_level": collaboration_level,
        "diversity_index": diversity_index,
        "agent_count": len(scores),
        "update_count": history_length,
    }


def calculate_collaborative_adjustment(base_score: float, context: dict[str, float]) -> float:
    """협업 기반 조정 계산"""

    collaboration_intensity = context.get("collaboration_intensity", 0.0)
    diversity_index = context.get("diversity_index", 0.0)

    # 협업 강도와 다양성에 따른 조정
    adjustment = (collaboration_intensity * 0.1) - (diversity_index * 0.05)

    # 조정 범위 제한 (-0.1 ~ +0.1)
    adjustment = max(-0.1, min(0.1, adjustment))

    return adjustment
