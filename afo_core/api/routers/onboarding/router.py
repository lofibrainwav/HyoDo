"""Onboarding Router - FastAPI 라우터 구현

새로운 에이전트나 사용자가 왕국에 들어왔을 때
시스템 아키텍처를 온보딩하는 FastAPI 엔드포인트들.

Trinity Score: 眞95% 善94% 美96% 孝93% 永92%
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from .base import BaseOnboardingService, OnboardingServiceError
from .models import (
    AgentMemorySystemResponse,
    MemorySearchRequest,
    OnboardingResponse,
    SystemArchitectureResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


class OnboardingService(BaseOnboardingService):
    """온보딩 서비스 구현 (眞: 명확한 구현)"""

    async def get_status(self) -> dict[str, Any]:
        """온보딩 상태 조회 구현"""
        return {
            "is_initialized": True,
            "current_stage": 1,
            "total_stages": 6,
            "trinity_score": 94.16,
            "ready_for_onboarding": True,
        }

    async def get_system_architecture(self) -> dict[str, Any]:
        """시스템 아키텍처 조회 구현"""
        # 6성역 (Sanctuaries)
        sanctuaries = [
            {
                "sanctuary_type": "Royal",
                "label": "Chancellor Hall",
                "organ_label": "HEART (Decision)",
                "position_x": 0.0,
                "position_y": 0.0,
                "scale": 1.3,
                "trinity_score": 98.0,
                "risk_level": 22,
                "description": "승상이 결정을 내리는 중심",
            },
            {
                "sanctuary_type": "Sanctuary",
                "label": "Royal Library",
                "organ_label": "BRAIN (Memory)",
                "position_x": 0.0,
                "position_y": -380.0,
                "scale": 0.95,
                "trinity_score": 95.0,
                "risk_level": 10,
                "description": "Context7 자기 인식 지식 베이스",
            },
            {
                "sanctuary_type": "Gate",
                "label": "Iron Gate",
                "organ_label": "GALL (Shield)",
                "position_x": 0.0,
                "position_y": 380.0,
                "scale": 1.05,
                "trinity_score": 88.0,
                "risk_level": 45,
                "description": "보안/방어 시스템",
            },
            {
                "sanctuary_type": "Barracks",
                "label": "Imperial Armory",
                "organ_label": "SKILLS (Action)",
                "position_x": -420.0,
                "position_y": -180.0,
                "scale": 0.9,
                "trinity_score": 95.0,
                "risk_level": 15,
                "description": "스킬 레지스트리 및 실행",
            },
            {
                "sanctuary_type": "Observatory",
                "label": "Heavenly Observatory",
                "organ_label": "LUNGS (Monitor)",
                "position_x": 420.0,
                "position_y": -180.0,
                "scale": 0.9,
                "trinity_score": 99.0,
                "risk_level": 5,
                "description": "모니터링 및 관찰",
            },
            {
                "sanctuary_type": "Warehouse",
                "label": "Alchemical Warehouse",
                "organ_label": "STOMACH (Storage)",
                "position_x": 420.0,
                "position_y": 180.0,
                "scale": 0.9,
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
                "name": "제갈량 (Zhuge Liang)",
                "pillar": "眞",
                "weight": "35%",
                "role": "기술적 확실성/아키텍처",
                "symbol": "⚔️",
                "trinity_score": 95.0,
            },
            {
                "name": "사마의 (Sima Yi)",
                "pillar": "善",
                "weight": "35%",
                "role": "보안/안정성/리스크",
                "symbol": "🛡️",
                "trinity_score": 92.0,
            },
            {
                "name": "주유 (Zhou Yu)",
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

        return {
            "sanctuaries": sanctuaries,
            "organs": organs,
            "strategists": strategists,
            "pillars": pillars,
        }

    async def get_agent_memory_system(self) -> dict[str, Any]:
        """에이전트 기억 시스템 조회 구현"""
        # Context7 통계
        try:
            # 안전하게 import (실행 중인 서비스에 영향 주지 않음)
            from AFO.services.context7_service import get_context7_instance

            context7 = get_context7_instance()
            context7_stats = {
                "document_count": len(getattr(context7, "_load_document", lambda: [])()),
                "cache_hits": getattr(context7, "_cache_stats", {}).get("hits", 0),
                "cache_total": getattr(context7, "_cache_stats", {}).get("hits", 0)
                + getattr(context7, "_cache_stats", {}).get("misses", 0),
                "is_initialized": True,
            }
        except Exception as e:
            logger.warning(f"Context7 초기화 실패: {e}")
            context7_stats = {
                "document_count": 0,
                "cache_hits": 0,
                "cache_total": 0,
                "is_initialized": False,
            }

        # Memory Manager 통계
        try:
            # 안전하게 import
            from multimodal_rag.memory import MemoryManager

            memory_manager = MemoryManager()
            memory_stats = {
                "max_documents": memory_manager.config.get("max_documents", 1000),
                "current_usage": memory_manager.current_memory_mb,
                "lru_cleanup": memory_manager.config.get("lru_enabled", True),
                "is_initialized": True,
            }
        except Exception as e:
            logger.warning(f"Memory Manager 초기화 실패: {e}")
            memory_stats = {
                "max_documents": 0,
                "current_usage": 0,
                "lru_cleanup": False,
                "is_initialized": False,
            }

        # Yeongdeok 통계 (모듈화 후)
        try:
            # 아직 모듈화되지 않았으므로 placeholder
            yeongdeok_stats = {
                "record_count": 0,
                "security_scan": 0,
                "mlx_available": False,
                "is_initialized": False,
            }
        except Exception as e:
            logger.warning(f"Yeongdeok 초기화 실패: {e}")
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

        return {
            "context7": context7_stats,
            "memory_manager": memory_stats,
            "yeongdeok": yeongdeok_stats,
            "integration_status": integration_status,
        }

    async def demo_memory_search(self, query: str) -> dict[str, Any]:
        """메모리 검색 데모 구현"""
        results = {
            "query": query,
            "context7_response": None,
            "memory_response": None,
            "yeongdeok_response": None,
        }

        # Context7 검색
        try:
            from AFO.services.context7_service import get_context7_instance

            context7 = get_context7_instance()
            context7_results = context7.search(query, limit=5)
            results["context7_response"] = context7_results
        except Exception as e:
            logger.warning(f"Context7 검색 실패: {e}")
            results["context7_response"] = {"error": str(e)}

        # Memory Manager 검색
        try:
            from multimodal_rag.memory import MemoryManager

            memory_manager = MemoryManager()
            # 메모리 검색 로직 (placeholder)
            results["memory_response"] = {"documents": []}
        except Exception as e:
            logger.warning(f"Memory Manager 검색 실패: {e}")
            results["memory_response"] = {"error": str(e)}

        # Yeongdeok 검색 (모듈화 전이므로 placeholder)
        try:
            results["yeongdeok_response"] = {"records": []}
        except Exception as e:
            logger.warning(f"Yeongdeok 검색 실패: {e}")
            results["yeongdeok_response"] = {"error": str(e)}

        return results


# 서비스 싱글톤 인스턴스
_service_instance: OnboardingService | None = None


def get_onboarding_service() -> OnboardingService:
    """온보딩 서비스 싱글톤 인스턴스 반환"""
    global _service_instance
    if _service_instance is None:
        _service_instance = OnboardingService()
    return _service_instance


# API 엔드포인트들
@router.get("/status", response_model=dict[str, Any])
async def get_onboarding_status() -> dict[str, Any]:
    """온보딩 상태 조회

    Returns:
        온보딩 상태 (현재 단계, 완료 여부 등)
    """
    try:
        service = get_onboarding_service()
        return await service.get_status()
    except Exception as e:
        logger.error(f"온보딩 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="온보딩 상태 조회 실패")


@router.get("/architecture", response_model=SystemArchitectureResponse)
async def get_system_architecture() -> SystemArchitectureResponse:
    """시스템 아키텍처 조회

    Returns:
        6성역, 오장육부, 3책사, 5기둥 정보
    """
    try:
        service = get_onboarding_service()
        architecture_data = await service.get_system_architecture()

        return SystemArchitectureResponse(**architecture_data)
    except Exception as e:
        logger.error(f"시스템 아키텍처 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="시스템 아키텍처 조회 실패")


@router.get("/agent-memory", response_model=AgentMemorySystemResponse)
async def get_agent_memory_system() -> AgentMemorySystemResponse:
    """에이전트 기억 시스템 조회

    Returns:
        Context7, Memory Manager, Yeongdeok 정보
    """
    try:
        service = get_onboarding_service()
        memory_data = await service.get_agent_memory_system()

        return AgentMemorySystemResponse(**memory_data)
    except Exception as e:
        logger.error(f"에이전트 기억 시스템 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="에이전트 기억 시스템 조회 실패")


@router.post("/demo/memory-search")
async def demo_memory_search(request: MemorySearchRequest) -> dict[str, Any]:
    """메모리 검색 데모

    Args:
        request: 메모리 검색 요청

    Returns:
        Context7, Memory Manager, Yeongdeok 검색 결과
    """
    try:
        service = get_onboarding_service()
        return await service.demo_memory_search(request.query)
    except Exception as e:
        logger.error(f"메모리 검색 데모 실패: {e}")
        raise HTTPException(status_code=500, detail="메모리 검색 데모 실패")


__all__ = [
    "router",
    "OnboardingService",
    "get_onboarding_service",
]
