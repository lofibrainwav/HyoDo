# Trinity Score: 90.0 (Established by Chancellor)
"""Julie CPA Prophet Prediction Engine - 미래 지출 예측

Phase 14: LinearRegression → Prophet 업그레이드
Facebook Prophet 기반 정밀 시계열 예측

眞 (Truth): 데이터 기반 정확한 예측
善 (Goodness): 미래 리스크 사전 경고
孝 (Serenity): 자동화된 예측으로 형님 안심
永 (Eternity): 왕국의 장기 재정 안정

의존성: prophet (pip install prophet 또는 conda install -c conda-forge prophet)
"""

import logging
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)

# Prophet은 선택적 의존성
try:
    from prophet import Prophet

    PROPHET_AVAILABLE = True
    logger.info("[ProphetEngine] Prophet 라이브러리 로드 완료")
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("[ProphetEngine] Prophet not installed. Using fallback LinearRegression.")


# =============================================================================
# Mock Historical Data (실제로는 DB에서 가져옴)
# =============================================================================

MOCK_KINGDOM_SPEND = [
    {"ds": "2025-01-01", "y": 62000},
    {"ds": "2025-02-01", "y": 68000},
    {"ds": "2025-03-01", "y": 71000},
    {"ds": "2025-04-01", "y": 69000},
    {"ds": "2025-05-01", "y": 75000},
    {"ds": "2025-06-01", "y": 82000},
    {"ds": "2025-07-01", "y": 78000},
    {"ds": "2025-08-01", "y": 81000},
    {"ds": "2025-09-01", "y": 85000},
    {"ds": "2025-10-01", "y": 83000},
    {"ds": "2025-11-01", "y": 88000},
    {"ds": "2025-12-01", "y": 95000},  # 연말 spike
]

# Phase 보상 등 특별 이벤트
KINGDOM_EVENTS = [
    {
        "holiday": "phase_reward",
        "ds": "2025-06-30",
        "lower_window": 0,
        "upper_window": 2,
    },
    {"holiday": "year_end", "ds": "2025-12-31", "lower_window": -3, "upper_window": 2},
]


def get_historical_data(category: str | None = None) -> pd.DataFrame:
    """과거 지출 데이터 조회

    실제로는 DB에서 가져오지만, 현재는 Mock 데이터 반환
    """
    df = pd.DataFrame(MOCK_KINGDOM_SPEND)
    df["ds"] = pd.to_datetime(df["ds"])
    return df


# =============================================================================
# Advanced Tuning Parameters (Phase 14-10)
# =============================================================================

ADVANCED_TUNING = {
    "changepoint_prior_scale": 0.15,  # 추세 변화 민감도 ↑
    "changepoint_range": 0.95,  # 변화 검출 범위 95%
    "seasonality_prior_scale": 30.0,  # 계절성 강도 ↑
    "holidays_prior_scale": 50.0,  # 이벤트 영향 강도 ↑
    "seasonality_mode": "multiplicative",  # 지출 증가 시 계절성도 커짐
    "yearly_seasonality": True,
    "weekly_seasonality": False,
    "daily_seasonality": False,
    "interval_width": 0.95,  # 95% 불확실성 구간
    "uncertainty_samples": 2000,  # 더 정확한 구간
}


def predict_with_prophet(
    historical_data: pd.DataFrame,
    periods: int = 3,
    freq: str = "MS",  # Monthly Start
    include_events: bool = True,
    growth: str = "linear",
    yearly_seasonality: bool = True,
    weekly_seasonality: bool = False,
    use_advanced_tuning: bool = True,  # Phase 14-10: 고급 튜닝 활성화
) -> dict:
    """Prophet 기반 미래 예측

    Args:
        historical_data: 과거 데이터 (ds, y 컬럼 필수)
        periods: 예측 기간 (기본 3개월)
        freq: 주기 (MS=월초, D=일별)
        include_events: 왕국 이벤트 포함 여부
        growth: 성장 모델 (linear, logistic)
        yearly_seasonality: 연간 계절성
        weekly_seasonality: 주간 계절성

    Returns:
        예측 결과 딕셔너리

    """
    if not PROPHET_AVAILABLE:
        return _fallback_linear_prediction(historical_data, periods)

    try:
        # 이벤트 데이터 준비
        holidays = None
        if include_events:
            holidays = pd.DataFrame(KINGDOM_EVENTS)
            holidays["ds"] = pd.to_datetime(holidays["ds"])

        # Phase 14-10: 고급 튜닝 적용
        if use_advanced_tuning:
            model = Prophet(
                growth=growth,
                changepoint_prior_scale=ADVANCED_TUNING["changepoint_prior_scale"],
                changepoint_range=ADVANCED_TUNING["changepoint_range"],
                seasonality_prior_scale=ADVANCED_TUNING["seasonality_prior_scale"],
                holidays_prior_scale=ADVANCED_TUNING["holidays_prior_scale"],
                seasonality_mode=ADVANCED_TUNING["seasonality_mode"],
                yearly_seasonality=ADVANCED_TUNING["yearly_seasonality"],
                weekly_seasonality=ADVANCED_TUNING["weekly_seasonality"],
                daily_seasonality=ADVANCED_TUNING["daily_seasonality"],
                interval_width=ADVANCED_TUNING["interval_width"],
                uncertainty_samples=ADVANCED_TUNING["uncertainty_samples"],
                holidays=holidays,
            )
            # 커스텀 Phase 6개월 주기 seasonality 추가
            model.add_seasonality(name="phase_cycle", period=180, fourier_order=10)
            logger.info("[ProphetEngine] 고급 튜닝 적용됨 (Phase 14-10)")
        else:
            # 기본 설정
            model = Prophet(
                growth=growth,
                yearly_seasonality=yearly_seasonality,
                weekly_seasonality=weekly_seasonality,
                daily_seasonality=False,
                seasonality_mode="multiplicative",
                holidays=holidays,
            )

        # 미국 휴일 추가 (선택)
        model.add_country_holidays(country_name="US")

        # 모델 학습
        model.fit(historical_data)

        # 미래 날짜 생성
        future = model.make_future_dataframe(periods=periods, freq=freq)

        # 예측
        forecast = model.predict(future)

        # 미래 기간만 추출
        last_historical = historical_data["ds"].max()
        future_forecast = forecast[forecast["ds"] > last_historical]

        # 결과 포맷팅
        predictions = []
        for _, row in future_forecast.iterrows():
            predictions.append(
                {
                    "date": row["ds"].strftime("%Y-%m-%d"),
                    "month": row["ds"].strftime("%Y-%m"),
                    "predicted": int(row["yhat"]),
                    "lower": int(row["yhat_lower"]),
                    "upper": int(row["yhat_upper"]),
                    "trend": int(row["trend"]),
                }
            )

        total_predicted = sum(p["predicted"] for p in predictions)
        avg_predicted = total_predicted // len(predictions) if predictions else 0

        # Confidence 계산 (예측 범위 기반)
        avg_range = (
            sum(p["upper"] - p["lower"] for p in predictions) / len(predictions)
            if predictions
            else 0
        )
        confidence = (
            max(50, min(95, 100 - (avg_range / avg_predicted * 50))) if avg_predicted > 0 else 50
        )

        logger.info(f"[ProphetEngine] 예측 완료: {len(predictions)}개월, 총 ${total_predicted:,}")

        return {
            "engine": "Prophet",
            "periods": periods,
            "predictions": predictions,
            "summary": {
                "total": total_predicted,
                "average": avg_predicted,
                "confidence": round(confidence, 1),
            },
            "message": f"Julie CPA: 향후 {periods}개월 예상 지출 ${total_predicted:,} (신뢰도 {confidence:.0f}%)",
            "advice": _generate_advice(predictions, historical_data),
        }

    except Exception as e:
        logger.error(f"[ProphetEngine] 예측 실패: {e}")
        return _fallback_linear_prediction(historical_data, periods)


