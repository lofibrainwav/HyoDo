"""
Backoff Strategies - 사전 정의된 재시도 전략

다양한 사용 사례에 맞는 백오프 전략 프리셋을 제공합니다.
"""

from .backoff import ExponentialBackoff


class BackoffStrategies:
    """
    사전 정의된 재시도 전략

    **사용 예제**:
    ```python
    # API 호출용 (빠른 재시도)
    api_backoff = BackoffStrategies.api()

    # 네트워크 연결용 (느린 재시도)
    network_backoff = BackoffStrategies.network()

    # 데이터베이스 연결용 (중간 속도)
    db_backoff = BackoffStrategies.database()
    ```
    """

    @staticmethod
    def api(
        max_retries: int = 5,
        retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    ) -> ExponentialBackoff:
        """
        API 호출용 백오프 (빠른 재시도)

        - 초기 지연: 0.5초
        - 지수 밑수: 2
        - 최대 지연: 30초
        - Jitter: 활성화
        """
        return ExponentialBackoff(
            max_retries=max_retries,
            base_delay=0.5,
            exponential_base=2.0,
            max_delay=30.0,
            jitter=True,
            retryable_exceptions=retryable_exceptions,
        )

    @staticmethod
    def network(
        max_retries: int = 10,
        retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    ) -> ExponentialBackoff:
        """
        네트워크 연결용 백오프 (느린 재시도)

        - 초기 지연: 2초
        - 지수 밑수: 2
        - 최대 지연: 120초
        - Jitter: 활성화
        """
        return ExponentialBackoff(
            max_retries=max_retries,
            base_delay=2.0,
            exponential_base=2.0,
            max_delay=120.0,
            jitter=True,
            retryable_exceptions=retryable_exceptions,
        )

    @staticmethod
    def database(
        max_retries: int = 7,
        retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    ) -> ExponentialBackoff:
        """
        데이터베이스 연결용 백오프 (중간 속도)

        - 초기 지연: 1초
        - 지수 밑수: 2
        - 최대 지연: 60초
        - Jitter: 활성화
        """
        return ExponentialBackoff(
            max_retries=max_retries,
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=True,
            retryable_exceptions=retryable_exceptions,
        )

    @staticmethod
    def aggressive(
        max_retries: int = 3,
        retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    ) -> ExponentialBackoff:
        """
        공격적 백오프 (매우 빠른 재시도)

        - 초기 지연: 0.1초
        - 지수 밑수: 1.5
        - 최대 지연: 5초
        - Jitter: 활성화

        **주의**: 서버 부하 증가 가능
        """
        return ExponentialBackoff(
            max_retries=max_retries,
            base_delay=0.1,
            exponential_base=1.5,
            max_delay=5.0,
            jitter=True,
            retryable_exceptions=retryable_exceptions,
        )

    @staticmethod
    def conservative(
        max_retries: int = 15,
        retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    ) -> ExponentialBackoff:
        """
        보수적 백오프 (매우 느린 재시도)

        - 초기 지연: 5초
        - 지수 밑수: 2
        - 최대 지연: 300초 (5분)
        - Jitter: 활성화

        **용도**: 외부 서비스 장애 시 장기 재시도
        """
        return ExponentialBackoff(
            max_retries=max_retries,
            base_delay=5.0,
            exponential_base=2.0,
            max_delay=300.0,
            jitter=True,
            retryable_exceptions=retryable_exceptions,
        )
