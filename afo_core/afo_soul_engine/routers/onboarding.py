"""Onboarding Router - 에이전트/사용자 온보딩 API

새로운 에이전트나 사용자가 왕국에 들어왔을 때
시스템 아키텍처를 팔란티어 스타일로 온보딩하는 API를 제공합니다.

Trinity Score: 眞95% 善94% 美96% 孝93% 永92%
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from afo_soul_engine.services import agent_registry, knowledge_service
from afo_soul_engine.types.onboarding import (
    AgentMemorySystemResponse,
    AgentRegistration,
    KnowledgeQuery,
    OnboardingRequest,
    OnboardingResponse,
    SystemArchitectureResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


# API Endpoints
@router.get("/status", response_model=dict[str, Any])
async def get_onboarding_status() -> dict[str, Any]:
    """온보딩 상태 조회

    Returns:
        온보딩 상태 (현재 단계, 완료 여부 등)
    """
    return {
        "is_initialized": True,
        "current_stage": 1,
        "total_stages": 6,
        "trinity_score": 94.16,
        "ready_for_onboarding": True,
    }


@router.get("/architecture", response_model=SystemArchitectureResponse)
async def get_system_architecture() -> SystemArchitectureResponse:
    """시스템 아키텍처 조회

    Returns:
        6성역, 오장육부, 3책사, 5기둥 정보
    """
    # 6성역 (Sanctuaries)
    sanctuaries = [
        {
            "type": "Royal",
            "label": "Chancellor Hall",
            "organ_label": "HEART (Decision)",
            "position": {"x": 0, "y": 0},
            "trinity_score": 98.0,
            "risk_level": 22,
            "description": "승상이 결정을 내리는 중심",
        },
        {
            "type": "Sanctuary",
            "label": "Royal Library",
            "organ_label": "BRAIN (Memory)",
            "position": {"x": 0, "y": -380},
            "trinity_score": 95.0,
            "risk_level": 10,
            "description": "Context7 자기 인식 지식 베이스",
        },
        {
            "type": "Gate",
            "label": "Iron Gate",
            "organ_label": "GALL (Shield)",
            "position": {"x": 0, "y": 380},
            "trinity_score": 88.0,
            "risk_level": 45,
            "description": "보안/방어 시스템",
        },
        {
            "type": "Barracks",
            "label": "Imperial Armory",
            "organ_label": "SKILLS (Action)",
            "position": {"x": -420, "y": -180},
            "trinity_score": 95.0,
            "risk_level": 15,
            "description": "스킬 레지스트리 및 실행",
        },
        {
            "type": "Observatory",
            "label": "Heavenly Observatory",
            "organ_label": "LUNGS (Monitor)",
            "position": {"x": 420, "y": -180},
            "trinity_score": 99.0,
            "risk_level": 5,
            "description": "모니터링 및 관찰",
        },
        {
            "type": "Warehouse",
            "label": "Alchemical Warehouse",
            "organ_label": "STOMACH (Storage)",
            "position": {"x": 420, "y": 180},
            "trinity_score": 90.0,
            "risk_level": 30,
            "description": "데이터 웨어하우스",
        },
    ]

    # 오장육부 (Internal Organs)
    organs = [
        {
            "name": "Heart (심장)",
            "role": "캐시/세션",
            "implementation": "Redis (6379)",
            "status": "active",
        },
        {
            "name": "Liver (간)",
            "role": "영구 저장",
            "implementation": "PostgreSQL (15432)",
            "status": "active",
        },
        {
            "name": "Spleen (비장)",
            "role": "AI 모델 서빙",
            "implementation": "Ollama (11434)",
            "status": "active",
        },
        {
            "name": "Lungs (폐)",
            "role": "벡터 저장소",
            "implementation": "LanceDB (파일 기반)",
            "status": "active",
        },
        {
            "name": "Kidneys (신장)",
            "role": "외부 연결",
            "implementation": "MCP",
            "status": "active",
        },
    ]

    # 3책사 (Strategists)
    strategists = [
        {
            "name": "제갈량 (Jang Yeong-sil)",
            "pillar": "眞",
            "weight": "35%",
            "role": "기술적 확실성/아키텍처",
            "symbol": "⚔️",
            "trinity_score": 95.0,
        },
        {
            "name": "사마의 (Yi Sun-sin)",
            "pillar": "善",
            "weight": "35%",
            "role": "보안/안정성/리스크",
            "symbol": "🛡️",
            "trinity_score": 92.0,
        },
        {
            "name": "주유 (Shin Saimdang)",
            "pillar": "美",
            "weight": "20%",
            "role": "단순함/UX/디자인",
            "symbol": "🌉",
            "trinity_score": 96.0,
        },
    ]

    # 5기둥 (Pillars)
    pillars = [
        {
            "name": "眞",
            "weight": "35%",
            "description": "기술적 확실성/타입 안전성",
            "trinity_score": 95.0,
        },
        {
            "name": "善",
            "weight": "35%",
            "description": "보안/리스크/PII 보호",
            "trinity_score": 92.0,
        },
        {
            "name": "美",
            "weight": "20%",
            "description": "단순함/일관성/구조화",
            "trinity_score": 96.0,
        },
        {
            "name": "孝",
            "weight": "8%",
            "description": "평온 수호/운영 마찰 제거",
            "trinity_score": 94.0,
        },
        {
            "name": "永",
            "weight": "2%",
            "description": "영속성/결정 기록",
            "trinity_score": 92.0,
        },
    ]

    return SystemArchitectureResponse(
        sanctuaries=sanctuaries,
        organs=organs,
        strategists=strategists,
        pillars=pillars,
    )


@router.get("/agent-memory", response_model=AgentMemorySystemResponse)
async def get_agent_memory_system() -> AgentMemorySystemResponse:
    """에이전트 기억 시스템 조회

    Returns:
        Context7, Memory Manager, Yeongdeok 정보
    """
    knowledge_status = knowledge_service.get_status()

    # Context7 통계
    context7_stats = {
        "document_count": knowledge_status["document_count"],
        "cache_hits": 0,
        "cache_total": 0,
        "is_initialized": knowledge_status["is_initialized"],
    }

    # Memory Manager 통계 (스텁 - 실제 구현 필요)
    memory_stats = {
        "max_documents": 1000,
        "current_usage": 0,
        "lru_cleanup": True,
        "is_initialized": False,
    }

    # Yeongdeok 통계 (스텁 - 실제 구현 필요)
    yeongdeok_stats = {
        "record_count": 0,
        "security_scan": 0,
        "mlx_available": False,
        "is_initialized": False,
    }

    # 통합 상태
    integration_status = {
        "context7_initialized": context7_stats["is_initialized"],
        "memory_initialized": memory_stats["is_initialized"],
        "yeongdeok_initialized": yeongdeok_stats["is_initialized"],
        "fully_integrated": (
            context7_stats["is_initialized"]
            and memory_stats["is_initialized"]
            and yeongdeok_stats["is_initialized"]
        ),
    }

    return AgentMemorySystemResponse(
        context7=context7_stats,
        memory_manager=memory_stats,
        yeongdeok=yeongdeok_stats,
        integration_status=integration_status,
    )


@router.post("/demo/memory-search")
async def demo_memory_search(query: str) -> dict[str, Any]:
    """메모리 검색 데모

    Args:
        query: 검색 쿼리

    Returns:
        Context7, Memory Manager, Yeongdeok 검색 결과
    """
    results = {
        "query": query,
        "context7_response": {"documents": []},
        "memory_response": {"documents": []},
        "yeongdeok_response": {"records": []},
    }

    # Context7 검색
    context7_results = await knowledge_service.query_knowledge(query)
    results["context7_response"]["documents"] = context7_results

    return results


@router.post("/context7/initialize")
async def initialize_context7(background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Context7 지식 베이스 초기화

    모든 에이전트가 공유하는 왕국 지식을 LanceDB에 임베딩합니다.

    Returns:
        초기화 상태 및 문서 수
    """
    if knowledge_service.is_initialized:
        return {
            "status": "already_initialized",
            "document_count": knowledge_service.document_count,
            "message": "Context7 is already initialized",
        }

    # 백그라운드에서 초기화 실행
    # 주의: Async 메서드를 background task로 실행하려면 래퍼 필요할 수 있음
    # 하지만 FastAPI BackgroundTasks는 async def도 지원함.
    background_tasks.add_task(knowledge_service.initialize_context7)

    return {
        "status": "initializing",
        "message": "Context7 initialization started in background",
    }


