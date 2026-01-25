from functools import lru_cache
from typing import Annotated

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.functional_validators import AfterValidator


@lru_cache(maxsize=1024)
def positive_non_zero(v: float | int) -> float | int:
    """캐시 적용 - 동일 입력 반복 시 속도 극대화"""
    if v <= 0:
        raise ValueError("양수여야 하며 0이 될 수 없습니다")
    return round(float(v), 2)


PositiveNonZero = Annotated[float, AfterValidator(positive_non_zero)]


class AFOBaseModel(BaseModel):
    """왕국 모든 모델의 조상 - 안전·평온·영속성 보장"""

    model_config = ConfigDict(
        strict=False,  # 자동 변환 허용 (형님 편의)
        extra="forbid",  # 정의 안 된 키 차단 (보안)
        frozen=True,  # 불변성 (永)
        validate_default=True,
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def kingdom_consistency_check(self) -> None:
        """왕국 공통 최종 검증"""
        return self
