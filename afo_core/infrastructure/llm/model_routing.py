from __future__ import annotations

import logging
import re
from typing import Any

# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO Model Routing - Task-Type Based Model Selection

작업 유형에 따른 최적 모델 선택 시스템 (M4 Pro 24GB 최적화)
- 기본 대화/이미지: qwen3-vl (화타) [Ollama - Vision 전용]
- 코딩: Qwen2.5-Coder-32B (사마휘) [MLX - 네이티브 2배 빠름]
- 추론: DeepSeek-R1-14B (좌자) [MLX - 네이티브 2배 빠름]

MLX 우선 정책: Apple Silicon 통합 메모리 활용으로 최고 성능
"""

# Import core config from model_config (SSOT)
from .model_config import ModelConfig, TaskType

# Import scholar utilities (extracted to reduce file size)
from .scholar_utils import (
    AutoOptimizationEngine,
    ScholarCollaboration,
    ScholarMetrics,
    auto_optimizer,
    scholar_collaboration,
    scholar_metrics,
)

__all__ = [
    "TaskType",
    "ModelConfig",
    "TASK_PATTERNS",
    "classify_task",
    "get_model_for_task",
    "get_routing_info",
    "get_advanced_routing_info",
    "get_model_with_escalation",
    "should_escalate",
    "get_escalation_model",
    "get_vision_model",
    "scholar_collaboration",
    "scholar_metrics",
    "auto_optimizer",
    # Re-export classes for backward compatibility
    "ScholarCollaboration",
    "ScholarMetrics",
    "AutoOptimizationEngine",
]

logger = logging.getLogger(__name__)


# 키워드 패턴 정의 (정규식)
# OPTIMIZATION: 화타 Beauty Score 개선을 위한 UX 패턴 (간소화)
TASK_PATTERNS: dict[TaskType, list[str]] = {
    TaskType.CHAT: [
        # 대화/감성 표현 (핵심)
        r"어떻게.*(?:생각|하면|할까)",
        r"(?:조언|의견|추천|제안|아이디어)",
        r"(?:느낌|감정|마음)",
        # UX/디자인 (핵심)
        r"(?:UX|UI|사용자.*경험|인터페이스)",
        r"(?:디자인|스타일|테마|컬러|폰트|레이아웃)",
        r"(?:사용성|편리|직관|깔끔|예쁘|아름답)",
        # 감성적 표현 (통합)
        r"(?:좋아|싫어|마음에.*들)",
        r"(?:부탁|도와줘|감사|고마워|미안|죄송)",
        r"(?:축하|기념|이벤트|파티|여행|휴가)",
        # 감정/심리 (통합)
        r"(?:힐링|휴식|스트레스|피로|힘들)",
        r"(?:성공|실패|노력|희망|꿈|목표)",
        r"(?:사랑|우정|가족|친구|관계|소통)",
        # 마음 관련 (통합 패턴)
        r"마음.*(?:표현|전달|이해|공감|치유|안정|행복)",
        r"감정.*(?:표현|전달|공유|이해|공감|인식|관리)",
        # UX 전문 패턴 (통합)
        r"사용자.*(?:경험|만족|심리|맥락|맞춤|개인화)",
        r"(?:접근성|포용성|감성.*지능|인지.*부하)",
    ],
    TaskType.VISION: [
        r"(?:image|이미지|사진|그림|vision)",
        r"(?:screenshot|스크린샷|화면)",
        r"(?:보여|봐봐)",
    ],
    TaskType.CODE_GENERATE: [
        r"코드.*(?:작성|생성|만들|짜|짤)",
        r"(?:implement|구현|write.*code)",
        r"(?:함수|클래스|컴포넌트).*(?:만들|생성|정의|구현)",
        r"(?:def|class|import)\s+\w+",
        r"(?:알고리즘|프로그래밍|코딩|개발)",
        r"(?:스크립트|프로그램|소스코드)",
        r"(?:모듈|라이브러리|패키지)",
        r"(?:API|백엔드|프론트엔드).*개발",
        r"(?:데이터베이스|SQL|쿼리)",
        r"(?:서버|클라이언트)",
        r"(?:웹|모바일|데스크톱).*앱",
        r"(?:AI|인공지능|머신러닝|딥러닝)",
        r"(?:테스트|자동화|빌드|배포|CI/CD)",
        r"(?:도커|쿠버네티스|클라우드|AWS|Azure|GCP)",
    ],
    TaskType.CODE_REVIEW: [
        r"코드.*(?:리뷰|분석|검토|확인|봐)",
        r"(?:review|refactor|리팩터)",
        r"(?:debug|디버그|버그.*찾|오류.*확인)",
    ],
    TaskType.REASONING: [
        r"(?:단계.*분석|step.*by.*step)",
        r"(?:깊이.*생각|추론|reasoning)",
        r"(?:왜.*(?:그런|이런)|논리|분석.*해)",
        r"(?:think.*through|복잡.*문제)",
    ],
    TaskType.EMBED: [
        r"(?:embed|임베딩|벡터|vector)",
        r"(?:similarity|유사도)",
    ],
    TaskType.DOCUMENT: [
        r"(?:문서화|document|docstring)",
        r"(?:주석|comment|readme)",
        r"설명.*작성",
    ],
}

# 컴파일된 패턴 캐시
_COMPILED_PATTERNS: dict[TaskType, list[re.Pattern[str]]] = {}


def _get_compiled_patterns() -> dict[TaskType, list[re.Pattern[str]]]:
    """정규식 패턴 컴파일 (캐시)"""
    global _COMPILED_PATTERNS
    if not _COMPILED_PATTERNS:
        for task_type, patterns in TASK_PATTERNS.items():
            _COMPILED_PATTERNS[task_type] = [re.compile(p, re.IGNORECASE) for p in patterns]
    return _COMPILED_PATTERNS


def classify_task(query: str, context: dict[str, Any] | None = None) -> TaskType:
    """
    쿼리를 분석하여 작업 유형 분류

    Args:
        query: 사용자 쿼리
        context: 추가 컨텍스트 (이미지 포함 여부 등)

    Returns:
        분류된 TaskType
    """
    ctx = context or {}

    # 1. 컨텍스트에 이미지가 있으면 VISION
    if ctx.get("has_image") or ctx.get("image_url") or ctx.get("images"):
        logger.debug("🖼️ Task classified as VISION (image context detected)")
        return TaskType.VISION

    # 2. 명시적 task_type 지정
    if explicit_type := ctx.get("task_type"):
        try:
            task = TaskType(explicit_type)
            logger.debug(f"📋 Task explicitly set: {task.value}")
            return task
        except ValueError:
            pass

    # 3. 패턴 매칭
    compiled = _get_compiled_patterns()
    query_lower = query.lower()

    # 우선순위: VISION > CODE > REASONING > DOCUMENT > EMBED > CHAT
    priority_order = [
        TaskType.VISION,
        TaskType.CODE_GENERATE,
        TaskType.CODE_REVIEW,
        TaskType.REASONING,
        TaskType.DOCUMENT,
        TaskType.EMBED,
    ]

    for task_type in priority_order:
        patterns = compiled.get(task_type, [])
        for pattern in patterns:
            if pattern.search(query_lower):
                logger.debug(f"🎯 Task classified as {task_type.value} (pattern match)")
                return task_type

    # 4. 기본값: CHAT
    logger.debug("💬 Task classified as CHAT (default)")
    return TaskType.CHAT


def get_model_for_task(task_type: TaskType) -> str:
    """
    작업 유형에 맞는 모델 반환

    Args:
        task_type: 작업 유형

    Returns:
        Ollama 모델 ID
    """
    model = ModelConfig.TASK_MODEL_MAP.get(task_type, ModelConfig.HEO_JUN)
    scholar = ModelConfig.TASK_SCHOLAR_MAP.get(task_type, "Unknown")
    logger.info(f"🧑‍🎓 Selected scholar: {scholar} → model: {model}")
    return model


def get_routing_info(query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    라우팅 정보 종합 반환

    Args:
        query: 사용자 쿼리
        context: 추가 컨텍스트

    Returns:
        {task_type, model, scholar, reasoning}
    """
    task_type = classify_task(query, context)
    model = get_model_for_task(task_type)
    scholar = ModelConfig.TASK_SCHOLAR_MAP.get(task_type, "Unknown")

    return {
        "task_type": task_type.value,
        "model": model,
        "scholar": scholar,
        "reasoning": f"Query classified as '{task_type.value}' → {scholar}",
    }


