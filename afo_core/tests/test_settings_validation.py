from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from AFO.config.settings import AFOSettings, get_settings


def test_settings_type_validation() -> None:
    """테스트: 잘못된 데이터 타입이 들어왔을 때 Pydantic 검증이 작동하는지 확인"""
    # 眞: Truth - 타입 안전성 검증

    # 1. 포트 번호가 문자열인 경우 (Pydantic은 타입 캐스팅을 시도하지만, 숫자가 아닌 경우 에러)
    invalid_settings_data = {"REDIS_PORT": "invalid_port"}

    # Mock environment variables or use a custom class for testing
    class TestSettings(AFOSettings):
        class Config:
            env_prefix = "AFO_TEST_"

    os.environ["AFO_TEST_REDIS_PORT"] = "not_a_number"

    with pytest.raises(ValidationError):
        TestSettings()

    # Clean up
    del os.environ["AFO_TEST_REDIS_PORT"]


def test_settings_range_validation() -> None:
    """테스트: 범위 제한(ge/le)이 작동하는지 확인"""
    # 善: Goodness - 안정성 검증

    os.environ["AFO_TEST_REDIS_MAX_CONNECTIONS"] = "0"  # ge=1 이어야 함

    class TestSettings(AFOSettings):
        class Config:
            env_prefix = "AFO_TEST_"

    with pytest.raises(ValidationError):
        TestSettings()

    del os.environ["AFO_TEST_REDIS_MAX_CONNECTIONS"]


def test_singleton_consistency() -> None:
    """테스트: get_settings()가 항상 같은 인스턴스를 반환하는지 확인 (SSOT)"""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_redis_url_construction() -> None:
    """테스트: REDIS_URL이 없는 경우 호스트/포트로 올바르게 생성되는지 확인"""
    settings = get_settings()
    url = settings.get_redis_url()
    assert url.startswith("redis://")
    assert str(settings.REDIS_PORT) in url
