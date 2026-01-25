from __future__ import annotations

import logging
import traceback
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from collections.abc import Callable

# Trinity Score: 90.0 (Established by Chancellor)
"""Error Handling Utilities (야전교범 원칙 준수)
眞善美孝永 철학에 기반한 에러 핸들링 패턴

眞 (Truth): 정확한 에러 타입 및 메시지
善 (Goodness): 안전한 에러 처리 및 복구
美 (Beauty): 우아한 에러 메시지 및 로깅
孝 (Serenity): 개발자 경험 최적화
永 (Eternity): 재사용 가능한 에러 핸들링 패턴
"""


P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)


class AFOError(Exception):
    """AFO 왕국 기본 에러 클래스"""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        code: str | None = None,  # code는 error_code의 별칭 (하위 호환성)
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        # code 또는 error_code 중 하나라도 제공되면 사용
        self.error_code = error_code or code
        self.details = details or {}


class TruthError(AFOError):
    """眞 (Truth) 에러 - 기술적 정확성 관련"""

    pass


class GoodnessError(AFOError):
    """善 (Goodness) 에러 - 안전성 및 윤리 관련"""

    pass


class BeautyError(AFOError):
    """美 (Beauty) 에러 - 구조적 우아함 관련"""

    pass


class SerenityError(AFOError):
    """孝 (Serenity) 에러 - 평온함 및 마찰 관련"""

    pass


class EternityError(AFOError):
    """永 (Eternity) 에러 - 영속성 관련"""

    pass


class ValidationError(AFOError):
    """검증 에러 - 입력값 검증 실패 관련 (善 - Goodness)"""

    pass


def handle_errors(
    default_return: Any = None,
    log_error: bool = True,
    reraise: bool = False,
    error_type: type[AFOError] = AFOError,
) -> Callable[[Callable[P, T]], Callable[P, T | Any]]:
    """에러 핸들링 데코레이터 (眞善美孝永 철학)

    Args:
        default_return: 에러 발생 시 기본 반환값
        log_error: 에러 로깅 여부
        reraise: 에러 재발생 여부
        error_type: 변환할 에러 타입

    Returns:
        데코레이터 함수

    """

    def decorator(func: Callable[P, T]) -> Callable[P, T | Any]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        f"[{func.__name__}] Error: {e}",
                        exc_info=True,
                        extra={
                            "function": func.__name__,
                            "error_type": type(e).__name__,
                            "traceback": traceback.format_exc(),
                        },
                    )

                if reraise:
                    if isinstance(e, AFOError):
                        raise
                    raise error_type(str(e)) from e

                return default_return

        return wrapper

    return decorator


async def handle_async_errors(
    default_return: Any = None,
    log_error: bool = True,
    reraise: bool = False,
    error_type: type[AFOError] = AFOError,
) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    """비동기 에러 핸들링 데코레이터 (眞善美孝永 철학)

    Args:
        default_return: 에러 발생 시 기본 반환값
        log_error: 에러 로깅 여부
        reraise: 에러 재발생 여부
        error_type: 변환할 에러 타입

    Returns:
        데코레이터 함수

    """

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        f"[{func.__name__}] Async Error: {e}",
                        exc_info=True,
                        extra={
                            "function": func.__name__,
                            "error_type": type(e).__name__,
                            "traceback": traceback.format_exc(),
                        },
                    )

                if reraise:
                    if isinstance(e, AFOError):
                        raise
                    raise error_type(str(e)) from e

                return default_return

        return wrapper

    return decorator


def safe_execute[T](
    func: Callable[..., T],
    default: Any = None,
    log_error: bool = True,
) -> Callable[..., T | Any]:
    """안전한 함수 실행 (善 - Goodness)

    Args:
        func: 실행할 함수
        default: 에러 발생 시 기본 반환값
        log_error: 에러 로깅 여부

    Returns:
        래핑된 함수

    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T | Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_error:
                logger.error(f"Safe execute failed: {e}", exc_info=True)
            return default

    return wrapper


async def safe_execute_async(
    func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs
) -> tuple[Any | None, Exception | None]:
    """안전한 비동기 함수 실행 (善 - Goodness)

    Returns:
        (result, error) 튜플

    """
    try:
        result = await func(*args, **kwargs)
        return result, None
    except Exception as e:
        logger.error(f"Safe async execute failed: {e}", exc_info=True)
        return None, e


def validate_input(
    value: Any,
    name: str,
    validator: Callable[[Any], bool],
    error_message: str | None = None,
) -> Any:
    """입력값 검증 (善 - Goodness)

    Args:
        value: 검증할 값
        name: 값의 이름 (에러 메시지용)
        validator: 검증 함수 (True 반환 시 통과)
        error_message: 커스텀 에러 메시지

    Returns:
        검증된 값

    Raises:
        ValidationError: 검증 실패 시

    """
    if not validator(value):
        message = error_message or f"Validation failed for {name}: {value}"
        raise ValidationError(message, error_code="VALIDATION_FAILED")

    return value


def require_not_none(value: Any, name: str) -> Any:
    """None 값 검증 (善 - Goodness)

    Args:
        value: 검증할 값
        name: 값의 이름 (에러 메시지용)

    Returns:
        검증된 값 (None이 아닌 경우)

    Raises:
        ValidationError: 값이 None인 경우

    """
    if value is None:
        raise ValidationError(f"{name} cannot be None", error_code="NONE_VALUE")

    return value


def log_and_return_error(error: AFOError, context: str | None = None) -> dict[str, Any]:
    """에러 로깅 및 응답 생성 (善 - Goodness)

    Args:
        error: 발생한 에러
        context: 에러 발생 컨텍스트

    Returns:
        에러 응답 딕셔너리

    """
    error_context = context or "unknown"
    logger.error(
        f"[{error_context}] Error: {error.message}",
        exc_info=True,
        extra={
            "error_code": error.error_code,
            "error_details": error.details,
            "context": error_context,
        },
    )

    return {
        "success": False,
        "error_code": error.error_code or "UNKNOWN_ERROR",
        "error_message": error.message,
        "error_details": error.details,
        "context": error_context,
    }