# ============================================================================
# Escalation Pattern (Bottom-Up LLM 오케스트레이션)
# ============================================================================

# OPTIMIZATION: Task-specific escalation thresholds (Trinity Score 최적화)
# Higher threshold = stricter quality requirement for that task type
# Lower threshold = more lenient (task is simpler or model is already optimal)
# 화타 Beauty Score 개선을 위한 CHAT 임계값 상향 조정
TASK_THRESHOLD_MAP: dict[TaskType, float] = {
    TaskType.CHAT: 92.0,  # Beauty Score 개선: 더 높은 품질 요구 (was 88.0)
    TaskType.VISION: 90.0,  # Vision tasks need precision
    TaskType.CODE_GENERATE: 90.0,  # 사마휘 품질 개선: 좌자 에스컬레이션 임계값 조정 (was 92.0)
    TaskType.CODE_REVIEW: 0.0,  # Bypass - already uses top model
    TaskType.REASONING: 0.0,  # Bypass - already uses top model
    TaskType.EMBED: 0.0,  # Bypass - deterministic
    TaskType.DOCUMENT: 85.0,  # Documentation - more lenient
}

# Default threshold for unknown task types
DEFAULT_ESCALATION_THRESHOLD = 90.0

# Backward compatibility alias (deprecated - use get_escalation_threshold())
ESCALATION_THRESHOLD = DEFAULT_ESCALATION_THRESHOLD


