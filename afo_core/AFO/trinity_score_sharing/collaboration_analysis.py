# Trinity Score: 95.0 (Established by Chancellor)
"""
Collaboration Analysis Utilities

협업 분석 관련 순수 함수들. sharing_system_full.py에서 추출됨.
통계 계산, 분포 분석, 협업 강도 측정 등.
"""

from __future__ import annotations

from typing import Any


def calculate_variance(values: list[float]) -> float:
    """분산 계산"""
    if len(values) <= 1:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)

    return variance


def analyze_score_distribution(scores: dict[str, float]) -> dict[str, Any]:
    """점수 분포 분석"""
    score_values = list(scores.values())

    if not score_values:
        return {
            "min_score": 0.0,
            "max_score": 0.0,
            "mean_score": 0.0,
            "mean": 0.0,
            "score_variance": 0.0,
            "variance": 0.0,
            "score_range": 0.0,
            "agent_count": 0,
            "min": 0.0,
            "max": 0.0,
        }

    return {
        "min_score": min(score_values),
        "max_score": max(score_values),
        "mean_score": sum(score_values) / len(score_values),
        "mean": sum(score_values) / len(score_values),  # Alias
        "score_variance": calculate_variance(score_values),
        "variance": calculate_variance(score_values),  # Alias
        "score_range": max(score_values) - min(score_values),
        "agent_count": len(score_values),
        "min": min(score_values),  # Alias
        "max": max(score_values),  # Alias
    }


def calculate_collaboration_intensity(scores: dict[str, float]) -> float:
    """협업 강도 계산"""
    if len(scores) <= 1:
        return 0.0

    # 점수 유사성 기반 협업 강도
    score_values = list(scores.values())
    mean_score = sum(score_values) / len(score_values)

    # 평균과의 편차가 적을수록 협업 강도가 높음
    total_deviation = sum(abs(score - mean_score) for score in score_values)
    collaboration_intensity = 1.0 - (total_deviation / (len(score_values) * 0.5))

    return max(0.0, collaboration_intensity)


def calculate_collaboration_impact(
    session_scores: dict[str, float],
    agent_type: str,
    new_score: float,
) -> float:
    """협업 영향도 계산"""
    other_agents = [score for agent, score in session_scores.items() if agent != agent_type]

    if not other_agents:
        return 0.0

    # 다른 Agent들의 평균 점수와의 차이
    avg_other_scores = sum(other_agents) / len(other_agents)
    score_diff = abs(new_score - avg_other_scores)

    # 협업 효과 정규화 (유사할수록 높음 -> 1.0)
    impact = 1.0 - min(score_diff / 2.0, 1.0)

    return max(0.0, impact)


def analyze_collaboration_context(
    session_scores: dict[str, float],
    target_agent: str,
    context_factors: dict[str, Any],
) -> dict[str, Any]:
    """협업 맥락 분석"""
    agent_keys = list(session_scores.keys())
    position = agent_keys.index(target_agent) + 1 if target_agent in agent_keys else 0

    return {
        "total_agents": len(session_scores),
        "agent_position": position,
        "score_distribution": analyze_score_distribution(session_scores),
        "collaboration_intensity": calculate_collaboration_intensity(session_scores),
        "context_factors": context_factors,
    }


def calculate_collaborative_adjustment(
    current_score: float,
    collaboration_context: dict[str, Any],
    context_factors: dict[str, Any],
) -> float:
    """협업 기반 점수 조정 계산"""
    adjustment = 0.0

    # 협업 강도에 따른 조정
    collaboration_intensity = collaboration_context.get("collaboration_intensity", 0.0)
    adjustment += collaboration_intensity * 0.05

    if collaboration_intensity < 0.3:
        adjustment -= 0.05 * (1.0 - collaboration_intensity)

    # 점수 분포 균형 조정
    score_dist = collaboration_context.get("score_distribution", {})
    score_variance = score_dist.get("score_variance", 0.0)

    # 분산이 높으면 (점수 차이가 크면) 조정
    # 낮은 점수의 Agent에게 약간의 보너스
    if score_variance > 0.1 and current_score < score_dist.get("mean_score", 0.8):
        adjustment += 0.02

    # 맥락 요인 기반 조정
    context_multiplier = context_factors.get("urgency", 1.0)
    context_multiplier *= context_factors.get("complexity", 1.0)

    adjustment *= context_multiplier

    # 조정된 점수 계산 (원래 점수의 ±10% 범위 제한)
    max_adjustment = current_score * 0.1
    adjustment = max(-max_adjustment, min(max_adjustment, adjustment))

    return adjustment


def generate_adjustment_reason(
    original_score: float,
    adjusted_score: float,
    collaboration_context: dict[str, Any],
) -> str:
    """조정 이유 생성"""
    adjustment = adjusted_score - original_score

    if abs(adjustment) < 0.01:
        return "No significant collaboration adjustment needed"

    direction = "increased" if adjustment > 0 else "decreased"
    magnitude = abs(adjustment)

    reasons = []

    collaboration_intensity = collaboration_context.get("collaboration_intensity", 0.0)
    if collaboration_intensity > 0.7:
        reasons.append(f"high collaboration synergy (+{collaboration_intensity:.2f})")

    score_dist = collaboration_context.get("score_distribution", {})
    score_variance = score_dist.get("score_variance", 0.0)
    if score_variance > 0.1:
        reasons.append(f"score distribution balancing (variance: {score_variance:.3f})")

    if not reasons:
        reasons.append("general collaborative optimization")

    return f"Score {direction} by {magnitude:.3f} due to {', '.join(reasons)}"


def calculate_adjustment_confidence(collaboration_context: dict[str, Any]) -> float:
    """조정 신뢰도 계산"""
    confidence = 0.8  # 기본 신뢰도

    # Agent 수에 따른 신뢰도
    total_agents = collaboration_context.get("total_agents", 1)
    if total_agents >= 3:
        confidence += 0.1
    elif total_agents == 1:
        confidence -= 0.2

    # 협업 강도에 따른 신뢰도
    collaboration_intensity = collaboration_context.get("collaboration_intensity", 0.0)
    confidence += collaboration_intensity * 0.1

    return min(1.0, confidence)


def assess_convergence_status(sync_metrics: dict[str, Any]) -> str:
    """수렴 상태 평가"""
    variance = sync_metrics.get("score_variance", 0.0)
    collaboration_impact = sync_metrics.get("collaboration_impact_avg", 0.0)

    if variance < 0.05 and collaboration_impact > 0.7:
        return "highly_converged"
    elif variance < 0.1 and collaboration_impact > 0.5:
        return "well_converged"
    elif variance < 0.2:
        return "moderately_converged"
    else:
        return "diverging"


def check_convergence(scores: dict[str, float]) -> str:
    """수렴 상태 확인"""
    variance = calculate_variance(list(scores.values()))

    if variance < 0.05:
        return "converged"
    elif variance < 0.15:
        return "converging"
    else:
        return "diverging"


__all__ = [
    "calculate_variance",
    "analyze_score_distribution",
    "calculate_collaboration_intensity",
    "calculate_collaboration_impact",
    "analyze_collaboration_context",
    "calculate_collaborative_adjustment",
    "generate_adjustment_reason",
    "calculate_adjustment_confidence",
    "assess_convergence_status",
    "check_convergence",
]
