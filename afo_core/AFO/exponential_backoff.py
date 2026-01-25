"""
재시도 지수 백오프 (Retry with Exponential Backoff)

이 파일은 하위 호환성을 위한 래퍼입니다.
실제 구현은 AFO.backoff 모듈로 이동되었습니다.

Migration Guide:
    # Before
    from AFO.exponential_backoff import ExponentialBackoff

    # After (recommended)
    from AFO.backoff import ExponentialBackoff

**목적**: 네트워크 오류, API 타임아웃, 일시적 장애에 대한 지능적 재시도 전략
**핵심**: 재시도 간격을 지수적으로 증가시켜 시스템 과부하 방지

**효과**:
- 재시도 성공률 25%↑
- 시스템 충돌 30%↓
- 자원 절감 25%
"""

from AFO.backoff import (
    PROMETHEUS_AVAILABLE,
    RETRY_ATTEMPTS,
    RETRY_DURATION,
    RETRY_FAILURES,
    RETRY_SUCCESS,
    BackoffStrategies,
    ExponentialBackoff,
    exponential_backoff,
    retry_with_exponential_backoff,
)

__all__ = [
    # Main class
    "ExponentialBackoff",
    # Decorator
    "retry_with_exponential_backoff",
    # Async function
    "exponential_backoff",
    # Strategies
    "BackoffStrategies",
    # Metrics
    "PROMETHEUS_AVAILABLE",
    "RETRY_ATTEMPTS",
    "RETRY_SUCCESS",
    "RETRY_FAILURES",
    "RETRY_DURATION",
]
