from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

# Trinity Score: 90.0 (Established by Chancellor)
"""Phase 11: 고급 타입 패턴 적용 - 프로토콜 인터페이스 정의

서비스 계층의 인터페이스 일관성을 위한 프로토콜 기반 설계
- IService 프로토콜: 공통 서비스 인터페이스
- IRepository 프로토콜: 데이터 액세스 계층 인터페이스
- IValidator 프로토콜: 검증 로직 인터페이스
"""


# 제네릭 타입 변수
T = TypeVar("T")
TKey = TypeVar("TKey")
TResult = TypeVar("TResult")


class IService[T](ABC):
    """서비스 인터페이스 프로토콜

    모든 서비스 클래스가 구현해야 하는 공통 인터페이스입니다.
    """

    @abstractmethod
    async def get_by_id(self, id: TKey) -> T | None:
        """ID로 엔티티 조회"""
        ...

    @abstractmethod
    async def get_all(self) -> list[T]:
        """모든 엔티티 조회"""
        ...

    @abstractmethod
    async def create(self, entity: T) -> T | None:
        """새 엔티티 생성"""
        ...

    @abstractmethod
    async def update(self, id: TKey, entity: T) -> T | None:
        """엔티티 업데이트"""
        ...

    @abstractmethod
    async def delete(self, id: TKey) -> bool:
        """엔티티 삭제"""
        ...


class IRepository[T, TKey](ABC):
    """리포지토리 인터페이스 프로토콜

    데이터 액세스 계층의 표준 인터페이스입니다.
    """

    @abstractmethod
    async def get(self, key: TKey) -> T | None:
        """키로 데이터 조회"""
        ...

    @abstractmethod
    async def get_all(self) -> list[T]:
        """모든 데이터 조회"""
        ...

    @abstractmethod
    async def find(self, predicate: Any) -> list[T]:
        """조건에 맞는 데이터 조회"""
        ...

    @abstractmethod
    async def add(self, entity: T) -> T | None:
        """데이터 추가"""
        ...

    @abstractmethod
    async def update(self, key: TKey, entity: T) -> bool:
        """데이터 업데이트"""
        ...

    @abstractmethod
    async def remove(self, key: TKey) -> bool:
        """데이터 삭제"""
        ...

    @abstractmethod
    async def exists(self, key: TKey) -> bool:
        """데이터 존재 여부 확인"""
        ...


class IValidator[T](ABC):
    """검증 인터페이스 프로토콜

    데이터 검증 로직의 표준 인터페이스입니다.
    """

    @abstractmethod
    def validate(self, data: T) -> ValidationResult:
        """데이터 검증 수행"""
        ...


class ValidationResult:
    """검증 결과 클래스"""

    def __init__(self, is_valid: bool = True, errors: list[str] | None = None) -> None:
        self.is_valid = is_valid
        self.errors = errors or []

    def add_error(self, error: str) -> None:
        """에러 추가"""
        self.errors.append(error)
        self.is_valid = False

    def get_errors(self) -> list[str]:
        """모든 에러 반환"""
        return self.errors.copy()


class ILogger(ABC):
    """로깅 인터페이스 프로토콜"""

    @abstractmethod
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """디버그 레벨 로깅"""
        ...

    @abstractmethod
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """정보 레벨 로깅"""
        ...

    @abstractmethod
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """경고 레벨 로깅"""
        ...

    @abstractmethod
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """에러 레벨 로깅"""
        ...

    @abstractmethod
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """치명적 레벨 로깅"""
        ...


class ICache[T](ABC):
    """캐시 인터페이스 프로토콜"""

    @abstractmethod
    async def get(self, key: str) -> T | None:
        """캐시에서 데이터 조회"""
        ...

    @abstractmethod
    async def set(self, key: str, value: T, ttl: int | None = None) -> bool:
        """캐시에 데이터 저장"""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """캐시 키 존재 여부 확인"""
        ...

    @abstractmethod
    async def clear(self) -> bool:
        """모든 캐시 데이터 삭제"""
        ...


