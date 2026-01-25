from __future__ import annotations

import inspect
import re
from datetime import datetime
from typing import Any, TypeGuard
from uuid import UUID

# Trinity Score: 90.0 (Established by Chancellor)
"""Phase 11: 고급 타입 패턴 적용 - 타입 가드 함수들

런타임 타입 안전성을 위한 TypeGuard 기반 타입 검증 함수들
- 런타임 타입 검증 강화
- isinstance() 패턴 표준화
- 정적 타입 검사와 런타임 검증 통합
"""


# 기본 타입 가드들
def is_string(value: Any) -> TypeGuard[str]:
    """값이 문자열인지 확인"""
    return isinstance(value, str)


def is_int(value: Any) -> TypeGuard[int]:
    """값이 정수인지 확인"""
    return isinstance(value, int)


def is_float(value: Any) -> TypeGuard[float]:
    """값이 실수인지 확인"""
    return isinstance(value, float)


def is_bool(value: Any) -> TypeGuard[bool]:
    """값이 불리언인지 확인"""
    return isinstance(value, bool)


def is_list(value: Any) -> TypeGuard[list[Any]]:
    """값이 리스트인지 확인"""
    return isinstance(value, list)


def is_dict(value: Any) -> TypeGuard[dict[Any, Any]]:
    """값이 딕셔너리인지 확인"""
    return isinstance(value, dict)


def is_uuid_string(value: Any) -> TypeGuard[str]:
    """값이 유효한 UUID 문자열인지 확인"""
    if not isinstance(value, str):
        return False
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def is_email(value: Any) -> TypeGuard[str]:
    """값이 유효한 이메일 주소인지 확인"""
    if not isinstance(value, str):
        return False

    # RFC 5322 준수 이메일 패턴 (간소화)
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, value.strip()))


def is_url(value: Any) -> TypeGuard[str]:
    """값이 유효한 URL인지 확인"""
    if not isinstance(value, str):
        return False

    # 기본 URL 패턴 (http/https)
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, value.strip()))


def is_positive_int(value: Any) -> TypeGuard[int]:
    """값이 양의 정수인지 확인"""
    return isinstance(value, int) and value > 0


def is_non_negative_int(value: Any) -> TypeGuard[int]:
    """값이 0 이상의 정수인지 확인"""
    return isinstance(value, int) and value >= 0


def is_positive_float(value: Any) -> TypeGuard[float]:
    """값이 양의 실수인지 확인"""
    return isinstance(value, (int, float)) and float(value) > 0


def is_percentage(value: Any) -> TypeGuard[float]:
    """값이 0-100 사이의 백분율인지 확인"""
    if not isinstance(value, (int, float)):
        return False
    percent = float(value)
    return 0 <= percent <= 100


def is_datetime_string(value: Any) -> TypeGuard[str]:
    """값이 ISO 형식의 날짜/시간 문자열인지 확인"""
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


# 복합 타입 가드들
def is_non_empty_string(value: Any) -> TypeGuard[str]:
    """값이 비어있지 않은 문자열인지 확인"""
    return isinstance(value, str) and bool(value.strip())


def is_non_empty_list(value: Any) -> TypeGuard[list[Any]]:
    """값이 비어있지 않은 리스트인지 확인"""
    return isinstance(value, list) and len(value) > 0


def is_non_empty_dict(value: Any) -> TypeGuard[dict[Any, Any]]:
    """값이 비어있지 않은 딕셔너리인지 확인"""
    return isinstance(value, dict) and len(value) > 0


# 도메인 특화 타입 가드들
def is_valid_skill_category(value: Any) -> TypeGuard[str]:
    """값이 유효한 스킬 카테고리인지 확인"""
    if not isinstance(value, str):
        return False

    valid_categories = {"truth", "goodness", "beauty", "serenity", "eternity"}
    return value.lower() in valid_categories


def is_valid_philosophy_score(value: Any) -> TypeGuard[float]:
    """값이 유효한 철학 점수인지 확인 (0-100)"""
    if not isinstance(value, (int, float)):
        return False
    score = float(value)
    return 0 <= score <= 100