def _fallback_linear_prediction(df: pd.DataFrame, periods: int) -> dict:
    """Prophet 없을 때 LinearRegression 폴백"""
    from sklearn.linear_model import LinearRegression

    # 간단한 선형 회귀
    df = df.copy()
    df["x"] = range(len(df))

    features = df[["x"]].values
    y = df["y"].values

    model = LinearRegression()
    model.fit(features, y)

    # 미래 예측
    predictions = []
    last_date = df["ds"].max()

    for i in range(1, periods + 1):
        future_x = len(df) + i - 1
        predicted = int(model.predict([[future_x]])[0])
        future_date = last_date + timedelta(days=30 * i)

        predictions.append(
            {
                "date": future_date.strftime("%Y-%m-%d"),
                "month": future_date.strftime("%Y-%m"),
                "predicted": predicted,
                "lower": int(predicted * 0.9),
                "upper": int(predicted * 1.1),
                "trend": predicted,
            }
        )

    total = sum(p["predicted"] for p in predictions)

    logger.info(f"[ProphetEngine] Fallback 예측: {periods}개월, 총 ${total:,}")

    return {
        "engine": "LinearRegression (Fallback)",
        "periods": periods,
        "predictions": predictions,
        "summary": {
            "total": total,
            "average": total // periods,
            "confidence": 65.0,  # 폴백은 낮은 신뢰도
        },
        "message": f"Julie CPA: 향후 {periods}개월 예상 지출 ${total:,} (기본 예측)",
        "advice": "Prophet 설치 권장: conda install -c conda-forge prophet",
    }


def _generate_advice(predictions: list, historical: pd.DataFrame) -> str:
    """예측 결과 기반 조언 생성

    善 (Goodness): 형님에게 유익한 조언
    """
    if not predictions:
        return "데이터 부족 - 더 많은 기록이 필요합니다."

    # 과거 평균
    hist_avg = historical["y"].mean()

    # 미래 평균
    future_avg = sum(p["predicted"] for p in predictions) / len(predictions)

    # 성장률
    growth_rate = ((future_avg - hist_avg) / hist_avg) * 100

    advice_parts = []

    if growth_rate > 10:
        advice_parts.append(f"⚠️ 지출 증가 추세 (+{growth_rate:.1f}%): 예산 조정 검토 필요")
    elif growth_rate < -5:
        advice_parts.append(f"✅ 지출 감소 추세 ({growth_rate:.1f}%): 절약 효과 확인!")
    else:
        advice_parts.append(f"📊 안정적 지출 패턴 ({growth_rate:+.1f}%)")

    # 연말 경고
    for p in predictions:
        if "12" in p["month"] or "01" in p["month"]:
            advice_parts.append("🎄 연말/연초 spike 예상 - 여유 자금 확보 권장")
            break

    return " | ".join(advice_parts)


def predict_category_spend(category: str, periods: int = 3) -> dict:
    """카테고리별 지출 예측"""
    df = get_historical_data(category)
    return predict_with_prophet(df, periods=periods)


def get_kingdom_forecast(periods: int = 3) -> dict:
    """왕국 전체 지출 예측 (메인 API)

    眞 (Truth): 정확한 예측
    孝 (Serenity): 형님 안심을 위한 명확한 결과
    """
    df = get_historical_data()
    result = predict_with_prophet(df, periods=periods)

    # 추가 메타데이터
    result["kingdom_status"] = "healthy" if result["summary"]["confidence"] > 70 else "monitoring"
    result["last_updated"] = datetime.now().isoformat()
    result["data_points"] = len(df)

    return result