def get_escalation_threshold(task_type: TaskType) -> float:
    """Get task-specific escalation threshold.

    OPTIMIZATION: Different task types have different quality requirements.
    Returns 0.0 for tasks that bypass escalation (already on top models).
    """
    return TASK_THRESHOLD_MAP.get(task_type, DEFAULT_ESCALATION_THRESHOLD)


def should_escalate(trinity_score: float, task_type: TaskType) -> bool:
    """
    Trinity Score 기반 에스컬레이션 필요 여부 판단

    OPTIMIZATION: Task-specific thresholds for better routing.
    - CHAT: 88.0 (more lenient)
    - CODE_GENERATE: 92.0 (stricter)
    - DOCUMENT: 85.0 (documentation is lenient)

    Args:
        trinity_score: Trinity Score (0-100)
        task_type: 작업 유형

    Returns:
        True if escalation needed
    """
    # Get task-specific threshold
    threshold = get_escalation_threshold(task_type)

    # Threshold 0.0 means bypass (already using optimal model)
    if threshold == 0.0:
        return False

    # Trinity Score 기반 판단
    if trinity_score < threshold:
        logger.info(
            f"⚡ Escalation triggered: Trinity Score {trinity_score:.1f} < {threshold} ({task_type.value})"
        )
        return True

    return False


def get_escalation_model(task_type: TaskType) -> str:
    """
    에스컬레이션 시 사용할 정밀 모델 반환

    Args:
        task_type: 작업 유형

    Returns:
        에스컬레이션 모델 ID
    """
    model = ModelConfig.ESCALATION_MODEL_MAP.get(task_type, ModelConfig.HEO_JUN)
    logger.info(f"📈 Escalation model selected: {model} for {task_type.value}")
    return model


def get_model_with_escalation(
    task_type: TaskType,
    trinity_score: float | None = None,
) -> tuple[str, bool]:
    """
    에스컬레이션을 고려한 모델 선택

    Bottom-Up 전략:
    1. 기본 모델(빠름)로 시작
    2. Trinity Score 확인
    3. 필요시 정밀 모델로 에스컬레이션

    Args:
        task_type: 작업 유형
        trinity_score: Trinity Score (None이면 기본 모델 반환)

    Returns:
        (model_id, is_escalated)
    """
    base_model = ModelConfig.TASK_MODEL_MAP.get(task_type, ModelConfig.HEO_JUN_FAST)

    # Trinity Score 없으면 기본 모델 (빠른 응답)
    if trinity_score is None:
        return base_model, False

    # 에스컬레이션 필요 여부 판단
    if should_escalate(trinity_score, task_type):
        escalation_model = get_escalation_model(task_type)
        return escalation_model, True

    return base_model, False


# ============================================================================
# Vision 2단계 선택 (Trinity Score 기반)
# ============================================================================


def get_vision_model(trinity_score: float | None = None) -> tuple[str, str]:
    """
    Vision 작업용 모델 선택 (2단계 Bottom-Up)

    전략:
    - 1단계: qwen3-vl:2b (12초, 빠른 초안) - 62% 케이스 커버
    - 2단계: qwen3-vl:latest (정밀 검증) - Trinity < 90일 때

    Args:
        trinity_score: Trinity Score (None이면 1단계 모델)

    Returns:
        (model_id, stage_description)
    """
    if trinity_score is None:
        logger.info("🖼️ Vision Stage 1: Fast model (qwen3-vl:2b)")
        return ModelConfig.HEO_JUN_FAST, "Stage 1 (Fast)"

    vision_threshold = get_escalation_threshold(TaskType.VISION)
    if trinity_score >= vision_threshold:
        logger.info(f"🖼️ Vision complete: Trinity {trinity_score:.1f} ≥ {vision_threshold}")
        return ModelConfig.HEO_JUN_FAST, "Stage 1 (Sufficient)"

    logger.info(
        f"🖼️ Vision Stage 2: Precise model needed (Trinity {trinity_score:.1f} < {vision_threshold})"
    )
    return ModelConfig.HEO_JUN, "Stage 2 (Precise)"


