# Trinity Score: 90.0 (Established by Chancellor)
"""
Wallet Models Tests
TICKET-150: 0% 커버리지 모듈 테스트 - wallet/models.py

眞 (Truth): Pydantic 모델 검증 테스트
"""

import pytest
from api.routes.wallet.models import (
    API_PROVIDERS,
    WALLET_OPERATIONS,
    WalletAPIKeyRequest,
    WalletAPIResponse,
    WalletSessionRequest,
    WalletStatusResponse,
)
from pydantic import ValidationError


class TestWalletConstants:
    """상수 테스트"""

    def test_api_providers_list(self):
        """API 제공자 목록 검증"""
        assert isinstance(API_PROVIDERS, list)
        assert len(API_PROVIDERS) == 5
        assert "openai" in API_PROVIDERS
        assert "anthropic" in API_PROVIDERS
        assert "google" in API_PROVIDERS

    def test_wallet_operations_list(self):
        """Wallet 작업 목록 검증"""
        assert isinstance(WALLET_OPERATIONS, list)
        assert "setup" in WALLET_OPERATIONS
        assert "sync" in WALLET_OPERATIONS
        assert "status" in WALLET_OPERATIONS


class TestWalletAPIKeyRequest:
    """WalletAPIKeyRequest 모델 테스트"""

    def test_valid_request(self):
        """유효한 요청 생성"""
        request = WalletAPIKeyRequest(
            provider="openai",
            api_key="sk-test-key-12345",
        )
        assert request.provider == "openai"
        assert request.api_key == "sk-test-key-12345"
        assert request.environment == "production"  # default

    def test_custom_environment(self):
        """커스텀 환경 설정"""
        request = WalletAPIKeyRequest(
            provider="anthropic",
            api_key="test-key",
            environment="development",
        )
        assert request.environment == "development"

    def test_missing_required_field(self):
        """필수 필드 누락 시 에러"""
        with pytest.raises(ValidationError):
            WalletAPIKeyRequest(provider="openai")  # api_key 누락


class TestWalletSessionRequest:
    """WalletSessionRequest 모델 테스트"""

    def test_valid_request(self):
        """유효한 세션 요청"""
        request = WalletSessionRequest(session_id="session-123")
        assert request.session_id == "session-123"
        assert request.provider is None  # default

    def test_with_provider(self):
        """제공자 포함 세션 요청"""
        request = WalletSessionRequest(
            session_id="session-456",
            provider="google",
        )
        assert request.provider == "google"


class TestWalletStatusResponse:
    """WalletStatusResponse 모델 테스트"""

    def test_valid_response(self):
        """유효한 상태 응답"""
        response = WalletStatusResponse(
            status="active",
            providers={"openai": {"status": "connected"}},
            total_apis=3,
            timestamp="2026-01-21T12:00:00Z",
        )
        assert response.status == "active"
        assert response.total_apis == 3


class TestWalletAPIResponse:
    """WalletAPIResponse 모델 테스트"""

    def test_valid_response(self):
        """유효한 API 응답"""
        response = WalletAPIResponse(
            api_id="api-001",
            provider="openai",
            status="active",
            timestamp="2026-01-21T12:00:00Z",
        )
        assert response.api_id == "api-001"
        assert response.provider == "openai"
