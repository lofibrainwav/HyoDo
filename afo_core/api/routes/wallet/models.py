from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""Wallet Models - Pydantic 모델 및 상수 정의 (DRY 원칙)
승상의 간결화: 중복 제거, 타입 안전성 향상
"""


# 승상의 간결화: API Provider 상수 정의 (DRY 원칙)
API_PROVIDERS = ["openai", "anthropic", "google", "azure", "aws"]
WALLET_OPERATIONS = ["setup", "sync", "test", "status", "get", "delete"]


# Request Models
class WalletAPIKeyRequest(BaseModel):
    """Wallet API 키 설정 요청 모델"""

    provider: str = Field(..., description="API 제공자")
    api_key: str = Field(..., description="API 키")
    environment: str = Field(default="production", description="환경 (production, development)")


class WalletSessionRequest(BaseModel):
    """Wallet 세션 요청 모델"""

    session_id: str = Field(..., description="세션 ID")
    provider: str | None = Field(default=None, description="API 제공자")


# Response Models
class WalletStatusResponse(BaseModel):
    """Wallet 상태 응답 모델"""

    status: str
    providers: dict[str, Any]
    total_apis: int
    timestamp: str


class WalletAPIResponse(BaseModel):
    """Wallet API 응답 모델"""

    api_id: str
    provider: str
    status: str
    timestamp: str