def get_advanced_routing_info(
    query: str,
    context: dict[str, Any] | None = None,
    trinity_score: float | None = None,
) -> dict[str, Any]:
    """
    고급 라우팅 정보 (에스컬레이션 포함)

    Args:
        query: 사용자 쿼리
        context: 추가 컨텍스트
        trinity_score: Trinity Score (에스컬레이션 판단용)

    Returns:
        확장된 라우팅 정보
    """
    task_type = classify_task(query, context)

    # Vision 특별 처리
    if task_type == TaskType.VISION:
        model, stage = get_vision_model(trinity_score)
        is_escalated = stage == "Stage 2 (Precise)"
    else:
        model, is_escalated = get_model_with_escalation(task_type, trinity_score)
        stage = "Escalated" if is_escalated else "Default"

    scholar = ModelConfig.TASK_SCHOLAR_MAP.get(task_type, "Unknown")

    return {
        "task_type": task_type.value,
        "model": model,
        "scholar": scholar,
        "stage": stage,
        "is_escalated": is_escalated,
        "trinity_score": trinity_score,
        "reasoning": f"Query '{task_type.value}' → {model} ({stage})",
    }


# ============================================================================
# Monitoring Functions (using imported scholar_metrics)
# ============================================================================


def get_routing_info_with_monitoring(
    query: str, context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    모니터링이 포함된 라우팅 정보 반환

    Args:
        query: 사용자 쿼리
        context: 추가 컨텍스트

    Returns:
        라우팅 정보 + 모니터링 데이터
    """
    import time

    start_time = time.time()

    # 기존 라우팅 로직
    routing_info = get_routing_info(query, context)

    # 모니터링 기록 (기본 메트릭)
    end_time = time.time()
    response_time = end_time - start_time

    # 간단한 응답 길이 기반 품질 추정 (임시)
    estimated_quality = min(100.0, len(query) * 0.5)  # 쿼리 길이에 기반한 추정

    scholar_metrics.record_response(
        scholar=routing_info["scholar"],
        response_time=response_time,
        response_length=len(query),  # 쿼리 길이로 임시 사용
        quality_score=estimated_quality,
    )

    # 모니터링 정보 추가
    routing_info["monitoring"] = {
        "response_time": response_time,
        "estimated_quality": estimated_quality,
        "performance_report": scholar_metrics.get_performance_report(routing_info["scholar"]),
    }

    return routing_info


def get_scholar_performance_report() -> dict[str, Any]:
    """학자 성능 모니터링 리포트"""
    return {
        "timestamp": "2026-01-22T00:23:00Z",
        "monitoring_active": True,
        "scholars": scholar_metrics.get_all_scholars_report(),
        "summary": {
            "total_tasks": sum(scholar_metrics.task_counts.values()),
            "total_errors": sum(scholar_metrics.error_counts.values()),
            "error_rate": sum(scholar_metrics.error_counts.values())
            / max(sum(scholar_metrics.task_counts.values()), 1),
        },
    }


# ============================================================================
# Dynamic Escalation Optimization (동적 임계값 조정)
# ============================================================================


def optimize_escalation_thresholds(current_trinity_score: float) -> dict[TaskType, float]:
    """
    Trinity Score 기반 동적 임계값 최적화

    Args:
        current_trinity_score: 현재 Trinity Score

    Returns:
        최적화된 임계값 맵
    """
    # 기본 임계값
    base_thresholds = TASK_THRESHOLD_MAP.copy()

    # Trinity Score 기반 동적 조정
    if current_trinity_score >= 90.0:
        # 고품질 상태: 임계값 낮춰서 더 많은 작업에 정밀 모델 사용
        adjustment = -2.0  # 임계값 2점 낮춤
    elif current_trinity_score >= 75.0:
        # 중간 상태: 기본 임계값 유지
        adjustment = 0.0
    else:
        # 저품질 상태: 임계값 높여서 정밀 모델 사용 제한
        adjustment = +3.0  # 임계값 3점 높임

    # Beauty Score 개선을 위한 화타 특화 조정
    optimized_thresholds = {}
    for task_type, threshold in base_thresholds.items():
        if threshold == 0.0:
            # 이미 최적 모델인 경우 변경하지 않음
            optimized_thresholds[task_type] = threshold
        else:
            new_threshold = threshold + adjustment

            # 화타 CHAT 작업 특별 최적화
            if task_type == TaskType.CHAT:
                if current_trinity_score < 75.0:
                    # Beauty Score 낮을 때 더 엄격하게
                    new_threshold = min(95.0, new_threshold + 2.0)
                else:
                    # Beauty Score 높을 때 더 관대하게
                    new_threshold = max(85.0, new_threshold - 1.0)

            # 범위 제한 (70-95)
            optimized_thresholds[task_type] = max(70.0, min(95.0, new_threshold))

    return optimized_thresholds


def get_dynamic_escalation_threshold(
    task_type: TaskType, current_trinity_score: float | None = None
) -> float:
    """
    동적 에스컬레이션 임계값 계산

    Args:
        task_type: 작업 유형
        current_trinity_score: 현재 Trinity Score

    Returns:
        최적화된 임계값
    """
    if current_trinity_score is None:
        return get_escalation_threshold(task_type)

    optimized_thresholds = optimize_escalation_thresholds(current_trinity_score)
    return optimized_thresholds.get(task_type, get_escalation_threshold(task_type))


def should_escalate_dynamic(
    trinity_score: float, task_type: TaskType, current_overall_score: float | None = None
) -> bool:
    """
    동적 임계값 기반 에스컬레이션 판단

    Args:
        trinity_score: 작업별 Trinity Score
        task_type: 작업 유형
        current_overall_score: 현재 전체 Trinity Score

    Returns:
        에스컬레이션 필요 여부
    """
    dynamic_threshold = get_dynamic_escalation_threshold(task_type, current_overall_score)

    if dynamic_threshold == 0.0:
        return False

    if trinity_score < dynamic_threshold:
        logger.info(
            f"🎯 Dynamic escalation: {trinity_score:.1f} < {dynamic_threshold:.1f} ({task_type.value})"
        )
        return True

    return False


# ============================================================================
# Auto-Optimization Functions (auto_optimizer imported from scholar_utils)
# ============================================================================


def get_auto_optimized_routing(
    query: str,
    context: dict[str, Any] | None = None,
    trinity_score: float | None = None,
    task_complexity: str = "medium",
) -> dict[str, Any]:
    """
    자동 최적화된 라우팅 정보 반환

    Args:
        query: 사용자 쿼리
        context: 추가 컨텍스트
        trinity_score: 현재 Trinity Score
        task_complexity: 작업 복잡도 (simple, medium, complex)

    Returns:
        자동 최적화된 라우팅 정보
    """
    # 기본 라우팅
    routing_info = get_routing_info(query, context)

    # 자동 최적화 적용
    scholar = routing_info["scholar"]
    task_type = routing_info["task_type"]

    optimization = auto_optimizer.predict_optimal_strategy(
        scholar=scholar,
        task_type=task_type,
        current_trinity=trinity_score or 85.0,
        task_complexity=task_complexity,
    )

    # 최적화된 모델 선택
    task_enum = TaskType(task_type)
    base_model = ModelConfig.TASK_MODEL_MAP.get(task_enum, ModelConfig.HEO_JUN)

    if optimization["should_escalate"]:
        final_model = get_escalation_model(task_enum)
        stage = "Auto-Escalated"
    else:
        final_model = base_model
        stage = "Auto-Optimized"

    # 결과 업데이트
    routing_info["model"] = final_model
    routing_info["stage"] = stage
    routing_info["optimization"] = optimization
    routing_info["reasoning"] = f"Auto-optimized: {optimization['reasoning']}"

    return routing_info


def get_auto_optimization_report() -> dict[str, Any]:
    """자동 최적화 시스템 리포트"""
    return {
        "timestamp": "2026-01-22T00:32:00Z",
        "system_active": True,
        "insights": auto_optimizer.get_pattern_insights(),
        "learning_progress": auto_optimizer.get_pattern_insights()["learning_progress"],
        "recommendations": {
            "ready_for_production": len(
                [
                    k
                    for k, v in auto_optimizer.get_pattern_insights()["learning_progress"].items()
                    if v["ready_for_learning"]
                ]
            ),
            "needs_more_data": len(
                [
                    k
                    for k, v in auto_optimizer.get_pattern_insights()["learning_progress"].items()
                    if not v["ready_for_learning"]
                ]
            ),
        },
    }
