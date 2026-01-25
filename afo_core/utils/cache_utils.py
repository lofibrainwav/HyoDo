from __future__ import annotations

import json
import logging
from functools import wraps
from typing import TYPE_CHECKING, Any

import redis

if TYPE_CHECKING:
    from collections.abc import Callable

    from redis import Redis

# Trinity Score: 90.0 (Established by Chancellor)
# Redis 캐시 유틸리티


# 로깅 설정
logger = logging.getLogger(__name__)


class CacheManager:
    """Redis 기반 캐시 관리자"""

    def __init__(self) -> None:
        self.redis: Redis | None = None
        self.enabled: bool = False
        # Phase 35-1: 하드코딩 제거 - settings 함수 사용
        from ..settings import get_settings

        settings = get_settings()

        # 환경별 Redis 초기화 전략 (Phase 35-1: 환경 적응성 강화)
        environment = settings.environment

        try:
            # settings 객체에서 Redis URL 가져오기
            redis_url = settings.get_redis_url()

            # 테스트 환경에서는 Redis 연결을 시도하지 않음 (graceful degradation)
            if environment == "test":
                logger.info("테스트 환경: Redis 연결 생략 (캐시 비활성화)")
                self.redis = None
                self.enabled = False
                return

            if settings.REDIS_PASSWORD:
                # 비밀번호가 있는 경우 URL에 포함
                import urllib.parse

                parsed = urllib.parse.urlparse(redis_url)
                redis_url = redis_url.replace(
                    f"{parsed.hostname}:{parsed.port}",
                    f":{settings.REDIS_PASSWORD}@{parsed.hostname}:{parsed.port}",
                )

            self.redis = redis.from_url(
                redis_url,
                socket_timeout=settings.REDIS_TIMEOUT,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,
                retry_on_timeout=True,
            )
            if self.redis is not None:
                self.redis.ping()  # 연결 테스트
            self.enabled = True
        except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
            logger.warning("Redis 연결 실패 (settings 기반): %s", str(e))
            logger.info(
                "Redis 연결 실패로 캐시 기능이 비활성화됩니다. 메모리 기반 캐시로 대체 가능합니다."
            )
            self.redis = None
            self.enabled = False
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.warning("Redis 초기화 중 예상치 못한 에러: %s", str(e))
            self.redis = None
            self.enabled = False

    def get(self, key: str) -> Any | None:
        """캐시에서 데이터 가져오기"""
        if not self.enabled or self.redis is None:
            return None
        try:
            data = self.redis.get(key)
            if data and isinstance(data, (str, bytes, bytearray)):
                return json.loads(data)
            return None
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("캐시 데이터 JSON 파싱 실패 (키: %s): %s", key, str(e))
            return None
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning("Redis 연결 에러 (키: %s): %s", key, str(e))
            return None
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.warning("캐시 조회 중 예상치 못한 에러 (키: %s): %s", key, str(e))
            return None

    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """캐시에 데이터 저장"""
        if not self.enabled or self.redis is None:
            return False
        try:
            json_str = json.dumps(value)
            self.redis.setex(key, expire, json_str)
            return True
        except (TypeError, ValueError) as e:
            logger.warning("캐시 데이터 JSON 직렬화 실패 (키: %s): %s", key, str(e))
            return False
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning("Redis 연결 에러 (키: %s): %s", key, str(e))
            return False
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.warning("캐시 저장 중 예상치 못한 에러 (키: %s): %s", key, str(e))
            return False

    def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        if not self.enabled or self.redis is None:
            return False
        try:
            return bool(self.redis.delete(key))
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning("Redis 연결 에러 (키: %s): %s", key, str(e))
            return False
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("캐시 삭제 중 예상치 못한 에러 (키: %s): %s", key, str(e))
            return False


# 글로벌 캐시 인스턴스
cache = CacheManager()


def cached(expire: int = 300) -> Callable[[Callable], Callable]:
    """API 엔드포인트 캐싱 데코레이터"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 캐시 키 생성
            key = f"{func.__name__}:{str(args) + str(kwargs)}"

            # 캐시에서 먼저 확인
            cached_data = cache.get(key)
            if cached_data is not None:
                return cached_data

            # 실제 함수 실행
            result = await func(*args, **kwargs)

            # 결과 캐싱
            cache.set(key, result, expire)

            return result

        return wrapper

    return decorator
