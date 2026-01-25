from __future__ import annotations

from datetime import datetime
from typing import Any

import redis
from fastapi import APIRouter

from AFO.config.settings import get_settings
from AFO.models import API_PROVIDERS

# Trinity Score: 90.0 (Established by Chancellor)
"""
Wallet Billing Router - API 사용량 및 청구 관리
Strangler Fig Pattern (간결화 버전)
"""

# Create router
billing_router = APIRouter(prefix="/billing", tags=["Wallet Billing"])


@billing_router.get("/usage/{api_id}")
async def get_api_usage(api_id: str) -> dict[str, Any]:
    """
    **API 사용량 조회** - 특정 API의 사용량 및 청구 정보

    **Path Parameter**: api_id (API 식별자)
    **Response**: 사용량 정보
    """
    try:
        # 사용량 조회 로직 - Redis 기반 구현
        settings = get_settings()
        redis_client = redis.from_url(settings.get_redis_url(), decode_responses=True)

        # API 사용량 키
        usage_key = f"wallet:usage:{api_id}"

        # 사용량 데이터 조회
        usage_data = redis_client.hgetall(usage_key)

        return {
            "api_id": api_id,
            "usage": {
                "requests": int(usage_data.get("requests", 0)),
                "tokens": int(usage_data.get("tokens", 0)),
                "cost": float(usage_data.get("cost", 0.0)),
                "last_updated": usage_data.get("last_updated"),
            },
            "timestamp": datetime.now().isoformat(),
        }

    except ImportError:
        # Redis unavailable, return mock data
        return {
            "api_id": api_id,
            "usage": {"requests": 0, "tokens": 0, "cost": 0.0},
            "timestamp": datetime.now().isoformat(),
            "note": "Redis unavailable - mock data",
        }
    except Exception as e:
        # Redis error, return basic info
        return {
            "api_id": api_id,
            "usage": {"requests": 0, "tokens": 0, "cost": 0.0, "error": str(e)},
            "timestamp": datetime.now().isoformat(),
        }


@billing_router.get("/summary")
async def get_billing_summary() -> dict[str, Any]:
    """
    **청구 요약** - 전체 API 사용량 및 청구 요약

    **Response**: 청구 요약 정보
    """
    try:
        # 청구 요약 로직 - Redis 기반 집계
        settings = get_settings()
        redis_client = redis.from_url(settings.get_redis_url(), decode_responses=True)

        # 모든 API 제공자에 대한 사용량 집계
        total_requests = 0
        total_tokens = 0
        total_cost = 0.0
        api_summaries = []

        for provider in API_PROVIDERS:
            usage_key = f"wallet:usage:{provider}"
            usage_data = redis_client.hgetall(usage_key)

            if usage_data:
                requests = int(usage_data.get("requests", 0))
                tokens = int(usage_data.get("tokens", 0))
                cost = float(usage_data.get("cost", 0.0))

                total_requests += requests
                total_tokens += tokens
                total_cost += cost

                api_summaries.append(
                    {
                        "provider": provider,
                        "requests": requests,
                        "tokens": tokens,
                        "cost": cost,
                        "last_updated": usage_data.get("last_updated"),
                    }
                )

        return {
            "total_apis": len(API_PROVIDERS),
            "total_usage": {
                "requests": total_requests,
                "tokens": total_tokens,
                "cost": round(total_cost, 4),
            },
            "api_summaries": api_summaries,
            "timestamp": datetime.now().isoformat(),
        }

    except ImportError:
        # Redis unavailable, return mock data
        return {
            "total_apis": len(API_PROVIDERS),
            "total_usage": {"requests": 0, "tokens": 0, "cost": 0.0},
            "api_summaries": [],
            "timestamp": datetime.now().isoformat(),
            "note": "Redis unavailable - mock data",
        }
    except Exception as e:
        # Redis error, return basic info
        return {
            "total_apis": len(API_PROVIDERS),
            "total_usage": {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0,
                "error": str(e),
            },
            "api_summaries": [],
            "timestamp": datetime.now().isoformat(),
        }
