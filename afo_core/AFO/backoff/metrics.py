"""
Exponential Backoff Metrics - Prometheus 메트릭 헬퍼

재시도 관련 Prometheus 메트릭을 관리합니다.
"""

from typing import cast

from prometheus_client import REGISTRY, Counter, Histogram

# Prometheus 메트릭 연동 (옵션)
try:
    PROMETHEUS_AVAILABLE = True

    # 재시도 메트릭 (중복 등록 방지)
    def _get_or_create_counter(name: str, description: str, labels: list[str]) -> Counter | None:
        """Counter를 가져오거나 생성 (중복 등록 방지)"""
        try:
            # 이미 등록된 메트릭이 있는지 확인
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, "_name") and collector._name == name:
                    return cast("Counter", collector)
            # 없으면 새로 생성
            return Counter(name, description, labels)
        except ValueError:
            # 중복 등록 에러 발생 시 기존 메트릭 반환
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, "_name") and collector._name == name:
                    return cast("Counter", collector)
            # 그래도 없으면 None 반환 (메트릭 비활성화)
            return None

    def _get_or_create_histogram(
        name: str, description: str, labels: list[str]
    ) -> Histogram | None:
        """Histogram을 가져오거나 생성 (중복 등록 방지)"""
        try:
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, "_name") and collector._name == name:
                    return cast("Histogram", collector)
            return Histogram(name, description, labels)
        except ValueError:
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, "_name") and collector._name == name:
                    return cast("Histogram", collector)
            return None

    # 재시도 메트릭 (lazy initialization)
    RETRY_ATTEMPTS = _get_or_create_counter(
        "exponential_backoff_retry_attempts_total",
        "Total number of retry attempts",
        ["function_name"],
    )
    RETRY_SUCCESS = _get_or_create_counter(
        "exponential_backoff_retry_success_total",
        "Total number of successful retries",
        ["function_name"],
    )
    RETRY_FAILURES = _get_or_create_counter(
        "exponential_backoff_retry_failures_total",
        "Total number of failed retries",
        ["function_name", "exception_type"],
    )
    RETRY_DURATION = _get_or_create_histogram(
        "exponential_backoff_retry_duration_seconds",
        "Duration of retry operations",
        ["function_name"],
    )
except ImportError:
    PROMETHEUS_AVAILABLE = False
    RETRY_ATTEMPTS = None
    RETRY_SUCCESS = None
    RETRY_FAILURES = None
    RETRY_DURATION = None
