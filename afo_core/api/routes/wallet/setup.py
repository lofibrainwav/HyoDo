from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from AFO.models import API_PROVIDERS, WalletAPIKeyRequest, WalletStatusResponse

# Trinity Score: 90.0 (Established by Chancellor)
"""
Wallet Setup Router - API 키 설정 및 관리
Strangler Fig Pattern (간결화 버전)
"""

# Create router
setup_router = APIRouter(prefix="/setup", tags=["Wallet Setup"])


@setup_router.post("/api-key")
async def set_api_key(request: WalletAPIKeyRequest) -> dict[str, Any]:
    """
    **Wallet API 키 설정** - API 키 저장 및 관리 (Phase 31 구현)

    **Request Body**:
    - `provider` (str): API 제공자 (openai, anthropic, google 등)
    - `api_key` (str): API 키
    - `environment` (str): 환경 (production, development)

    **Response**: 설정 결과
    """
    try:
        # Provider 검증
        if request.provider not in API_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider. Must be one of: {', '.join(API_PROVIDERS)}",
            )

        # API 키 기본 검증
        if not request.api_key or len(request.api_key.strip()) == 0:
            raise HTTPException(status_code=400, detail="API key cannot be empty")

        # API 키 길이 검증 (너무 짧거나 긴 키 방지)
        if len(request.api_key) < 10:
            raise HTTPException(status_code=400, detail="API key is too short")

        # 실제 API 키 저장 (domain/wallet 사용)
        try:
            from AFO.api_wallet import create_wallet

            wallet = create_wallet()
            wallet.set(
                name=f"{request.provider}_{request.environment}",
                value=request.api_key,
                key_type="api",
                service=request.provider,
                description=f"{request.provider} API key for {request.environment}",
            )

            return {
                "status": "success",
                "message": f"API key for {request.provider} saved securely",
                "provider": request.provider,
                "environment": request.environment,
                "encrypted": True,
                "timestamp": datetime.now().isoformat(),
            }

        except ImportError as e:
            # Wallet 모듈을 사용할 수 없는 경우
            raise HTTPException(
                status_code=503,
                detail="API wallet system not available. Please ensure wallet components are installed.",
            ) from e
        except Exception as e:
            # Wallet 저장 실패
            raise HTTPException(
                status_code=500, detail=f"Failed to save API key securely: {e!s}"
            ) from e

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e!s}") from e


@setup_router.get("/status", response_model=WalletStatusResponse)
async def get_wallet_status() -> WalletStatusResponse:
    """
    **Wallet 상태 조회** - API Wallet 시스템 상태 확인 (Phase 31 구현)

    **Response**: Wallet 상태 및 API 제공자 정보
    """
    try:
        # 실제 wallet 상태 조회 (domain/wallet 사용)
        try:
            from AFO.api_wallet import create_wallet

            wallet = create_wallet()
            keys_list = wallet.list_keys()

            # Provider별 상태 계산
            providers_status = {}
            for provider in API_PROVIDERS:
                # 해당 provider의 키가 있는지 확인
                provider_keys = [
                    key
                    for key in keys_list
                    if key.get("service") == provider
                    or any(env in key.get("name", "") for env in ["production", "development"])
                ]
                providers_status[provider] = len(provider_keys) > 0

            total_keys = len(keys_list)

            return WalletStatusResponse(
                status="operational" if total_keys > 0 else "empty",
                providers=providers_status,
                total_apis=total_keys,
                timestamp=datetime.now().isoformat(),
            )

        except ImportError as e:
            # Wallet 모듈을 사용할 수 없는 경우
            raise HTTPException(
                status_code=503,
                detail="API wallet system not available. Please ensure wallet components are installed.",
            ) from e
        except Exception:
            # Wallet 조회 실패 - 기본 상태 반환
            return WalletStatusResponse(
                status="error",
                providers=dict.fromkeys(API_PROVIDERS, False),
                total_apis=0,
                timestamp=datetime.now().isoformat(),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wallet status: {e}") from e
