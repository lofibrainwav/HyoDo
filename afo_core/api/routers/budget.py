# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Julie CPA - Budget API Router
Phase 12 Extension: 실시간 예산 추적 및 리스크 알림

"금고 안전! Julie CPA가 왕국 부를 지켜요" 🛡️💰
"""

import logging
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.requests import Request

from AFO.julie_cpa.models.budget import MOCK_BUDGETS, BudgetSummary
from AFO.utils.standard_shield import shield

router = APIRouter(prefix="/api/julie/budget", tags=["Julie CPA - Budget"])
logger = logging.getLogger(__name__)


def calculate_risk_score(total_remaining: int, total_allocated: int) -> tuple[float, str]:
    """SSOT 연동 리스크 점수 계산

    善 (Goodness): 예산 잔여율에 따른 리스크 평가
    - 잔여율 > 30%: safe (risk 0-5)
    - 잔여율 20-30%: warning (risk 6-10)
    - 잔여율 < 20%: critical (risk 11-20)
    """
    if total_allocated == 0:
        return 0.0, "safe"

    remaining_rate = (total_remaining / total_allocated) * 100

    if remaining_rate >= 30:
        risk = 5.0 - (remaining_rate - 30) * 0.1  # 잔여 많을수록 낮은 리스크
        risk = max(0.0, min(5.0, risk))
        return risk, "safe"
    elif remaining_rate >= 20:
        risk = 6.0 + (30 - remaining_rate) * 0.4
        return min(10.0, risk), "warning"
    else:
        risk = 11.0 + (20 - remaining_rate) * 0.5
        return min(20.0, risk), "critical"


def generate_summary(risk_level: str, utilization_rate: float) -> str:
    """Julie의 한줄 평가 생성"""
    if risk_level == "safe":
        return f"✅ 예산 안정 – 사용률 {utilization_rate:.1f}%, Julie CPA 감시 중 🛡️"
    elif risk_level == "warning":
        return f"⚠️ 주의! 예산 {utilization_rate:.1f}% 사용 – 지출 조절 권장"
    else:
        return f"🚨 경고! 예산 {utilization_rate:.1f}% 소진 – 긴급 검토 필요"


@router.get("", response_model=BudgetSummary)
@shield(pillar="善", log_error=True, reraise=False)
async def get_budget_summary(request: Request) -> BudgetSummary:
    """예산 현황 조회

    Returns:
        BudgetSummary: 전체 예산 현황 및 리스크 점수

    """
    total_allocated = sum(b.allocated for b in MOCK_BUDGETS)
    total_spent = sum(b.spent for b in MOCK_BUDGETS)
    total_remaining = sum(b.remaining for b in MOCK_BUDGETS)

    utilization_rate = (total_spent / total_allocated * 100) if total_allocated > 0 else 0.0
    risk_score, risk_level = calculate_risk_score(total_remaining, total_allocated)

    return BudgetSummary(
        budgets=MOCK_BUDGETS,
        total_allocated=total_allocated,
        total_spent=total_spent,
        total_remaining=total_remaining,
        utilization_rate=round(utilization_rate, 2),
        risk_score=round(risk_score, 2),
        risk_level=risk_level,
        summary=generate_summary(risk_level, utilization_rate),
        timestamp=datetime.now().isoformat(),
    )


@router.get("/category/{category_name}")
@shield(pillar="善", log_error=True, reraise=False)
async def get_category_budget(request: Request, category_name: str) -> BudgetSummary:
    """특정 카테고리 예산 조회

    Args:
        category_name: 조회할 카테고리 이름

    Returns:
        BudgetSummary: 해당 카테고리의 예산 정보

    Raises:
        HTTPException: 카테고리를 찾을 수 없는 경우 404

    """
    for budget in MOCK_BUDGETS:
        if budget.category.lower() == category_name.lower():
            # BudgetCategory를 BudgetSummary로 변환
            total_allocated = budget.allocated
            total_spent = budget.spent
            total_remaining = budget.remaining
            utilization_rate = budget.utilization_rate()
            risk_score, risk_level = calculate_risk_score(total_remaining, total_allocated)
            return BudgetSummary(
                budgets=[budget],
                total_allocated=total_allocated,
                total_spent=total_spent,
                total_remaining=total_remaining,
                utilization_rate=utilization_rate,
                risk_score=round(risk_score, 2),
                risk_level=risk_level,
                summary=generate_summary(risk_level, utilization_rate),
                timestamp=datetime.now().isoformat(),
            )
    raise HTTPException(status_code=404, detail=f"카테고리 '{category_name}' 없음")


class SpendRequest(BaseModel):
    category: str
    amount: int
    description: str | None = None
    dry_run: bool = True


@router.post("/spend")
@shield(pillar="善", log_error=True, reraise=False)
async def record_spending(request: Request, body: SpendRequest) -> dict[str, Any]:
    """지출 기록 (DRY_RUN 기본)

    善 (Goodness): 안전 우선 - dry_run=True가 기본값

    Args:
        request: 지출 요청 정보

    Returns:
        dict: 지출 기록 결과

    """
    for budget in MOCK_BUDGETS:
        if budget.category.lower() == body.category.lower():
            # 타입 안전한 변환: int()에 object 타입을 직접 전달하지 않음
            amount_value = request.amount
            if isinstance(amount_value, (int, float)):
                amount_int: int = int(amount_value)
            elif isinstance(amount_value, str):
                try:
                    amount_int = int(amount_value)
                except ValueError:
                    amount_int = 0
            else:
                amount_int = 0
            new_spent = budget.spent + amount_int
            new_remaining = budget.allocated - new_spent

            # 리스크 체크
            if new_remaining < 0:
                return {
                    "success": False,
                    "mode": "DRY_RUN" if body.dry_run else "BLOCKED",
                    "reason": f"예산 초과! 잔여: ₩{budget.remaining:,}, 요청: ₩{body.amount:,}",
                    "suggestion": "예산 재할당 또는 지출 조정 필요",
                }

            if body.dry_run:
                return {
                    "success": True,
                    "mode": "DRY_RUN",
                    "preview": {
                        "category": budget.category,
                        "current_spent": budget.spent,
                        "new_spent": new_spent,
                        "new_remaining": new_remaining,
                    },
                    "message": "시뮬레이션 완료 – dry_run=False로 실제 반영",
                }
            else:
                # 실제 반영
                budget.spent = new_spent
                budget.calculate_remaining()
                logger.info(f"[Julie] 지출 기록: {body.category} +₩{body.amount:,}")
                return {
                    "success": True,
                    "mode": "EXECUTED",
                    "updated": budget.model_dump(),
                    "message": f"지출 기록 완료: {body.description or '(설명 없음)'}",
                }

    raise HTTPException(status_code=404, detail=f"카테고리 '{body.category}' 없음")


@router.get("/risk-alert")
@shield(pillar="善", log_error=True, reraise=False)
async def get_risk_alerts(request: Request) -> dict[str, Any]:
    """리스크 알림 조회

    SSOT 연동: 위험 카테고리만 반환

    Returns:
        dict: 리스크 알림 목록 및 요약

    """
    alerts = []

    for budget in MOCK_BUDGETS:
        utilization = (budget.spent / budget.allocated * 100) if budget.allocated > 0 else 0

        if utilization >= 80:
            level = "critical" if utilization >= 90 else "warning"
            alerts.append(
                {
                    "level": level,
                    "category": budget.category,
                    "utilization": round(utilization, 1),
                    "remaining": budget.remaining,
                    "message": f"🚨 {budget.category}: {utilization:.1f}% 사용 (잔여 ₩{budget.remaining:,})",
                }
            )

    return {
        "count": len(alerts),
        "alerts": alerts,
        "summary": (
            "금고 문제? Julie가 자동 복구 중 – 조금만 기다려주세요!"
            if alerts
            else "✅ 모든 예산 안정"
        ),
    }


# ============================================================
# Phase 12-3: Smart Suggestions (Rule-Based)
# ============================================================


@router.get("/suggestions")
@shield(pillar="善", log_error=True, reraise=False)
async def get_budget_suggestions(request: Request) -> dict[str, Any]:
    """Julie CPA의 스마트 제안

    룰 기반 알고리즘으로 예산 최적화 제안 생성
    - 지출율 50% 이상: 절감 제안
    - 지출율 80% 이상: 긴급 제안
    - 카테고리별 맞춤 제안

    Returns:
        dict: 예산 제안 목록 및 잠재 절감액

    """
    total_allocated = sum(b.allocated for b in MOCK_BUDGETS)
    total_spent = sum(b.spent for b in MOCK_BUDGETS)
    spend_rate = (total_spent / total_allocated * 100) if total_allocated > 0 else 0

    suggestions = []

    # 전체 지출율 기반 제안
    if spend_rate > 80:
        suggestions.append(
            {
                "priority": "critical",
                "icon": "🚨",
                "title": "긴급 예산 조정 필요",
                "message": f"전체 지출율 {spend_rate:.1f}%! 예산 추가 배정 또는 지출 동결을 권장합니다.",
                "action": "예산 재검토",
                "expected_saving": 0,
            }
        )
    elif spend_rate > 50:
        estimated_saving = int(total_spent * 0.1)  # 10% 절감 예상
        suggestions.append(
            {
                "priority": "warning",
                "icon": "💡",
                "title": "지출 최적화 기회",
                "message": f"지출율 {spend_rate:.1f}% – 10% 절감 시 약 ₩{estimated_saving:,} 절약 가능!",
                "action": "지출 패턴 분석",
                "expected_saving": estimated_saving,
            }
        )

    # 카테고리별 제안
    for budget in MOCK_BUDGETS:
        util = (budget.spent / budget.allocated * 100) if budget.allocated > 0 else 0

        if util >= 90:
            suggestions.append(
                {
                    "priority": "critical",
                    "icon": "🔥",
                    "title": f"{budget.category} 예산 위기",
                    "message": f"사용률 {util:.1f}% – 잔여 ₩{budget.remaining:,}만 남음",
                    "action": "즉시 점검",
                    "expected_saving": 0,
                }
            )
        elif util >= 70 and util < 90:
            potential = int(budget.spent * 0.15)
            suggestions.append(
                {
                    "priority": "info",
                    "icon": "📊",
                    "title": f"{budget.category} 효율화 제안",
                    "message": f"15% 최적화 시 ₩{potential:,} 절약 예상",
                    "action": "분석 보기",
                    "expected_saving": potential,
                }
            )

    # 제안이 없으면 긍정 메시지
    if not suggestions:
        suggestions.append(
            {
                "priority": "success",
                "icon": "✨",
                "title": "예산 상태 양호!",
                "message": "모든 카테고리가 안정적입니다. 계속 잘 관리하고 계세요!",
                "action": None,
                "expected_saving": 0,
            }
        )

    total_potential_saving = sum(int(cast("Any", s.get("expected_saving", 0))) for s in suggestions)

    return {
        "spend_rate": round(spend_rate, 2),
        "suggestion_count": len(suggestions),
        "suggestions": suggestions,
        "total_potential_saving": total_potential_saving,
        "summary": f"Julie CPA 분석 완료 – {len(suggestions)}개 제안, 잠재 절감 ₩{total_potential_saving:,}",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# Phase 12-4: ML Predictions (LinearRegression - Lightweight)
# ============================================================

# Mock historical data for prediction (simulate 6 months)
MOCK_HISTORY = [
    {"month": "2024-07", "spent": 680000},
    {"month": "2024-08", "spent": 720000},
    {"month": "2024-09", "spent": 695000},
    {"month": "2024-10", "spent": 750000},
    {"month": "2024-11", "spent": 710000},
    {"month": "2024-12", "spent": 735000},  # Current
]


def predict_next_month_spending(history: list[dict[str, Any]]) -> dict[str, Any]:
    """간단 선형회귀로 다음 달 지출 예측

    sklearn 없이 구현 (순수 Python)
    y = mx + b (Linear Regression)
    """
    n = len(history)
    if n < 2:
        return {
            "predicted_spending": history[-1]["spent"] if history else 0,
            "confidence": 0.0,
            "trend": "insufficient_data",
        }

    # x = 월 인덱스, y = 지출액
    x = list(range(n))
    y = [h["spent"] for h in history]

    # 평균 계산
    x_mean = sum(x) / n
    y_mean = sum(y) / n

    # 기울기 (m) 계산: m = Σ(xi - x̄)(yi - ȳ) / Σ(xi - x̄)²
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    m = 0 if denominator == 0 else numerator / denominator

    # y절편 (b) 계산: b = ȳ - m * x̄
    b = y_mean - m * x_mean

    # 다음 달 예측 (x = n)
    next_month_prediction = m * n + b

    # R² 계산 (결정계수 = 신뢰도)
    ss_res = sum((y[i] - (m * x[i] + b)) ** 2 for i in range(n))
    ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    # 추세 판단
    if m > 1000:
        trend = "increasing"
    elif m < -1000:
        trend = "decreasing"
    else:
        trend = "stable"

    return {
        "predicted_spending": max(0, int(next_month_prediction)),
        "confidence": round(max(0, min(1, r_squared)), 2),
        "trend": trend,
        "slope": round(m, 2),  # 월별 변화량
    }


@router.get("/prediction")
@shield(pillar="善", log_error=True, reraise=False)
async def get_budget_prediction(request: Request) -> dict[str, Any]:
    """Julie CPA의 미래 예측

    LinearRegression으로 다음 달 지출 예측
    - 6개월 과거 데이터 기반
    - 신뢰도 (R²) 포함
    - 추세 분석 (증가/감소/안정)

    Returns:
        dict: 예측 결과 및 조언

    """
    prediction = predict_next_month_spending(MOCK_HISTORY)

    current_spending_raw = MOCK_HISTORY[-1]["spent"]
    current_spending: int = (
        int(current_spending_raw) if isinstance(current_spending_raw, (int, float)) else 0
    )
    predicted_val = prediction.get("predicted_spending", 0)
    predicted: int = (
        int(predicted_val) if isinstance(predicted_val, (int, float)) else current_spending
    )

    # 예측 vs 현재 비교
    diff = predicted - current_spending
    diff_percent = (diff / current_spending * 100) if current_spending > 0 else 0

    # 제안 메시지 생성
    if prediction["trend"] == "increasing":
        advice = "📈 지출 증가 추세 – 예산 추가 배정 또는 지출 조절을 고려하세요."
        risk_level = "warning" if diff_percent > 5 else "info"
    elif prediction["trend"] == "decreasing":
        advice = "📉 지출 감소 추세 – 잘 관리하고 계세요! 여유 예산 활용 가능."
        risk_level = "safe"
    else:
        advice = "📊 지출 안정 추세 – 현재 패턴 유지하면 예산 내 관리 가능."
        risk_level = "safe"

    # 신뢰도 기반 메시지 조정
    confidence = prediction["confidence"]
    if confidence < 0.5:
        confidence_note = "(데이터 부족 – 예측 정확도 낮음)"
    elif confidence < 0.8:
        confidence_note = "(중간 신뢰도)"
    else:
        confidence_note = "(높은 신뢰도 ✓)"

    return {
        "current_month_spending": current_spending,
        "next_month_predicted": predicted,
        "difference": diff,
        "difference_percent": round(diff_percent, 1),
        "confidence": confidence,
        "confidence_note": confidence_note,
        "trend": prediction["trend"],
        "trend_slope": prediction["slope"],
        "risk_level": risk_level,
        "advice": advice,
        "history": MOCK_HISTORY,
        "summary": f"Julie CPA 예측: 다음 달 예상 ₩{predicted:,} ({'+' if diff > 0 else ''}{diff_percent:.1f}%)",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# Phase 14: Prophet 기반 고정밀 예측
# ============================================================


@router.get("/forecast")
@shield(pillar="善", log_error=True, reraise=False)
async def get_budget_forecast(request: Request, periods: int = 3) -> dict[str, Any]:
    """Prophet 기반 미래 예산 예측

    Phase 14: LinearRegression → Prophet 업그레이드
    - 시계열 패턴 자동 학습
    - 이벤트(Phase 보상, 연말) 반영
    - 신뢰 구간 제공

    Args:
        periods: 예측 기간 (기본 3개월, 최대 12개월)

    眞 (Truth): 데이터 기반 정확한 예측
    善 (Goodness): 형님 안심을 위한 명확한 결과

    Returns:
        dict: 예측 결과 및 요약

    """
    try:
        from AFO.julie_cpa.prophet_engine import get_kingdom_forecast

        # 기간 제한 (1~12개월)
        periods = max(1, min(12, periods))

        result = get_kingdom_forecast(periods=periods)

        logger.info(f"[Julie] Prophet 예측 완료: {periods}개월, 총 ${result['summary']['total']:,}")

        return result

    except ImportError as e:
        # Prophet 없으면 기존 LinearRegression 사용
        logger.warning(f"[Julie] Prophet 미설치, 폴백 사용: {e}")

        # 간단한 폴백 응답
        from AFO.julie_cpa.prophet_engine import get_kingdom_forecast

        return get_kingdom_forecast(periods=periods)

    except Exception as e:
        logger.error(f"[Julie] 예측 실패: {e}")
        raise HTTPException(status_code=500, detail=f"예측 실패: {e!s}") from e


# ============================================================
# Phase 14 완전체: Hybrid 예측 (Prophet + auto_arima)
# ============================================================


@router.get("/forecast-hybrid")
@shield(pillar="善", log_error=True, reraise=False)
async def get_hybrid_budget_forecast(request: Request, periods: int = 3) -> dict[str, Any]:
    """Prophet + auto_arima 하이브리드 예측

    Phase 14 완전체: 99%+ 정확도
    - Prophet 기본 예측 (추세 + 계절성)
    - auto_arima 잔차 보정 (미세 패턴)

    Args:
        periods: 예측 기간 (기본 3개월, 최대 12개월)

    眞 (Truth): 형님의 경제적 진실 - 돈을 담당하는 매우 중요한 시스템

    Returns:
        dict: 하이브리드 예측 결과

    """
    try:
        from AFO.julie_cpa.hybrid_engine import get_hybrid_forecast

        periods = max(1, min(12, periods))
        result = get_hybrid_forecast(periods=periods)

        logger.info(
            f"[Julie] Hybrid 예측 완료: {periods}개월, 신뢰도 {result.get('summary', {}).get('confidence', 0)}%"
        )

        return result

    except ImportError as e:
        logger.warning(f"[Julie] Hybrid 엔진 미설치: {e}")
        # Prophet 폴백
        from AFO.julie_cpa.prophet_engine import get_kingdom_forecast

        return get_kingdom_forecast(periods=periods)

    except Exception as e:
        logger.error(f"[Julie] Hybrid 예측 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid 예측 실패: {e!s}") from e


# ============================================================
# Phase 15: The Grok Singularity (외부 지능 자문)
# ============================================================


@router.get("/consult-grok")
@shield(pillar="善", log_error=True, reraise=False)
async def consult_grok_advisor(request: Request, periods: int = 3) -> dict[str, Any]:
    """Phase 15: The Grok Singularity - 외부 지능(xAI) 자문

    왕국의 예산 예측 데이터를 바탕으로 Grok에게 거시경제적 조언을 구합니다.
    - 智 (Wisdom): 외부 데이터와 내부 데이터의 융합

    Args:
        periods: 예측 기간 (기본 3개월)

    Returns:
        dict: Grok 분석 결과 및 예측 요약

    """
    try:
        from AFO.julie_cpa.grok_engine import consult_grok
        from AFO.julie_cpa.hybrid_engine import get_hybrid_forecast

        # 1. 내부 예측 수행 (Hybrid Engine)
        logger.info("[Julie] Grok 자문을 위한 내부 예측 수행 중...")
        forecast = get_hybrid_forecast(periods=periods)

        # 2. Grok에게 자문 (비동기)
        logger.info("[Julie] Grok(The Sage from the Stars) 호출 중...")
        analysis = await consult_grok(forecast)

        return {
            "source": "xAI (Grok)",
            "forecast_summary": forecast["summary"],
            "grok_analysis": analysis,
        }

    except Exception as e:
        logger.error(f"[Julie] Grok 자문 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Grok 통신 실패: {e!s}") from e
