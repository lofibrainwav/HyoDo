"""
MyGPT 컨텍스트 관리

jangjungwha.com ↔ MyGPT 양방향 컨텍스트 동기화
Upstash Redis 기반 실제 데이터 저장
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from .models import MyGPTContextItem, MyGPTContextsResponse

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mygpt", tags=["MyGPT"])

# Upstash Redis 클라이언트 초기화
redis_client = None
try:
    import os

    import redis

    # Upstash Redis 연결 설정
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")

    if upstash_url and upstash_token:
        # Upstash REST API 사용
        from upstash_redis import Redis

        redis_client = Redis(url=upstash_url, token=upstash_token)
        logger.info("✅ Upstash Redis 클라이언트 초기화 성공")
    else:
        # 로컬 Redis 폴백
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))

        redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        logger.info(f"✅ 로컬 Redis 클라이언트 초기화: {redis_host}:{redis_port}")

except ImportError:
    logger.warning("⚠️ Redis 라이브러리가 설치되지 않음")
    redis_client = None
except Exception as e:
    logger.error(f"❌ Redis 클라이언트 초기화 실패: {e}")
    redis_client = None

# MyGPT 컨텍스트 키
MYGPT_CONTEXTS_KEY = "mygpt:contexts"
MYGPT_NOTEBOOKS_KEY = "mygpt:notebooks"


def get_contexts_from_redis() -> list[MyGPTContextItem]:
    """
    Redis에서 MyGPT 컨텍스트 목록을 가져옵니다.
    """
    if not redis_client:
        logger.warning("Redis 클라이언트 없음, 빈 목록 반환")
        return []

    try:
        # 컨텍스트 데이터 가져오기
        contexts_data = redis_client.get(MYGPT_CONTEXTS_KEY)
        if not contexts_data:
            logger.info("Redis에 저장된 컨텍스트 없음")
            return []

        # JSON 파싱
        contexts_list = json.loads(contexts_data)
        contexts = []

        for item in contexts_list:
            try:
                context = MyGPTContextItem(
                    id=item["id"],
                    title=item["title"],
                    tags=item.get("tags", []),
                    content_preview=item.get("content_preview", ""),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    updated_at=datetime.fromisoformat(item["updated_at"]),
                )
                contexts.append(context)
            except (KeyError, ValueError) as e:
                logger.warning(f"컨텍스트 파싱 오류: {e}, 항목: {item}")

        logger.info(f"Redis에서 {len(contexts)}개 컨텍스트 로드")
        return contexts

    except Exception as e:
        logger.error(f"Redis에서 컨텍스트 로드 실패: {e}")
        return []


def save_contexts_to_redis(contexts: list[MyGPTContextItem]) -> bool:
    """
    컨텍스트 목록을 Redis에 저장합니다.
    """
    if not redis_client:
        logger.warning("Redis 클라이언트 없음, 저장하지 않음")
        return False

    try:
        # 컨텍스트를 JSON으로 변환
        contexts_data = []
        for ctx in contexts:
            contexts_data.append(
                {
                    "id": ctx.id,
                    "title": ctx.title,
                    "tags": ctx.tags,
                    "content_preview": ctx.content_preview,
                    "created_at": ctx.created_at.isoformat(),
                    "updated_at": ctx.updated_at.isoformat(),
                }
            )

        # Redis에 저장
        redis_client.set(MYGPT_CONTEXTS_KEY, json.dumps(contexts_data))
        logger.info(f"Redis에 {len(contexts)}개 컨텍스트 저장")
        return True

    except Exception as e:
        logger.error(f"Redis에 컨텍스트 저장 실패: {e}")
        return False


def get_notebooks_from_redis() -> list[dict]:
    """
    Redis에서 노트북 목록을 가져옵니다.
    """
    if not redis_client:
        logger.warning("Redis 클라이언트 없음, 빈 목록 반환")
        return []

    try:
        notebooks_data = redis_client.get(MYGPT_NOTEBOOKS_KEY)
        if not notebooks_data:
            logger.info("Redis에 저장된 노트북 없음")
            return []

        notebooks = json.loads(notebooks_data)
        logger.info(f"Redis에서 {len(notebooks)}개 노트북 로드")
        return notebooks

    except Exception as e:
        logger.error(f"Redis에서 노트북 로드 실패: {e}")
        return []


# 데모 컨텍스트 데이터 (Redis 연결 실패 시 폴백)
DEMO_CONTEXTS = [
    MyGPTContextItem(
        id="o75vEpSlZeNtlMy1bp3jB",
        title="TAX-EASYUP-5165-M (2025 Inflation Update)",
        tags=["tax", "inflation", "2025"],
        content_preview="CPE Depot Easy Update 2025 — Inflation Adjustment Baseline...",
        created_at=datetime(2026, 1, 19, 6, 54),
        updated_at=datetime(2026, 1, 19, 6, 54),
    ),
    MyGPTContextItem(
        id="YNHOAXPKiUai_42YK6Uvp",
        title="Tax EasyUp 5165 - 2025 Comprehensive Summary",
        tags=["tax", "CPE", "inflation"],
        content_preview="### 📘 2025 EasyUp 5165 Comprehensive Summary...",
        created_at=datetime(2026, 1, 19, 6, 48),
        updated_at=datetime(2026, 1, 19, 6, 48),
    ),
    MyGPTContextItem(
        id="0jNiduX5sCws2TQM6q7WQ",
        title="Julie CPA Strategy Log",
        tags=["strategy", "julie-cpa"],
        content_preview="Initial entry for Julie CPA project notebook...",
        created_at=datetime(2026, 1, 18, 20, 30),
        updated_at=datetime(2026, 1, 18, 20, 30),
    ),
    MyGPTContextItem(
        id="z5h1SVRxY_efJTCh3vygz",
        title="AICPA_AI_Audit_Template_v1.0",
        tags=["aicpa", "audit", "template"],
        content_preview="Full AICPA AI Audit Standard Template...",
        created_at=datetime(2026, 1, 18, 10, 48),
        updated_at=datetime(2026, 1, 18, 10, 48),
    ),
    MyGPTContextItem(
        id="rHOGg0sel_1I98kkoA7l8",
        title="Julie_CPA_Full_AFO_Integration",
        tags=["julie-cpa", "afo-gpt", "integration"],
        content_preview="AFO GPT (Tax Simulation / Roth Optimizer...",
        created_at=datetime(2026, 1, 17, 1, 41),
        updated_at=datetime(2026, 1, 17, 1, 41),
    ),
]


@router.get("/contexts", response_model=MyGPTContextsResponse)
async def get_mygpt_contexts(
    limit: int = Query(default=5, description="최대 결과 수"),
    tag: str | None = Query(default=None, description="태그 필터"),
) -> MyGPTContextsResponse:
    """
    MyGPT 컨텍스트 목록 조회

    작업:
    1. Upstash Redis에서 컨텍스트 목록 조회 (실제 데이터 우선)
    2. Redis 연결 실패 시 데모 데이터 사용
    3. 태그 필터링 적용
    4. 페이지네이션 처리
    """
    try:
        # Redis에서 실제 데이터 시도
        contexts = get_contexts_from_redis()

        # Redis에 데이터가 없으면 데모 데이터 사용
        if not contexts:
            logger.info("Redis에 데이터 없음, 데모 데이터 사용")
            contexts = DEMO_CONTEXTS.copy()

            # 데모 데이터를 Redis에 저장 (향후 실제 데이터로 대체 가능)
            if redis_client and len(contexts) > 0:
                save_contexts_to_redis(contexts)

        # 태그 필터링
        if tag:
            contexts = [ctx for ctx in contexts if tag in ctx.tags]
            logger.info(f"태그 '{tag}'로 필터링: {len(contexts)}개 결과")

        # 개수 제한
        original_count = len(contexts)
        if limit < len(contexts):
            contexts = contexts[:limit]

        logger.info(f"MyGPT 컨텍스트 조회: 총 {original_count}개 중 {len(contexts)}개 반환")
        return MyGPTContextsResponse(contexts=contexts, total=len(contexts), page=1)

    except Exception as e:
        logger.error(f"MyGPT 컨텍스트 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Contexts fetch failed: {e!s}")


@router.get("/notebooks", response_model=dict)
async def get_mygpt_notebooks(
    limit: int = Query(default=10, description="최대 결과 수"),
) -> dict:
    """
    MyGPT 노트북 목록 조회

    작업:
    1. Upstash Redis에서 노트북 목록 조회
    2. 페이지네이션 처리
    """
    try:
        # Redis에서 실제 데이터 시도
        notebooks = get_notebooks_from_redis()

        # 개수 제한
        original_count = len(notebooks)
        if limit < len(notebooks):
            notebooks = notebooks[:limit]

        logger.info(f"MyGPT 노트북 조회: 총 {original_count}개 중 {len(notebooks)}개 반환")

        return {
            "notebooks": notebooks,
            "total": len(notebooks),
            "page": 1,
            "source": "redis" if redis_client else "demo",
        }

    except Exception as e:
        logger.error(f"MyGPT 노트북 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Notebooks fetch failed: {e!s}")


@router.get("/status", response_model=dict)
async def get_mygpt_status() -> dict:
    """
    MyGPT Redis 연결 상태 조회
    """
    try:
        status_info = {
            "redis_connected": redis_client is not None,
            "redis_type": "upstash" if os.getenv("UPSTASH_REDIS_REST_URL") else "local",
            "contexts_count": len(get_contexts_from_redis()),
            "notebooks_count": len(get_notebooks_from_redis()),
            "timestamp": datetime.now().isoformat(),
        }

        if redis_client:
            try:
                # Redis ping 테스트
                redis_client.ping()
                status_info["redis_health"] = "healthy"
            except Exception as e:
                status_info["redis_health"] = f"unhealthy: {e!s}"
        else:
            status_info["redis_health"] = "not_connected"

        logger.info(f"MyGPT 상태 조회: {status_info}")
        return status_info

    except Exception as e:
        logger.error(f"MyGPT 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {e!s}")


__all__ = ["router"]
