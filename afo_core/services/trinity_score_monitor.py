# Trinity Score 추이 분석 모니터링 서비스
"""
Trinity Score의 시간별 추이 분석 및 이상 감지
Prometheus 메트릭 기반 모니터링
"""

import logging
import time
from dataclasses import dataclass

from AFO.domain.metrics.trinity import TrinityMetrics
from AFO.domain.metrics.trinity_ssot import THRESHOLD_BALANCE_WARNING

logger = logging.getLogger(__name__)

# 기존 메트릭 시스템 사용 (중복 방지)
try:
    from utils.metrics import PROMETHEUS_AVAILABLE

    METRICS_AVAILABLE = PROMETHEUS_AVAILABLE
    logger.info("Using existing metrics system for Trinity Score monitoring")
except ImportError:
    METRICS_AVAILABLE = False
    logger.warning("Metrics system not available, Trinity Score monitoring disabled")


@dataclass
class TrinityScoreSample:
    """Trinity Score 샘플 데이터"""

    timestamp: float
    trinity_score: float
    truth: float = 0.0
    goodness: float = 0.0
    beauty: float = 0.0
    filial_serenity: float = 0.0
    eternity: float = 0.0
    balance_status: str = "unknown"


class TrinityScoreMonitor:
    """Trinity Score 모니터링 클래스"""

    def __init__(self, max_history: int = 100) -> None:
        self.max_history = max_history
        self.samples: list[TrinityScoreSample] = []

        # 기존 메트릭 시스템 사용
        if METRICS_AVAILABLE:
            # 기존 메트릭에서 가져오기 또는 생성
            try:
                from prometheus_client import Histogram

                from utils.metrics import get_or_create_metric

                self.trinity_score_histogram = get_or_create_metric(
                    Histogram,
                    "afo_trinity_score_change",
                    "Trinity Score change rate",
                    buckets=[-1.0, -0.5, -0.2, -0.1, 0.0, 0.1, 0.2, 0.5, 1.0],
                )

                logger.info("Trinity Score monitoring initialized with existing metrics")
            except Exception as e:
                logger.warning(f"Failed to initialize histogram metric: {e}")
                self.trinity_score_histogram = None
        else:
            self.trinity_score_histogram = None
            logger.warning("Metrics system not available for Trinity Score monitoring")

    def record_current_score(self, trinity_metrics: TrinityMetrics) -> None:
        """현재 Trinity Score 기록"""
        if not trinity_metrics:
            logger.warning("No Trinity metrics provided")
            return

        sample = TrinityScoreSample(
            timestamp=time.time(),
            trinity_score=trinity_metrics.trinity_score,
            truth=trinity_metrics.truth,
            goodness=trinity_metrics.goodness,
            beauty=trinity_metrics.beauty,
            filial_serenity=trinity_metrics.filial_serenity,
            eternity=trinity_metrics.eternity,
            balance_status=trinity_metrics.balance_status,
        )

        self.samples.append(sample)

        # 최대 히스토리 유지
        if len(self.samples) > self.max_history:
            self.samples = self.samples[-self.max_history :]

        # 기존 메트릭 시스템 사용
        if METRICS_AVAILABLE:
            try:
                from utils.metrics import update_trinity_scores

                # 기존 메트릭 시스템으로 기록
                scores = {
                    "truth": sample.truth,
                    "goodness": sample.goodness,
                    "beauty": sample.beauty,
                    "serenity": sample.filial_serenity,
                    "eternity": sample.eternity,
                    "total": sample.trinity_score,
                }
                update_trinity_scores(scores)

                logger.debug(
                    f"Trinity Score metrics recorded via existing system: {sample.trinity_score:.3f}"
                )

            except Exception as e:
                logger.error(f"Failed to record Trinity Score metrics: {e}")

        # 추이 분석 및 이상 감지
        self._analyze_trends_and_anomalies(sample)

    def _analyze_trends_and_anomalies(self, current_sample: TrinityScoreSample) -> None:
        """추이 분석 및 이상 감지"""
        if len(self.samples) < 2:
            return

        prev_sample = self.samples[-2]

        # 변화율 계산
        change = current_sample.trinity_score - prev_sample.trinity_score

        # 히스토그램 기록
        if self.trinity_score_histogram:
            try:
                self.trinity_score_histogram.observe(change)
            except Exception as e:
                logger.error(f"Failed to record histogram: {e}")

        # 이상 감지 (급격한 변화) - SSOT: trinity_ssot.py
        if abs(change) > THRESHOLD_BALANCE_WARNING:
            logger.warning(
                f"Trinity Score anomaly detected: {change:.3f} change "
                f"({prev_sample.trinity_score:.3f} → {current_sample.trinity_score:.3f})"
            )

    def get_recent_samples(self, limit: int = 20) -> list[dict]:
        """최근 샘플 반환"""
        return [
            {
                "timestamp": s.timestamp,
                "trinity_score": s.trinity_score,
                "truth": s.truth,
                "goodness": s.goodness,
                "beauty": s.beauty,
                "serenity": s.filial_serenity,
                "eternity": s.eternity,
                "balance_status": s.balance_status,
            }
            for s in self.samples[-limit:]
        ][::-1]  # 최신순 정렬

    def get_trend_analysis(self, window_minutes: int = 60) -> dict:
        """추이 분석 (Alias for get_recent_trends)"""
        return self.get_recent_trends(window_minutes)

    def get_recent_trends(self, window_minutes: int = 60) -> dict:
        """최근 추이 분석"""
        now = time.time()
        window_start = now - (window_minutes * 60)

        recent_samples = [s for s in self.samples if s.timestamp >= window_start]

        if len(recent_samples) < 2:
            return {"trend": "insufficient_data", "samples": len(recent_samples)}

        # 추세 계산
        first_score = recent_samples[0].trinity_score
        last_score = recent_samples[-1].trinity_score
        total_change = last_score - first_score

        trend = "stable"
        if total_change > 0.1:
            trend = "improving"
        elif total_change < -0.1:
            trend = "declining"

        return {
            "trend": trend,
            "total_change": total_change,
            "samples": len(recent_samples),
            "avg_score": sum(s.trinity_score for s in recent_samples) / len(recent_samples),
            "time_range_minutes": window_minutes,
        }

    def get_statistics(self) -> dict:
        """통계 정보 반환"""
        if not self.samples:
            return {"status": "no_data"}

        scores = [s.trinity_score for s in self.samples]

        return {
            "total_samples": len(self.samples),
            "current_score": self.samples[-1].trinity_score if self.samples else 0.0,
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "balance_distribution": {
                status: sum(1 for s in self.samples if s.balance_status == status)
                for status in {s.balance_status for s in self.samples}
            },
        }


# 전역 모니터 인스턴스
trinity_score_monitor = TrinityScoreMonitor()


def record_trinity_score_metrics(trinity_metrics: TrinityMetrics) -> None:
    """편의 함수: Trinity Score 메트릭 기록"""
    trinity_score_monitor.record_current_score(trinity_metrics)