def is_valid_complexity(value: Any) -> TypeGuard[int]:
    """값이 유효한 복잡도 점수인지 확인 (1-10)"""
    return isinstance(value, int) and 1 <= value <= 10


def is_valid_priority(value: Any) -> TypeGuard[str]:
    """값이 유효한 우선순위인지 확인"""
    if not isinstance(value, str):
        return False
    return value.lower() in {"high", "medium", "low"}


def is_valid_status(value: Any) -> TypeGuard[str]:
    """값이 유효한 상태값인지 확인"""
    if not isinstance(value, str):
        return False
    valid_statuses = {
        "pending",
        "in_progress",
        "completed",
        "cancelled",
        "deferred",
        "planning",
        "in-development",
        "archived",
    }
    return value.lower() in valid_statuses


# API 요청 검증 타입 가드들
def is_valid_pagination_params(page: Any, page_size: Any, max_page_size: int = 100) -> bool:
    """페이지네이션 파라미터가 유효한지 확인"""
    return is_positive_int(page) and is_positive_int(page_size) and page_size <= max_page_size


def is_valid_api_request_data(data: Any) -> TypeGuard[dict[str, Any]]:
    """API 요청 데이터가 유효한 딕셔너리인지 확인"""
    return isinstance(data, dict) and all(isinstance(k, str) for k in data.keys())


# 안전한 타입 변환 함수들 (타입 가드와 결합)
def safe_to_string(value: Any, default: str = "") -> str:
    """안전하게 문자열로 변환 (타입 가드 적용)"""
    if is_string(value):
        return value
    elif value is None:
        return default
    else:
        return str(value)


def safe_to_int(value: Any, default: int = 0) -> int:
    """안전하게 정수로 변환 (타입 가드 적용)"""
    if is_int(value):
        return value
    elif isinstance(value, (float, str)):
        try:
            return int(float(value))
        except (ValueError, OverflowError):
            return default
    else:
        return default


def safe_to_float(value: Any, default: float = 0.0) -> float:
    """안전하게 실수로 변환 (타입 가드 적용)"""
    if is_float(value):
        return value
    elif is_int(value):
        return float(value)
    elif isinstance(value, str):
        try:
            return float(value)
        except (ValueError, OverflowError):
            return default
    else:
        return default


def safe_to_bool(value: Any, default: bool = False) -> bool:
    """안전하게 불리언으로 변환 (타입 가드 적용)"""
    if is_bool(value):
        return value
    elif isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    elif isinstance(value, (int, float)):
        return bool(value)
    else:
        return default


# 제네릭 타입 가드 헬퍼
def is_instance_of_type(value: Any, expected_type: type) -> bool:
    """제네릭 타입 확인 헬퍼"""
    return isinstance(value, expected_type)


def is_list_of_type(value: Any, item_type: type) -> bool:
    """특정 타입의 리스트인지 확인"""
    return isinstance(value, list) and all(isinstance(item, item_type) for item in value)


def is_dict_of_types(value: Any, key_type: type, value_type: type) -> bool:
    """특정 타입들의 딕셔너리인지 확인"""
    return (
        isinstance(value, dict)
        and all(isinstance(k, key_type) for k in value.keys())
        and all(isinstance(v, value_type) for v in value.values())
    )


# 런타임 타입 검증 데코레이터
def validate_types(**type_guards: Any) -> Any:
    """런타임 타입 검증 데코레이터

    함수 파라미터에 타입 가드를 적용합니다.

    사용 예:
    @validate_types(name=is_non_empty_string, age=is_positive_int)
    def create_user(name: str, age: int) -> User:
        ...
    """

    def decorator(func: Any) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 함수 시그니처에서 파라미터 이름 추출

            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())

            # 위치 인자와 키워드 인자 결합
            all_args = dict(zip(param_names, args))
            all_args.update(kwargs)

            # 각 파라미터 검증
            for param_name, guard_func in type_guards.items():
                if param_name in all_args:
                    value = all_args[param_name]
                    if not guard_func(value):
                        raise TypeError(
                            f"파라미터 '{param_name}'의 값 '{value}'이(가) "
                            f"타입 검증 '{guard_func.__name__}'을 통과하지 못했습니다."
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator
