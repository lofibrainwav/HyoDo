from __future__ import annotations

import sys

from prometheus_client import (
    REGISTRY,
)
from prometheus_client import (
    Counter as _Counter,
)
from prometheus_client import (
    Gauge as _Gauge,
)
from prometheus_client import (
    Histogram as _Histogram,
)

from AFO.domain.metrics.trinity_ssot import THRESHOLD_BALANCE_WARNING, TrinityWeights

# Ensure both module paths resolve to the same instance to prevent duplicate registry entries.
if __name__ == "domain.metrics.prometheus":
    sys.modules.setdefault("AFO.domain.metrics.prometheus", sys.modules[__name__])
elif __name__ == "AFO.domain.metrics.prometheus":
    sys.modules.setdefault("domain.metrics.prometheus", sys.modules[__name__])


def Counter(name: str, documentation: str, labelnames: tuple[str, ...] = (), **kwargs) -> None:
    """Create or reuse a Counter to avoid duplicate registry entries."""
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]
    return _Counter(name, documentation, labelnames, **kwargs)


def Gauge(name: str, documentation: str, labelnames: tuple[str, ...] = (), **kwargs) -> None:
    """Create or reuse a Gauge to avoid duplicate registry entries."""
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]
    return _Gauge(name, documentation, labelnames, **kwargs)


def Histogram(name: str, documentation: str, labelnames: tuple[str, ...] = (), **kwargs) -> None:
    """Create or reuse a Histogram to avoid duplicate registry entries."""
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]
    return _Histogram(name, documentation, labelnames, **kwargs)


# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Prometheus Metrics Definitions
Centralized location for all Prometheus metrics to avoid circular imports and duplication.
"""


# ============================================================
# VibeCoding Metrics (Phase 3.2)
# ============================================================

# Phase 9 Trinity SBT Metrics
trinity_sbt_minted = Counter(
    "afo_trinity_sbt_minted_total", "Total number of Trinity SBTs minted", ["framework"]
)

# 선확인, 후보고 (Scout First, Report After)
dry_run_executions = Counter("afo_dry_run_executions_total", "DRY_RUN 시뮬레이션 실행 횟수")
wet_executions = Counter("afo_wet_executions_total", "WET 실제 실행 횟수")

# 선증명, 후확신 (Prove First, Confirm After)
prediction_accuracy = Gauge("afo_prediction_accuracy", "예측 정확도 (0.0-1.0)")

# 속도보다 정확성 (Accuracy Over Speed)
accurate_executions = Counter("afo_accurate_executions_total", "정확성 우선 실행 횟수")
fast_executions = Counter("afo_fast_executions_total", "속도 우선 실행 횟수")

vibecoding_compliance = Gauge(
    "afo_vibecoding_compliance_score", "VibeCoding 원칙 준수율 (0.0-1.0)", ["principle"]
)

# ============================================================
# Health Metrics (Phase 4) - 11장기 건강도
# ============================================================

health_organ_status = Gauge(
    "afo_health_organ_status",
    "11장기 건강 상태 (1=정상, 0=비정상)",
    ["organ_name", "organ_korean"],
)

health_total_score = Gauge("afo_health_total_score", "전체 건강도 점수 (0-100)")

health_healthy_organs = Gauge("afo_health_healthy_organs", "정상 장기 수 (0-11)")

health_percentage = Gauge("afo_health_percentage", "11장기 건강도 (0-100)")

api_response_time = Histogram("afo_api_response_time_seconds", "API 응답 시간 (초)")

# ============================================================
# Trinity Metrics (Phase 3.2)
# ============================================================

# 眞善美 점수 (0.0-1.0)
trinity_truth_score = Gauge(
    "afo_trinity_truth_score", "眞 (Truth) 기술 정확성 점수", ["service", "component"]
)
trinity_goodness_score = Gauge(
    "afo_trinity_goodness_score",
    "善 (Goodness) 윤리적 안정성 점수",
    ["service", "component"],
)
trinity_beauty_score = Gauge(
    "afo_trinity_beauty_score", "美 (Beauty) 사용자 경험 점수", ["service", "component"]
)
trinity_filial_serenity_score = Gauge(
    "afo_trinity_filial_serenity_score",
    "孝 (Filial Serenity) 점수",
    ["service", "component"],
)
trinity_serenity_core = Gauge(
    "afo_trinity_serenity_core", "Serenity(§) = ∛(T × G × B)", ["service", "component"]
)
trinity_score = Gauge(
    "afo_trinity_score", "Trinity Score = (T + G + B + H) / 4", ["service", "component"]
)

# Trinity 분석 횟수
trinity_analysis_total = Counter("afo_trinity_analysis_total", "Trinity 분석 완료 횟수")
trinity_calculations_total = Counter(
    "afo_trinity_calculations_total",
    "Trinity 메트릭 계산 총 횟수",
    ["service", "component", "balance_status"],
)

# Trinity 승상별 점수
trinity_strategist_score = Gauge(
    "afo_trinity_strategist_score",
    "Trinity 승상별 점수",
    ["strategist", "aspect", "weight"],
)

# Trinity 균형 델타 (Phase 8.1.3)
trinity_balance_delta = Gauge(
    "afo_trinity_balance_delta",
    "Trinity 균형 델타 (Max-Min) - Alert if >0.3",
    ["service", "component"],
)
trinity_balance_status = Gauge(
    "afo_trinity_balance_status",
    "균형 상태 (0=balanced, 1=warning, 2=imbalanced)",
    ["service", "component", "status"],
)

# ============================================================
# Ragas RAG Quality Metrics (Phase 8.1.3)
# ============================================================

ragas_faithfulness_score = Gauge(
    "afo_ragas_faithfulness_score",
    "Ragas Faithfulness 점수 (0.0-1.0) - 환각 감지",
    ["rag_system", "method"],
)
ragas_answer_relevancy_score = Gauge(
    "afo_ragas_answer_relevancy_score",
    "Ragas Answer Relevancy 점수 (0.0-1.0) - 답변 관련성",
    ["rag_system", "method"],
)
ragas_context_precision_score = Gauge(
    "afo_ragas_context_precision_score",
    "Ragas Context Precision 점수 (0.0-1.0) - 검색 정확도",
    ["rag_system", "method"],
)
ragas_context_recall_score = Gauge(
    "afo_ragas_context_recall_score",
    "Ragas Context Recall 점수 (0.0-1.0) - 검색 포괄성",
    ["rag_system", "method"],
)

# G-Eval RAG Quality Metrics (2025-11-08)
geval_correctness_score = Gauge(
    "afo_geval_correctness_score",
    "G-Eval Correctness 점수 (0.0-1.0) - 응답 정확도",
    ["rag_system", "method"],
)

geval_coherence_score = Gauge(
    "afo_geval_coherence_score",
    "G-Eval Coherence 점수 (0.0-1.0) - 응답 일관성",
    ["rag_system", "method"],
)

geval_consistency_score = Gauge(
    "afo_geval_consistency_score",
    "G-Eval Consistency 점수 (0.0-1.0) - 응답 논리성",
    ["rag_system", "method"],
)

geval_relevance_score = Gauge(
    "afo_geval_relevance_score",
    "G-Eval Relevance 점수 (0.0-1.0) - 응답 관련성",
    ["rag_system", "method"],
)

geval_self_consistency_score = Gauge(
    "afo_geval_self_consistency_score",
    "G-Eval Self-Consistency 점수 (0.0-1.0) - 일관성 검사",
    ["rag_system"],
)

# DeepEval RAG Quality Metrics (2025-11-08)
deepeval_faithfulness_score = Gauge(
    "afo_deepeval_faithfulness_score",
    "DeepEval Faithfulness 점수 (0.0-1.0) - 응답 사실성",
    ["rag_system", "method"],
)

deepeval_relevancy_score = Gauge(
    "afo_deepeval_relevancy_score",
    "DeepEval Relevancy 점수 (0.0-1.0) - 응답 관련성",
    ["rag_system", "method"],
)

deepeval_context_precision_score = Gauge(
    "afo_deepeval_context_precision_score",
    "DeepEval Context Precision 점수 (0.0-1.0) - 검색 정확도",
    ["rag_system", "method"],
)

deepeval_context_recall_score = Gauge(
    "afo_deepeval_context_recall_score",
    "DeepEval Context Recall 점수 (0.0-1.0) - 검색 포괄성",
    ["rag_system", "method"],
)

# ============================================================
# Redis 캐시 메트릭
# ============================================================

redis_cache_hits = Counter("afo_redis_cache_hits_total", "Redis 캐시 히트 횟수")
redis_cache_misses = Counter("afo_redis_cache_misses_total", "Redis 캐시 미스 횟수")

# ============================================================
# Phase 8.2.3: Prompt Caching Metrics
# ============================================================

# Prompt Cache Hit Rate (캐시 히트율)
prompt_cache_hit_rate = Gauge(
    "afo_prompt_cache_hit_rate",
    "Prompt Caching 히트율 (0.0-1.0) - Target: 60%+",
    ["provider"],  # 'openai' or 'claude'
)

# Prompt Cache Total Requests
prompt_cache_total_requests = Counter(
    "afo_prompt_cache_total_requests", "Prompt Caching 총 요청 수", ["provider"]
)

# Prompt Cache Cached Requests
prompt_cache_cached_requests = Counter(
    "afo_prompt_cache_cached_requests", "Prompt Caching 캐시된 요청 수", ["provider"]
)

# Prompt Cache Estimated Savings (USD)
prompt_cache_estimated_savings = Gauge(
    "afo_prompt_cache_estimated_savings_usd",
    "Prompt Caching 예상 절감 비용 (USD)",
    ["provider"],
)

# ============================================================
# Messaging Metrics (Kakao/Discord)
# ============================================================

messaging_requests_total = Counter(
    "afo_messaging_requests_total",
    "Total messaging requests",
    ["channel"],
)

messaging_errors_total = Counter(
    "afo_messaging_errors_total",
    "Total messaging errors",
    ["channel"],
)

messaging_response_seconds = Histogram(
    "afo_messaging_response_seconds",
    "Messaging response time in seconds",
    ["channel"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ============================================================
# Truth Loop Metrics
# ============================================================

# 1단계: 선확인 (先確認) - 마찰 탐지
truth_scan_total = Counter(
    "truth_loop_scan_total",
    "眞 루프 선확인 실행 횟수",
    ["status"],  # success, failure
)

truth_scan_failures = Gauge("truth_loop_scan_failures", "眞 루프 선확인 실패율 (%)")

# 2단계: 증명 (證明) - 오류 원인 분석
truth_prove_diversity = Gauge("truth_loop_prove_diversity", "眞 루프 증명 다양성 점수 (%)")
truth_prove_certainty = Gauge("truth_loop_prove_certainty", "眞 루프 증명 확실성 점수 (%)")

# 3단계: 정확성 (正確性) - 최종 眞 계산
truth_accuracy_score = Gauge("truth_loop_accuracy_score", "眞 루프 정확성 최종 점수 (%)")

# 4단계: 테스트 결과 - 순환 완료
truth_loop_duration = Histogram(
    "truth_loop_duration_seconds",
    "眞 루프 순환 소요 시간 (초)",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
)


# Phase 8.1.3: Trinity 점수 업데이트 헬퍼 함수
def update_trinity_scores(truth: float, goodness: float, beauty: float) -> float:
    """Trinity 점수를 업데이트하고 Balance Delta를 자동 계산

    Args:
        truth: 眞 (Truth) 점수 (0.0-1.0)
        goodness: 善 (Goodness) 점수 (0.0-1.0)
        beauty: 美 (Beauty) 점수 (0.0-1.0)

    """
    # Default labels for global score
    labels = {"service": "soul_engine", "component": "core"}

    trinity_truth_score.labels(**labels).set(truth)
    trinity_goodness_score.labels(**labels).set(goodness)
    trinity_beauty_score.labels(**labels).set(beauty)

    # Balance Delta 계산 (Phase 8.1.3)
    delta = max(truth, goodness, beauty) - min(truth, goodness, beauty)
    trinity_balance_delta.labels(**labels).set(delta)

    # 균형 법칙 위반 경고 (SSOT: trinity_ssot.py)
    if delta > THRESHOLD_BALANCE_WARNING:
        print(f"⚠️  Trinity 불균형 감지! Delta={delta:.3f} (Max-Min > {THRESHOLD_BALANCE_WARNING})")
        print(f"   眞={truth:.3f}, 善={goodness:.3f}, 美={beauty:.3f}")
        trinity_balance_status.labels(**labels, status="imbalanced").set(1)
    else:
        trinity_balance_status.labels(**labels, status="balanced").set(1)

    return delta


# Phase 8.1.3: VibeCoding 준수율 헬퍼 함수
def update_vibecoding_compliance() -> float:
    """VibeCoding 준수율을 DRY_RUN/WET 비율로 자동 계산

    원칙: DRY_RUN 없이 WET 실행 금지 (선확인, 후보고)
    준수율 = DRY_RUN / (DRY_RUN + WET_without_DRY)

    Returns:
        float: 준수율 (0.0-1.0)

    """
    # REGISTRY는 이미 상단에서 import됨

    # Counter 값 가져오기
    dry_run_count = 0
    wet_count = 0

    for metric in REGISTRY.collect():
        if metric.name == "afo_dry_run_executions_total":
            for sample in metric.samples:
                dry_run_count = int(sample.value)
        elif metric.name == "afo_wet_executions_total":
            for sample in metric.samples:
                wet_count = int(sample.value)

    # 준수율 계산 (최소 1회는 실행되었다고 가정)
    total = max(dry_run_count + wet_count, 1)
    compliance_rate = dry_run_count / total if total > 0 else 1.0

    # 메트릭 업데이트
    vibecoding_compliance.labels(principle="선확인_후보고").set(compliance_rate)

    # 목표: 100% (모든 WET은 DRY_RUN 후에 실행)
    if compliance_rate < 1.0 and (dry_run_count + wet_count) > 0:
        print(
            f"⚠️  VibeCoding 위반 감지! DRY_RUN={int(dry_run_count)}, WET={int(wet_count)}, "
            f"준수율={compliance_rate * 100:.1f}%"
        )

    return compliance_rate


# 초기값 설정 (서버 시작 시 0 또는 기본값으로 초기화)
# Default labels for initialization
init_labels = {"service": "soul_engine", "component": "core"}


def _initialize_metrics() -> None:
    """메트릭 초기화 (레지스트리 충돌 시 graceful 처리)"""
    try:
        trinity_truth_score.labels(**init_labels).set(0.95)
        trinity_goodness_score.labels(**init_labels).set(0.92)
        trinity_beauty_score.labels(**init_labels).set(0.88)
        trinity_filial_serenity_score.labels(**init_labels).set(1.0)
        trinity_serenity_core.labels(**init_labels).set(0.91)  # ∛(0.95*0.92*0.88) ≈ 0.916
        trinity_score.labels(**init_labels).set(0.93)  # (0.95+0.92+0.88+1.0)/4 = 0.9375
        trinity_balance_delta.labels(**init_labels).set(
            max(0.95, 0.92, 0.88) - min(0.95, 0.92, 0.88)
        )
        trinity_balance_status.labels(**init_labels, status="balanced").set(1)

        # Initialize counters
        trinity_analysis_total.inc(0)
        trinity_calculations_total.labels(**init_labels, balance_status="balanced").inc(0)

        prompt_cache_hit_rate.labels(provider="openai").set(0.0)
        prompt_cache_hit_rate.labels(provider="anthropic").set(0.0)
        prompt_cache_estimated_savings.labels(provider="openai").set(0.0)
        prompt_cache_estimated_savings.labels(provider="anthropic").set(0.0)

        redis_cache_hits.inc(0)
        redis_cache_misses.inc(0)
        health_total_score.set(100.0)
        health_healthy_organs.set(11.0)
        health_percentage.set(100.0)
        health_organ_status.labels(organ_name="all", organ_korean="전체").set(1.0)
        vibecoding_compliance.labels(principle="all").set(1.0)

        trinity_strategist_score.labels(
            strategist="제갈량", aspect="眞", weight=str(TrinityWeights.TRUTH)
        ).set(0.95)
        trinity_strategist_score.labels(
            strategist="사마의", aspect="善", weight=str(TrinityWeights.GOODNESS)
        ).set(0.92)
        trinity_strategist_score.labels(
            strategist="주유", aspect="美", weight=str(TrinityWeights.BEAUTY)
        ).set(0.88)
    except ValueError:
        # Prometheus registry conflict (stale metrics with different labels)
        # This can happen during hot-reload or test isolation issues
        pass


_initialize_metrics()
