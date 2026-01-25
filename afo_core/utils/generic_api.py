from __future__ import annotations

import logging
import re
from typing import Any, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel

# Trinity Score: 90.0 (Established by Chancellor)
"""Phase 11: 고급 타입 패턴 적용 - 제네릭 API 유틸리티

코드 재사용성과 타입 안전성을 위한 제네릭 타입 패턴 구현
- 제네릭 API 응답 핸들러
- 타입 안전한 변환 유틸리티
- 공통 에러 처리 패턴
"""


# 로깅 설정
logger = logging.getLogger(__name__)

# 제네릭 타입 변수
T = TypeVar("T")
U = TypeVar("U")


class APIResponse[T](BaseModel):
    """제네릭 API 응답 모델

    모든 API 엔드포인트에서 일관된 응답 형식을 제공합니다.
    """

    success: bool
    data: T | None = None
    message: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class PaginatedResponse[T](BaseModel):
    """제네릭 페이지네이션 응답 모델

    목록 조회 API에서 일관된 페이지네이션 형식을 제공합니다.
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class APIResult[T](BaseModel):
    """API 작업 결과 래퍼

    성공/실패 상태를 명확히 표현합니다.
    """

    success: bool
    value: T | None = None
    error_message: str | None = None

    @classmethod
    def ok(cls, value: T) -> APIResult[T]:
        """성공 결과 생성"""
        return cls(success=True, value=value)

    @classmethod
    def error(cls, message: str) -> APIResult[T]:
        """에러 결과 생성"""
        return cls(success=False, error_message=message)


def safe_int_conversion(value: Any, default: int = 0) -> int:
    """타입 안전한 int 변환

    다양한 입력 타입을 안전하게 int로 변환합니다.

    Args:
        value: 변환할 값
        default: 변환 실패 시 기본값

    Returns:
        변환된 int 값
    """
    if isinstance(value, int):
        return value
    elif isinstance(value, float):
        return int(value)
    elif isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            logger.warning(f"문자열을 int로 변환 실패: {value}")
            return default
    else:
        logger.warning(f"알 수 없는 타입을 int로 변환: {type(value)} - {value}")
        return default


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """타입 안전한 float 변환

    다양한 입력 타입을 안전하게 float로 변환합니다.

    Args:
        value: 변환할 값
        default: 변환 실패 시 기본값

    Returns:
        변환된 float 값
    """
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            logger.warning(f"문자열을 float로 변환 실패: {value}")
            return default
    else:
        logger.warning(f"알 수 없는 타입을 float로 변환: {type(value)} - {value}")
        return default


def safe_str_conversion(value: Any, default: str = "") -> str:
    """타입 안전한 str 변환

    다양한 입력 타입을 안전하게 str로 변환합니다.

    Args:
        value: 변환할 값
        default: 변환 실패 시 기본값

    Returns:
        변환된 str 값
    """
    if isinstance(value, str):
        return value
    elif value is None:
        return default
    else:
        try:
            return str(value)
        except Exception:
            logger.warning(f"값을 str로 변환 실패: {type(value)} - {value}")
            return default


def create_success_response[T](
    data: T, message: str | None = None, metadata: dict[str, Any] | None = None
) -> APIResponse[T]:
    """성공 응답 생성 헬퍼

    Args:
        data: 응답 데이터
        message: 성공 메시지
        metadata: 추가 메타데이터

    Returns:
        APIResponse 인스턴스
    """
    return APIResponse(success=True, data=data, message=message, metadata=metadata)


def create_error_response(
    error: str, message: str | None = None, metadata: dict[str, Any] | None = None
) -> APIResponse[Any]:
    """에러 응답 생성 헬퍼

    Args:
        error: 에러 메시지
        message: 사용자 친화적 메시지
        metadata: 추가 메타데이터

    Returns:
        APIResponse 인스턴스
    """
    return APIResponse(success=False, error=error, message=message, metadata=metadata)


def handle_api_errors(func_name: str) -> Any:
    """API 에러 처리 데코레이터

    공통 에러 처리 패턴을 제공합니다.

    Args:
        func_name: 함수 이름 (로깅용)

    Returns:
        데코레이터 함수
    """

    def decorator(func: Any) -> Any:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # FastAPI HTTP 예외는 그대로 전파
                raise
            except Exception as e:
                logger.error(f"{func_name} 실행 중 에러: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"{func_name} 처리 중 내부 오류가 발생했습니다.",
                ) from e

        return wrapper

    return decorator


def validate_pagination_params(
    page: int = 1, page_size: int = 20, max_page_size: int = 100
) -> tuple[int, int]:
    """페이지네이션 파라미터 검증

    Args:
        page: 페이지 번호 (1부터 시작)
        page_size: 페이지 크기
        max_page_size: 최대 페이지 크기

    Returns:
        검증된 (page, page_size) 튜플

    Raises:
        ValueError: 파라미터가 유효하지 않은 경우
    """
    if page < 1:
        raise ValueError("페이지 번호는 1 이상이어야 합니다")
    if page_size < 1 or page_size > max_page_size:
        raise ValueError(f"페이지 크기는 1에서 {max_page_size} 사이여야 합니다")

    return page, page_size


def create_paginated_response[T](
    items: list[T], total: int, page: int, page_size: int
) -> PaginatedResponse[T]:
    """페이지네이션 응답 생성 헬퍼

    Args:
        items: 현재 페이지 아이템들
        total: 전체 아이템 수
        page: 현재 페이지 번호
        page_size: 페이지 크기

    Returns:
        PaginatedResponse 인스턴스
    """
    total_pages = (total + page_size - 1) // page_size  # 올림 계산

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


# 타입 가드 함수들
def is_non_empty_string(value: Any) -> bool:
    """비어있지 않은 문자열인지 확인"""
    return isinstance(value, str) and bool(value.strip())


def is_positive_number(value: Any) -> bool:
    """양수인지 확인"""
    try:
        num = float(value)
        return num > 0
    except (TypeError, ValueError):
        return False


def is_valid_email(value: Any) -> bool:
    """유효한 이메일 형식인지 확인"""
    if not isinstance(value, str):
        return False

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, value))


# 제네릭 변환 함수들
def safe_convert(target_type: type[T], value: Any, default: T) -> T:
    """타입 안전한 제네릭 변환

    Args:
        target_type: 목표 타입
        value: 변환할 값
        default: 변환 실패 시 기본값

    Returns:
        변환된 값 또는 기본값
    """
    try:
        if target_type is int:
            return safe_int_conversion(value, default)  # type: ignore
        elif target_type is float:
            return safe_float_conversion(value, default)  # type: ignore
        elif target_type is str:
            return safe_str_conversion(value, default)  # type: ignore
        elif target_type is bool:
            return bool(value) if value is not None else default  # type: ignore
        else:
            # 기타 타입은 직접 변환 시도
            return target_type(value)  # type: ignore
    except Exception:
        logger.warning(f"{target_type.__name__} 변환 실패: {value}")
        return default
