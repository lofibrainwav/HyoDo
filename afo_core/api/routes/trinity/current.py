from datetime import UTC, datetime

from fastapi import APIRouter, Query

from AFO.domain.metrics.trinity_manager import trinity_manager

router = APIRouter(prefix="/api/trinity", tags=["Trinity Score"])


@router.get("/current", response_model=dict)
async def get_current_trinity_metrics():
    """
    현재 Trinity Score 조회 (TrinityManager 연동 완료)
    """
    metrics = trinity_manager.get_current_metrics()
    metrics_100 = metrics.to_100_scale()

    return {
        "trinity_score": metrics_100.trinity_score,
        "risk_score": 100.0 - metrics_100.goodness,
        "pillars": {
            "truth": metrics_100.truth,
            "goodness": metrics_100.goodness,
            "beauty": metrics_100.beauty,
            "serenity": metrics_100.filial_serenity,
            "eternity": metrics_100.eternity,
        },
        "deltas": trinity_manager.deltas,
        "timestamp": datetime.now(UTC).isoformat(),
        "note": "TrinityManager 연동 완료 - 실시간 계산",
        "implementation": "integrated",
    }


@router.post("/realtime", response_model=dict)
async def calculate_realtime_score(
    trigger: str = Query(..., description="Trigger name from TrinityManager.TRIGGERS"),
):
    """
    실시간 Trinity Score 계산 (TrinityManager 연동 완료)
    """
    metrics = trinity_manager.apply_trigger(trigger)
    metrics_100 = metrics.to_100_scale()

    return {
        "trinity_score": metrics_100.trinity_score,
        "risk_score": 100.0 - metrics_100.goodness,
        "pillars": {
            "truth": metrics_100.truth,
            "goodness": metrics_100.goodness,
            "beauty": metrics_100.beauty,
            "serenity": metrics_100.filial_serenity,
            "eternity": metrics_100.eternity,
        },
        "deltas": trinity_manager.deltas,
        "trigger_applied": trigger,
        "timestamp": datetime.now(UTC).isoformat(),
        "note": "TrinityManager 연동 완료 - 실시간 계산",
        "implementation": "integrated",
    }


@router.post("/pillar/update", response_model=dict)
async def update_pillar_score(pillar: str, delta: float):
    """
    특정 Pillar 점수 업데이트 (TrinityManager 연동 완료)
    """
    old_delta = trinity_manager.deltas.get(pillar, 0.0)
    trinity_manager.deltas[pillar] = old_delta + delta

    metrics = trinity_manager.get_current_metrics()
    metrics_100 = metrics.to_100_scale()

    pillar_score_mapping = {
        "truth": metrics_100.truth,
        "goodness": metrics_100.goodness,
        "beauty": metrics_100.beauty,
        "filial_serenity": metrics_100.filial_serenity,
        "eternity": metrics_100.eternity,
    }

    old_score = pillar_score_mapping.get(pillar, 0.0)
    new_score = old_score + delta

    return {
        "success": True,
        "pillar": pillar,
        "delta": delta,
        "old_delta": old_delta,
        "new_delta": trinity_manager.deltas[pillar],
        "old_score": old_score,
        "new_score": round(new_score, 2),
        "current_trinity_score": metrics_100.trinity_score,
        "message": f"{pillar} 점수 업데이트 완료",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/breakdown", response_model=dict)
async def get_score_breakdown():
    """
    Trinity Score 구성 분석 (TrinityManager 연동 완료)
    """
    metrics = trinity_manager.get_current_metrics()
    metrics_100 = metrics.to_100_scale()

    current_scores = {
        "truth": metrics_100.truth,
        "goodness": metrics_100.goodness,
        "beauty": metrics_100.beauty,
        "serenity": metrics_100.filial_serenity,
        "eternity": metrics_100.eternity,
    }

    breakdown = {
        "truth": {"score": current_scores["truth"], "weight": 0.35},
        "goodness": {"score": current_scores["goodness"], "weight": 0.35},
        "beauty": {"score": current_scores["beauty"], "weight": 0.20},
        "serenity": {"score": current_scores["serenity"], "weight": 0.08},
        "eternity": {"score": current_scores["eternity"], "weight": 0.02},
    }

    analysis = {
        "truth_ratio": round(current_scores["truth"] / 100.0, 4),
        "goodness_ratio": round(current_scores["goodness"] / 100.0, 4),
        "beauty_ratio": round(current_scores["beauty"] / 100.0, 4),
        "serenity_ratio": round(current_scores["serenity"] / 100.0, 4),
        "eternity_ratio": round(current_scores["eternity"] / 100.0, 4),
        "balance_delta": metrics_100.balance_delta,
        "balance_status": metrics_100.balance_status,
    }

    return {
        "current_scores": current_scores,
        "breakdown": breakdown,
        "analysis": analysis,
        "trinity_score": metrics_100.trinity_score,
        "serenity_core": metrics_100.serenity_core,
        "deltas": trinity_manager.deltas,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/triggers", response_model=dict)
async def list_available_triggers():
    """
    사용 가능한 트리거 목록 조회
    """
    return {
        "triggers": trinity_manager.TRIGGERS,
        "timestamp": datetime.now(UTC).isoformat(),
    }


__all__ = ["router"]