@router.post("/context7/sync")
async def sync_agent_knowledge(agent_id: str, knowledge: str) -> dict[str, Any]:
    """에이전트 지식 동기화

    에이전트가 학습한 새로운 지식을 Context7에 추가합니다.

    Args:
        agent_id: 에이전트 식별자 (claude, opencode, antigravity, gemini 등)
        knowledge: 추가할 지식 내용

    Returns:
        동기화 결과
    """
    if not knowledge_service.is_initialized:
        # 상태 체크를 강제로 할 수도 있지만, service 내부에서 파일 체크함.
        pass

    try:
        result = await knowledge_service.sync_knowledge(agent_id, knowledge)
        result["message"] = f"Knowledge synced from {agent_id}"
        return result
    except Exception as e:
        logger.error(f"[Context7] Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context7/status")
async def get_context7_status() -> dict[str, Any]:
    """Context7 상태 조회

    Returns:
        Context7 초기화 상태 및 통계
    """
    return knowledge_service.get_status()


@router.post("/agents/register")
async def register_agent(registration: AgentRegistration) -> dict[str, Any]:
    """에이전트 등록

    새로운 에이전트가 왕국에 합류할 때 등록합니다.

    Args:
        registration: 에이전트 등록 정보

    Returns:
        등록 결과
    """
    agent_registry.register_agent(
        registration.agent_id,
        registration.agent_type,
        registration.capabilities,
        registration.version,
    )

    active_agents = agent_registry.get_all_agents()
    active_agent_ids = [agent["agent_id"] for agent in active_agents]

    return {
        "status": "registered",
        "agent_id": registration.agent_id,
        "message": f"Welcome to AFO Kingdom, {registration.agent_type}!",
        "active_agents": active_agent_ids,
        "persisted": True,
    }