class IConfig(ABC):
    """설정 인터페이스 프로토콜"""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 조회"""
        ...

    @abstractmethod
    def get_bool(self, key: str, default: bool = False) -> bool:
        """불리언 설정 값 조회"""
        ...

    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int:
        """정수 설정 값 조회"""
        ...

    @abstractmethod
    def get_float(self, key: str, default: float = 0.0) -> float:
        """실수 설정 값 조회"""
        ...

    @abstractmethod
    def get_list(self, key: str, default: list[Any] | None = None) -> list[Any]:
        """리스트 설정 값 조회"""
        ...


# 추상 기본 클래스 구현 (ABC)
class BaseService[T, TKey](ABC):
    """기본 서비스 추상 클래스

    IService 프로토콜의 기본 구현을 제공합니다.
    """

    def __init__(self, repository: IRepository[T, TKey], logger: ILogger) -> None:
        self.repository = repository
        self.logger = logger

    async def get_by_id(self, id: TKey) -> T | None:
        """기본 ID 조회 구현"""
        try:
            return await self.repository.get(id)
        except Exception as e:
            self.logger.error(f"엔티티 조회 실패 (ID: {id}): {e}")
            return None

    async def get_all(self) -> list[T]:
        """기본 전체 조회 구현"""
        try:
            return await self.repository.get_all()
        except Exception as e:
            self.logger.error(f"전체 엔티티 조회 실패: {e}")
            return []

    @abstractmethod
    async def create(self, entity: T) -> T | None:
        """엔티티 생성 - 서브클래스에서 구현 필요"""
        ...

    @abstractmethod
    async def update(self, id: TKey, entity: T) -> T | None:
        """엔티티 업데이트 - 서브클래스에서 구현 필요"""
        ...

    async def delete(self, id: TKey) -> bool:
        """기본 삭제 구현"""
        try:
            return await self.repository.remove(id)
        except Exception as e:
            self.logger.error(f"엔티티 삭제 실패 (ID: {id}): {e}")
            return False


class BaseValidator[T](ABC):
    """기본 검증 추상 클래스

    IValidator 프로토콜의 기본 구현을 제공합니다.
    """

    def __init__(self, logger: ILogger) -> None:
        self.logger = logger

    @abstractmethod
    def validate(self, data: T) -> ValidationResult:
        """데이터 검증 - 서브클래스에서 구현 필요"""
        ...


class BaseRepository[T, TKey](ABC):
    """기본 리포지토리 추상 클래스

    IRepository 프로토콜의 기본 구현을 제공합니다.
    """

    def __init__(self, logger: ILogger) -> None:
        self.logger = logger

    @abstractmethod
    async def get(self, key: TKey) -> T | None:
        """키로 데이터 조회 - 서브클래스에서 구현 필요"""
        ...

    @abstractmethod
    async def get_all(self) -> list[T]:
        """모든 데이터 조회 - 서브클래스에서 구현 필요"""
        ...

    async def find(self, predicate: Any) -> list[T]:
        """기본 조건 조회 구현"""
        try:
            all_items = await self.get_all()
            return [item for item in all_items if predicate(item)]
        except Exception as e:
            self.logger.error(f"조건 조회 실패: {e}")
            return []

    @abstractmethod
    async def add(self, entity: T) -> T | None:
        """데이터 추가 - 서브클래스에서 구현 필요"""
        ...

    @abstractmethod
    async def update(self, key: TKey, entity: T) -> bool:
        """데이터 업데이트 - 서브클래스에서 구현 필요"""
        ...

    @abstractmethod
    async def remove(self, key: TKey) -> bool:
        """데이터 삭제 - 서브클래스에서 구현 필요"""
        ...

    async def exists(self, key: TKey) -> bool:
        """기본 존재 여부 확인 구현"""
        try:
            return await self.get(key) is not None
        except Exception as e:
            self.logger.error(f"존재 여부 확인 실패 (키: {key}): {e}")
            return False


# 타입 가드 함수들
def is_service(obj: Any) -> bool:
    """객체가 특정 서비스 타입을 구현하는지 확인"""
    return isinstance(obj, IService) and hasattr(obj, "create")


def is_repository(obj: Any) -> bool:
    """객체가 특정 리포지토리 타입을 구현하는지 확인"""
    return isinstance(obj, IRepository) and hasattr(obj, "add")


def is_validator(obj: Any) -> bool:
    """객체가 특정 검증 타입을 구현하는지 확인"""
    return isinstance(obj, IValidator) and hasattr(obj, "validate")
