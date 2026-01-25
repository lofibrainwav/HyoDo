from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from AFO.utils.redis_connection import get_redis_client

# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Wallet Session API
"""


# 설정 및 유틸리티
API_PROVIDERS = ["openai", "anthropic", "google", "ollama"]

session_router = APIRouter(prefix="/session")


class WalletSessionRequest(BaseModel):
    session_id: str
    provider: str | None = None


@session_router.get("/{session_id}")
async def get_wallet_session(session_id: str) -> dict[str, Any]:
    """
    **Wallet 세션 조회** - Redis에서 세션 정보를 가져옴
    """
    try:
        redis_client = get_redis_client()
        session_key = f"afo:wallet:session:{session_id}"

        try:
            session_data = redis_client.hgetall(session_key)
            if not session_data:
                return {
                    "session_id": session_id,
                    "status": "not_found",
                    "timestamp": datetime.now().isoformat(),
                }

            return {
                "session_id": session_id,
                "status": session_data.get("status", "unknown"),
                "provider": session_data.get("provider", "unknown"),
                "created_at": session_data.get("created_at"),
                "expires_at": session_data.get("expires_at"),
                "last_accessed": session_data.get("last_accessed"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "session_id": session_id,
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wallet session: {e}") from e


@session_router.post("/extract")
async def extract_wallet_session(request: WalletSessionRequest) -> dict[str, Any]:
    """
    **Wallet 세션 추출** - 브라우저 세션에서 API 키 추출
    """
    try:
        if request.provider and request.provider not in API_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider. Must be one of: {', '.join(API_PROVIDERS)}",
            )

        # 실제 추출 로직 생략 (데모용 Mock 데이터 생성)
        session_id = request.session_id
        session_key = f"afo:wallet:session:{session_id}"
        session_data = {
            "status": "active",
            "provider": request.provider or "unknown",
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "expires_at": (datetime.now().timestamp() + 86400),
        }

        try:
            redis_client = get_redis_client()
            # MyPy compatible cast for Redis hset mapping
            hset_mapping = cast("dict[str | bytes, str | bytes | float | int]", session_data)
            redis_client.hset(session_key, mapping=hset_mapping)
            redis_client.expire(session_key, 86400)

            return {
                "success": True,
                "session_id": session_id,
                "provider": session_data["provider"],
                "expires_at": session_data["expires_at"],
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to save wallet session to Redis: {e}"
            ) from e

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wallet session extraction failed: {e}") from e