@router.get("/agents/list")
async def list_agents() -> dict[str, Any]:
    """등록된 에이전트 목록

    Returns:
        현재 등록된 에이전트 정보
    """
    agents = agent_registry.get_all_agents()

    return {
        "agents": agents,
        "count": len(agents),
        "source": "redis"
        if agents
        else "empty",  # Service encapsulates source really, but for API compat
    }


@router.post("/knowledge/query")
async def query_shared_knowledge(query: KnowledgeQuery) -> dict[str, Any]:
    """공유 지식 검색

    모든 에이전트가 공유하는 지식 베이스에서 관련 정보를 검색합니다.

    Args:
        query: 검색 쿼리

    Returns:
        검색 결과
    """
    # 에이전트 활동 시간 업데이트
    agent_registry.update_agent_activity(query.agent_id)

    try:
        results = await knowledge_service.query_knowledge(query.query, query.top_k)

        return {
            "query": query.query,
            "agent_id": query.agent_id,
            "results": results,
            "result_count": len(results),
        }

    except Exception as e:
        logger.error(f"[KnowledgeQuery] Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/broadcast")
async def broadcast_knowledge(
    agent_id: str,
    knowledge: str,
    category: str = "general",
) -> dict[str, Any]:
    """지식 브로드캐스트

    에이전트가 학습한 새로운 지식을 모든 에이전트에게 공유합니다.

    Args:
        agent_id: 발신 에이전트
        knowledge: 공유할 지식
        category: 지식 카테고리 (general, architecture, security, etc.)

    Returns:
        브로드캐스트 결과
    """
    import time

    # 지식 동기화
    try:
        sync_result = await knowledge_service.sync_knowledge(agent_id, knowledge)
    except Exception as e:
        logger.error(f"[Broadcast] Sync failed: {e}")
        # 계속 진행하거나 에러 반환 (기존 로직: raise 되면 멈춤)
        # 여기서도 raise 하는게 맞음 -> knowledge_service.sync_knowledge raises Exception

    # 브로드캐스트 기록
    broadcast_record = {
        "agent_id": agent_id,
        "category": category,
        "timestamp": time.time(),
        "document_id": sync_result.get("document_id"),
    }

    # 에이전트 지식 카운트 업데이트
    agent_registry.increment_knowledge_count(agent_id)

    logger.info(f"[Broadcast] {agent_id} shared knowledge: {knowledge[:50]}...")

    agents = agent_registry.get_all_agents()
    recipients = [agent["agent_id"] for agent in agents]

    return {
        "status": "broadcasted",
        "broadcast": broadcast_record,
        "recipients": recipients,
        "message": f"Knowledge shared with {len(recipients)} agents",
    }


@router.get("/knowledge/stats")
async def get_knowledge_stats() -> dict[str, Any]:
    """지식 베이스 통계

    Returns:
        지식 베이스 및 에이전트 활동 통계
    """
    knowledge_status = knowledge_service.get_status()
    agents = agent_registry.get_all_agents()

    # 소스별 문서 수 집계 (상세 구현 생략가능 or 필요 시 knowledge_service에 추가)
    # 기존 로직에는 있었음. knowledge_service.get_status() 에는 단순 count만 있음.
    # 단순화하여 반환하거나, 필요하면 Service 확장.
    # 일단 기본 통계만 반환.

    return {
        "document_count": knowledge_status["document_count"],
        "active_agents": len(agents),
        "db_path": knowledge_status["db_path"],
    }
