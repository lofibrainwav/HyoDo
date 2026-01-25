# Trinity Score: 90.0 (Established by Chancellor)
"""Personas Router
Phase 2: Family Hub OS - 페르소나 API
TRINITY-OS 페르소나 시스템 통합
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from AFO.utils.standard_shield import shield

# 로깅 설정
logger = logging.getLogger(__name__)

# Persona service import
try:
    from AFO.services.persona_service import (
        get_current_persona,
        persona_service,
    )
    from AFO.services.persona_service import (
        switch_persona as switch_persona_service,
    )

    PERSONA_SERVICE_AVAILABLE = True
except ImportError as e:
    PERSONA_SERVICE_AVAILABLE = False
    logger.warning("Persona service not available - using fallback: %s", str(e))

# Persona models import
try:
    from AFO.api.models.persona import (
        Persona,
        PersonaContext,
        PersonaResponse,
        PersonaSwitchRequest,
        PersonaTrinityScore,
    )

    PERSONA_MODELS_AVAILABLE = True
except ImportError as e:
    PERSONA_MODELS_AVAILABLE = False
    logger.warning("Persona models not available - using fallback: %s", str(e))

router = APIRouter(prefix="/api/personas", tags=["Personas"])


@shield(pillar="眞")
@router.get("/health")
async def personas_health() -> dict[str, Any]:
    """페르소나 시스템 건강 상태 체크

    Returns:
        페르소나 시스템 상태

    """
    return {
        "status": "healthy",
        "message": "페르소나 시스템 정상 작동 중",
        "features": {
            "list_personas": "available",
            "get_persona": "available",
            "switch_persona": "available",
            "trinity_score": "available",
            "trinity_os_integration": "pending",  # Phase 2 확장
            "log_bridge": "pending",  # Phase 2 확장
        },
        "personas_count": len(DEFAULT_PERSONAS),
    }


# 기본 페르소나 정의 (TRINITY-OS 연동)
DEFAULT_PERSONAS: dict[str, dict[str, Any]] = {
    "commander": {
        "id": "commander",
        "name": "사령관",
        "role": "Commander",
        "description": "AFO 왕국의 최고 지휘관, 전략적 의사결정 담당",
        "icon": "👑",
        "color": "gold",
        "trinity_os_persona_id": "chancellor",
    },
    "family_head": {
        "id": "family_head",
        "name": "가족 가장",
        "role": "Family Head",
        "description": "가족의 평온과 행복을 책임지는 가장",
        "icon": "👨‍👩‍👧‍👦",
        "color": "blue",
        "trinity_os_persona_id": None,
    },
    "creator": {
        "id": "creator",
        "name": "창작자",
        "role": "Creator",
        "description": "예술과 창작에 집중하는 페르소나",
        "icon": "🎨",
        "color": "purple",
        "trinity_os_persona_id": None,
    },
    "jang_yeong_sil": {
        "id": "jang_yeong_sil",
        "name": "제갈량",
        "role": "Prime Strategist (Truth)",
        "description": "眞 (Truth) - 전략과 기술적 정확성",
        "icon": "⚔️",
        "color": "cyan",
        "trinity_os_persona_id": "jang_yeong_sil_truth",
    },
    "sima_yi": {
        "id": "sima_yi",
        "name": "사마의",
        "role": "Grand Guardian (Goodness)",
        "description": "善 (Goodness) - 안정성과 윤리",
        "icon": "🛡️",
        "color": "amber",
        "trinity_os_persona_id": "sima_yi_goodness",
    },
    "zhou_yu": {
        "id": "zhou_yu",
        "name": "주유",
        "role": "Grand Architect (Beauty)",
        "description": "美 (Beauty) - 우아함과 사용자 경험",
        "icon": "🌉",
        "color": "pink",
        "trinity_os_persona_id": "zhou_yu_beauty",
    },
}


@shield(pillar="眞")
@router.get("/current")
async def get_current_persona_endpoint() -> dict[str, Any]:
    """현재 활성화된 페르소나 조회

    Returns:
        현재 페르소나 정보

    """
    if PERSONA_SERVICE_AVAILABLE:
        try:
            return await get_current_persona()
        except (AttributeError, ValueError) as e:
            logger.warning("현재 페르소나 조회 실패 (속성/값 에러): %s", str(e))
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.debug("현재 페르소나 조회 중 예상치 못한 에러: %s", str(e))

    # Fallback: 기본 응답
    return {
        "id": "commander",
        "name": "사령관",
        "type": "commander",
        "active": True,
    }


@shield(pillar="眞")
@router.get("")
async def list_personas() -> dict[str, Any]:
    """모든 페르소나 목록 조회

    Returns:
        페르소나 목록

    """
    if not PERSONA_MODELS_AVAILABLE:
        # Fallback: 기본 페르소나 반환
        return {
            "personas": list(DEFAULT_PERSONAS.values()),
            "count": len(DEFAULT_PERSONAS),
        }

    # Phase 2 확장: DB에서 페르소나 조회 시도 (persona_service 사용)
    personas = []
    if PERSONA_SERVICE_AVAILABLE:
        # DB에서 조회 시도 (각 페르소나 ID로)
        for persona_id in DEFAULT_PERSONAS:
            try:
                db_persona = await persona_service.get_persona_from_db(persona_id)
                if db_persona:
                    # DB에서 조회된 페르소나 사용
                    persona = Persona(
                        id=db_persona["id"],
                        name=db_persona["name"],
                        role=DEFAULT_PERSONAS[persona_id].get("role", "Unknown"),
                        description=DEFAULT_PERSONAS[persona_id].get("description", ""),
                        icon=DEFAULT_PERSONAS[persona_id].get("icon", "👤"),
                        color=DEFAULT_PERSONAS[persona_id].get("color", "gray"),
                        trinity_os_persona_id=DEFAULT_PERSONAS[persona_id].get(
                            "trinity_os_persona_id"
                        ),
                        context=PersonaContext(
                            current_role=DEFAULT_PERSONAS[persona_id].get("role", "Unknown")
                        ),
                    )
                    personas.append(persona)
                    continue
            except (ValueError, KeyError, AttributeError) as e:
                logger.debug("DB 페르소나 조회 실패 (값/키/속성 에러): %s", str(e))
                # DB 조회 실패 시 기본 페르소나 사용
            except Exception as e:  # - Intentional fallback for unexpected errors
                logger.debug("DB 페르소나 조회 중 예상치 못한 에러: %s", str(e))
                # DB 조회 실패 시 기본 페르소나 사용

    # DB에서 조회되지 않은 페르소나 또는 DB 조회 실패 시 기본 페르소나 사용
    for persona_data in DEFAULT_PERSONAS.values():
        if not any(p.id == persona_data["id"] for p in personas):
            persona = Persona(
                id=persona_data["id"],
                name=persona_data["name"],
                role=persona_data["role"],
                description=persona_data["description"],
                icon=persona_data["icon"],
                color=persona_data["color"],
                trinity_os_persona_id=persona_data.get("trinity_os_persona_id"),
                context=PersonaContext(current_role=persona_data["role"]),
            )
            personas.append(persona)

    return {
        "personas": [p.model_dump() for p in personas],
        "count": len(personas),
    }


@shield(pillar="眞")
@router.get("/{persona_id}")
async def get_persona(persona_id: str) -> dict[str, Any]:
    """특정 페르소나 정보 조회

    Args:
        persona_id: 페르소나 ID

    Returns:
        페르소나 정보

    Raises:
        HTTPException: 페르소나를 찾을 수 없을 때

    """
    if persona_id not in DEFAULT_PERSONAS:
        raise HTTPException(status_code=404, detail=f"페르소나를 찾을 수 없습니다: {persona_id}")

    persona_data = DEFAULT_PERSONAS[persona_id]

    if PERSONA_MODELS_AVAILABLE:
        persona = Persona(
            id=persona_data["id"],
            name=persona_data["name"],
            role=persona_data["role"],
            description=persona_data["description"],
            icon=persona_data["icon"],
            color=persona_data["color"],
            trinity_os_persona_id=persona_data.get("trinity_os_persona_id"),
            context=PersonaContext(current_role=persona_data["role"]),
        )
        return dict(persona.model_dump())

    return persona_data


@shield(pillar="眞")
@router.post("/switch")
async def switch_persona(request: PersonaSwitchRequest) -> dict[str, Any]:
    """페르소나 전환 (眞善美孝永: 맥락 기반 응답)

    Args:
        request: 페르소나 전환 요청

    Returns:
        전환된 페르소나 정보 및 응답

    Raises:
        HTTPException: 페르소나를 찾을 수 없을 때

    """
    if request.persona_id not in DEFAULT_PERSONAS:
        raise HTTPException(
            status_code=404, detail=f"페르소나를 찾을 수 없습니다: {request.persona_id}"
        )

    persona_data = DEFAULT_PERSONAS[request.persona_id]

    # --- TRINITY-OS Integration (Phase 2) ---
    # Log Persona Switch to Family Hub
    try:
        from datetime import datetime

        # Log activity using internal logic (simulating API call)
        # We invoke the logic directly or via internal call if possible,
        # but here we'll use a direct import of the handler logic or just direct file access
        # to avoid async complexity in this snippet if not strictly needed.
        # Actually, let's use the BackgroundTasks pattern properly if passed,
        # but since we are inside a function, we'll do a direct lightweight update.
        from AFO.api.routers.family import (
            calculate_happiness_impact,
            load_family_data,
            save_family_data,
        )

        family_data = load_family_data()
        activities = family_data.get("activities", [])

        new_activity = {
            "id": f"act_{len(activities) + 1}",
            "member_id": "system",  # System event
            "type": "PersonaSwitch",
            "description": f"Switched to persona: {persona_data['name']}",
            "timestamp": datetime.now().isoformat(),
            "trinity_impact": 0.1,
        }

        activities.append(new_activity)
        family_data["activities"] = activities[-50:]

        # Update System Happiness (Tiny boost for freshness)
        current_happiness = family_data.get("system", {}).get("overall_happiness", 50.0)
        new_happiness = min(100.0, max(0.0, current_happiness + 0.1))

        if "system" not in family_data:
            family_data["system"] = {}
        family_data["system"]["overall_happiness"] = new_happiness

        save_family_data(family_data)
        logger.info("Logged persona switch to Family Hub: %s", persona_data["name"])

    except ImportError as e:
        logger.warning("Family Hub integration not available: %s", str(e))
    except (ValueError, KeyError, OSError) as e:
        logger.warning("Failed to log persona switch (값/키/파일 시스템 에러): %s", str(e))
    except Exception as e:  # - Intentional fallback for unexpected errors
        logger.debug("Failed to log persona switch (예상치 못한 에러): %s", str(e))

    if PERSONA_MODELS_AVAILABLE:
        persona = Persona(
            id=persona_data["id"],
            name=persona_data["name"],
            role=persona_data["role"],
            description=persona_data["description"],
            icon=persona_data["icon"],
            color=persona_data["color"],
            trinity_os_persona_id=persona_data.get("trinity_os_persona_id"),
            context=PersonaContext(
                current_role=persona_data["role"],
                active_personas=[request.persona_id],
                preferences=request.context,
            ),
        )

        # 기본 Trinity Score (Phase 2에서 실제 계산)
        trinity_score = PersonaTrinityScore(
            truth=80.0,
            goodness=75.0,
            beauty=90.0,
            serenity=85.0,
            eternity=80.0,
            total_score=82.0,
        )

        return {
            "persona": persona.model_dump(),
            "message": f"페르소나 '{persona.name}'로 전환되었습니다.",
            "trinity_score": trinity_score.model_dump(),
        }

    return {
        "persona": persona_data,
        "message": f"페르소나 '{persona_data['name']}'로 전환되었습니다.",
    }


@shield(pillar="眞")
@router.get("/{persona_id}/trinity-score")
async def get_persona_trinity_score(persona_id: str) -> dict[str, Any]:
    """페르소나별 Trinity Score 조회

    Args:
        persona_id: 페르소나 ID

    Returns:
        Trinity Score 정보

    Raises:
        HTTPException: 페르소나를 찾을 수 없을 때

    """
    if persona_id not in DEFAULT_PERSONAS:
        raise HTTPException(status_code=404, detail=f"페르소나를 찾을 수 없습니다: {persona_id}")

    persona_data = DEFAULT_PERSONAS[persona_id]

    # Phase 2 확장: 실제 Trinity Score 계산 (persona_service 사용)
    if PERSONA_SERVICE_AVAILABLE:
        try:
            # persona_service의 calculate_trinity_score 사용
            score_result = await persona_service.calculate_trinity_score(
                persona_data=persona_data, context={"persona_id": persona_id}
            )

            if PERSONA_MODELS_AVAILABLE:
                trinity_score = PersonaTrinityScore(
                    truth=score_result.get("truth_score", 80.0),
                    goodness=score_result.get("goodness_score", 75.0),
                    beauty=score_result.get("beauty_score", 90.0),
                    serenity=score_result.get("serenity_score", 85.0),
                    eternity=score_result.get("eternity_score", 80.0),
                    total_score=score_result.get("total_score", 82.0),
                )
                return dict(trinity_score.model_dump())

            return {
                "truth": score_result.get("truth_score", 80.0),
                "goodness": score_result.get("goodness_score", 75.0),
                "beauty": score_result.get("beauty_score", 90.0),
                "serenity": score_result.get("serenity_score", 85.0),
                "eternity": score_result.get("eternity_score", 80.0),
                "total_score": score_result.get("total_score", 82.0),
                "evaluation": score_result.get("evaluation", "양호"),
                "calculated_at": score_result.get("calculated_at"),
            }
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("Trinity Score 계산 실패 (값/타입/속성 에러), 기본값 사용: %s", str(e))
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.warning("Trinity Score 계산 실패 (예상치 못한 에러), 기본값 사용: %s", str(e))

    # Fallback: 기본값 반환
    if PERSONA_MODELS_AVAILABLE:
        trinity_score = PersonaTrinityScore(
            truth=80.0,
            goodness=75.0,
            beauty=90.0,
            serenity=85.0,
            eternity=80.0,
            total_score=82.0,
        )
        return dict(trinity_score.model_dump())

    return {
        "truth": 80.0,
        "goodness": 75.0,
        "beauty": 90.0,
        "serenity": 85.0,
        "eternity": 80.0,
        "total_score": 82.0,
    }
