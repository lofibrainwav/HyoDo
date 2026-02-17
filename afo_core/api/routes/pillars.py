from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from afo_soul_engine.agents.five_pillars_agent import get_five_pillars_agent
from api.compat import html_facade
from api.routes.system_health import get_system_metrics

# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
# mypy: ignore-errors
"""AFO 5기둥 API 엔드포인트 (眞善美孝永)
제3계명: 가족 플랫폼에 5기둥 심기
Phase 23-D: LangFlow 실시간 연동 추가
"""


# Phase 23-D: LangFlow 연동을 위한 에이전트 임포트
try:
    FIVE_PILLARS_AGENT_AVAILABLE = True
except ImportError:
    FIVE_PILLARS_AGENT_AVAILABLE = False

router = APIRouter(prefix="/api/5pillars", tags=["5 Pillars"])


class FivePillarsScores(BaseModel):
    """5기둥 점수 모델"""

    truth: float = Field(..., description="眞 (Truth) 점수", ge=0.0, le=1.0)
    goodness: float = Field(..., description="善 (Goodness) 점수", ge=0.0, le=1.0)
    beauty: float = Field(..., description="美 (Beauty) 점수", ge=0.0, le=1.0)
    serenity: float = Field(..., description="孝 (Serenity) 점수", ge=0.0, le=1.0)
    forever: float = Field(..., description="永 (Forever) 점수", ge=0.0, le=1.0)
    overall: float = Field(..., description="전체 평균 점수", ge=0.0, le=1.0)


class FivePillarsResponse(BaseModel):
    """5기둥 API 응답 모델"""

    scores: FivePillarsScores
    timestamp: str = Field(..., description="조회 시각 (ISO 8601)")
    balance: float = Field(..., description="5기둥 균형 (Max - Min)", ge=0.0)
    status: str = Field(default="success", description="상태")


class LangFlowFivePillarsRequest(BaseModel):
    """LangFlow 실시간 데이터 요청 모델 (Phase 23-D)"""

    data: dict[str, Any] = Field(..., description="LangFlow에서 넘어온 데이터")
    source: str = Field(default="langflow", description="데이터 출처")


class LiveFivePillarsResponse(BaseModel):
    """실시간 5기둥 응답 모델 (Phase 23-D)"""

    timestamp: str = Field(..., description="평가 시각 (ISO 8601)")
    breakdown: dict[str, float] = Field(..., description="5기둥 개별 점수")
    overall: float = Field(..., description="종합 점수")
    balance: float = Field(..., description="균형도 (0-100)")
    health: dict[str, Any] = Field(..., description="건강 상태 평가")
    source: str = Field(..., description="데이터 출처")
    status: str = Field(default="success", description="처리 상태")


async def calculate_five_pillars_from_system() -> dict[str, float]:
    """시스템 메트릭에서 5기둥 점수 계산 (비동기)

    Returns:
        5기둥 점수 딕셔너리

    """
    try:
        # 시스템 메트릭 가져오기

        metrics = await get_system_metrics()

        # 11-오장육부 평균 점수 계산
        organs = metrics.get("organs", [])
        avg_score = sum(org.get("score", 0) for org in organs) / len(organs) if organs else 95.0

        # 5기둥 점수 계산 (시스템 건강도 기반)
        # 眞善美孝는 시스템 건강도에서 계산
        base_score = avg_score / 100.0

        # 永(영원성)은 시스템 안정성과 영구성 보장 수준에서 계산
        # 영구성 = 시스템 안정성 + 코드 품질 + 문서화 수준
        stability_score = min(1.0, base_score + 0.02)  # 안정성 보너스
        forever_score = min(1.0, stability_score + 0.01)  # 영구성 보너스

        return {
            "truth": round(base_score, 3),
            "goodness": round(base_score, 3),
            "beauty": round(base_score * 0.95, 3),  # 아름다움은 약간 낮게
            "serenity": round(base_score + 0.01, 3),  # 평온은 약간 높게
            "forever": round(forever_score, 3),
        }
    except Exception as e:
        # Fallback: 기본 점수 반환
        print(f"⚠️  5기둥 점수 계산 실패, 기본값 사용: {e}")
        return {
            "truth": 0.95,
            "goodness": 0.92,
            "beauty": 0.88,
            "serenity": 0.96,
            "forever": 0.99,
        }


@router.get("/config", summary="5기둥 설정 조회 (SSOT)")
async def get_pillars_config() -> dict[str, Any]:
    """5기둥 설정 조회 (Frontend 동적 설정용)

    Trinity Score: 眞 (Truth) - SSOT(compat.py)에서 정의된 기둥 설정 반환
    """
    try:
        return html_facade.get_philosophy_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설정 조회 실패: {e!s}") from e


@router.get("/current", response_model=FivePillarsResponse, summary="현재 5기둥 점수 조회")
async def get_current_pillars() -> FivePillarsResponse:
    """현재 5기둥 점수 조회

    Frontend의 FamilyDashboard에서 사용합니다.
    시스템 메트릭을 기반으로 실시간 5기둥 점수를 계산합니다.

    Returns:
        5기둥 점수 (眞善美孝永) + Overall + Balance

    """
    try:
        # 5기둥 점수 계산 (비동기)
        scores_dict = await calculate_five_pillars_from_system()

        # Overall 계산 (SSOT: 0.18×眞 + 0.18×善 + 0.12×美 + 0.40×孝 + 0.12×永)
        overall = (
            scores_dict["truth"] * 0.18 + scores_dict["goodness"] * 0.18 + scores_dict["beauty"] * 0.12 + scores_dict["serenity"] * 0.40 + scores_dict["forever"] * 0.12)

        # Balance 계산
        balance = max(scores_dict.values()) - min(scores_dict.values())

        # 응답 생성
        return FivePillarsResponse(
            scores=FivePillarsScores(
                truth=scores_dict["truth"],
                goodness=scores_dict["goodness"],
                beauty=scores_dict["beauty"],
                serenity=scores_dict["serenity"],
                forever=scores_dict["forever"],
                overall=round(overall, 4),
            ),
            timestamp=datetime.now().isoformat(),
            balance=round(balance, 4),
            status="success",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"5기둥 점수 조회 실패: {e!s}") from e


@router.post(
    "/live",
    response_model=LiveFivePillarsResponse,
    summary="LangFlow 실시간 5기둥 평가",
)
async def evaluate_five_pillars_live(
    request: LangFlowFivePillarsRequest,
) -> LiveFivePillarsResponse:
    """LangFlow 실시간 데이터를 받아서 5기둥으로 평가 (Phase 23-D)

    LangFlow 워크플로우에서 데이터를 실시간으로 전송받아
    5기둥 점수로 변환하고 건강 상태를 평가합니다.

    Args:
        request: LangFlow 데이터와 출처 정보

    Returns:
        실시간 5기둥 평가 결과 (Frontend에서 실시간 표시용)

    """
    try:
        if not FIVE_PILLARS_AGENT_AVAILABLE:
            raise HTTPException(status_code=503, detail="5기둥 에이전트를 사용할 수 없습니다")

        # 5기둥 에이전트로 평가
        agent = get_five_pillars_agent()
        result = await agent.evaluate_five_pillars(request.data)

        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=f"5기둥 평가 실패: {result.get('error', 'Unknown error')}",
            )

        # 응답 포맷팅
        return LiveFivePillarsResponse(
            timestamp=result["timestamp"],
            breakdown=result["breakdown"],
            overall=result["overall"],
            balance=result["balance"],
            health=result["health"],
            source=request.source,
            status=result["status"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"실시간 5기둥 평가 실패: {e!s}") from e


# Phase 23-E: Family Hub OS 통합
try:
    FAMILY_HUB_CONFIG = Path(__file__).resolve().parents[2] / "config" / "family_hub.yaml"
    with FAMILY_HUB_CONFIG.open(encoding="utf-8") as f:
        family_config = yaml.safe_load(f)
    FAMILY_HUB_AVAILABLE = True
except Exception as e:
    FAMILY_HUB_AVAILABLE = False
    print(f"⚠️  Family Hub config not available: {e}")


# 실제 데이터 저장소 (Redis로 업그레이드 가능)
# MemberScore 모델 정의 (클래스 사용 전에 미리 정의)
class MemberScore(BaseModel):
    name: str
    truth: float
    goodness: float
    beauty: float
    serenity: float
    forever: float
    message: str = ""


FAMILY_DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "family_hub_data.json"
FAMILY_DATA_FILE.parent.mkdir(exist_ok=True)


def load_family_data() -> dict[str, Any]:
    """가족 데이터를 파일에서 로드"""
    if FAMILY_DATA_FILE.exists():
        try:
            with FAMILY_DATA_FILE.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  가족 데이터 로드 실패: {e}")
    return {}


def save_family_data(data: dict[str, Any]) -> None:
    """가족 데이터를 파일에 저장"""
    try:
        with FAMILY_DATA_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  가족 데이터 저장 실패: {e}")


# 글로벌 가족 데이터 저장소
family_members_data = load_family_data()


@router.get("/family/hub", summary="가족 허브 전체 상태 조회")
async def get_family_hub() -> dict[str, Any]:
    """가족 전체 허브 상태 조회 (Phase 23-E)

    가족 구성원별 상태 + 가족 전체 5기둥 + 미팅 정보 + 목표를 통합 제공

    Returns:
        가족 허브 전체 상태 데이터

    """
    try:
        if not FAMILY_HUB_AVAILABLE:
            raise HTTPException(status_code=503, detail="Family Hub 시스템을 사용할 수 없습니다")

        # 가족 구성원 상태 조회 (현재는 모의 데이터)
        members_status = await get_family_members_status()

        # 가족 전체 5기둥 계산
        family_pillars = await calculate_family_pillars(members_status)

        # 미팅 및 목표 정보
        meetings = get_upcoming_meetings()
        goals = get_family_goals()

        # 오늘의 메시지
        daily_message = generate_daily_family_message(family_pillars)

        response = {
            "timestamp": datetime.now().isoformat(),
            "family": {
                "name": "AFO Family",
                "members_count": len(members_status),
                "pillars": family_pillars,
                "harmony_score": family_pillars.get("overall", 0),
            },
            "members": members_status,
            "meetings": meetings,
            "goals": goals,
            "daily_message": daily_message,
            "status": "active",
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가족 허브 조회 실패: {e!s}") from e


async def get_family_members_status() -> dict[str, Any]:
    """가족 구성원별 상태 조회 (실시간 데이터 연동)"""
    # 1. 정적 페르소나 정보 (기본값)
    base_personas = {
        "jay": {
            "id": "jay",
            "name": "형님",
            "avatar": "👑",
            "role": "commander",
            "today_tasks": ["AFO 최적화", "가족 허브 구축"],
        },
        "julie": {
            "id": "julie",
            "name": "Julie",
            "avatar": "💼",
            "role": "cpa",
            "today_tasks": ["세무 문서 정리", "클라이언트 미팅"],
        },
        "jayden": {
            "id": "jayden",
            "name": "Jayden",
            "avatar": "⚾",
            "role": "kid",
            "today_tasks": ["영어 학습", "야구 연습"],
        },
    }

    # 2. 동적 데이터 가져오기
    dynamic_data = await get_family_hub_data()

    # 3. 데이터 병합
    merged_status = {}

    # Key mapping (Real Data uses Name as key, e.g. "Julie", "형님")
    # We need to map them to IDs "julie", "jay"
    name_to_id = {"Julie": "julie", "형님": "jay", "Jayden": "jayden"}

    for name, data in dynamic_data.items():
        member_id = name_to_id.get(name)
        if not member_id:
            # Handle unknown members if any
            continue

        base = base_personas.get(member_id, {})

        # Determine status based on message or explicit status field if it existed
        # For now, if message contains "WORKING" or "AUDITING", set status accordingly
        msg = data.get("message", "").upper()
        status = "active"
        if "WORKING" in msg:
            status = "WORKING"
        elif "AUDITING" in msg:
            status = "AUDITING"
        elif "IDLE" in msg:
            status = "IDLE"

        merged_status[member_id] = {
            **base,
            "status": status,
            "last_active": data.get("last_update", datetime.now().isoformat()),
            "current_focus": data.get("message", "General"),
            "pillars": {
                "truth": data.get("truth", 0),
                "goodness": data.get("goodness", 0),
                "beauty": data.get("beauty", 0),
                "serenity": data.get("serenity", 0),
                "forever": data.get("forever", 0),
            },
            "message": data.get("message", ""),
            "mood": "productive",  # Placeholder
        }

    return merged_status


async def calculate_family_pillars(members_status: dict[str, Any]) -> dict[str, float]:
    """가족 전체 5기둥 계산"""
    # 각 구성원의 기여도 가중치 적용
    weights = {"jay": 0.4, "julie": 0.35, "jayden": 0.25}

    family_pillars = {
        "truth": 0,
        "goodness": 0,
        "beauty": 0,
        "serenity": 0,
        "forever": 0,
    }

    total_weight = 0
    for member_id, member_data in members_status.items():
        weight = weights.get(member_id, 0.33)
        total_weight += weight

        for pillar, score in member_data["pillars"].items():
            family_pillars[pillar] += score * weight

    # 평균 계산
    for pillar in family_pillars:
        family_pillars[pillar] = round(family_pillars[pillar] / total_weight, 4)

    # 종합 점수 계산
    family_pillars["overall"] = round(
        sum(
            [
                family_pillars["truth"] * 0.30,
                family_pillars["goodness"] * 0.30,
                family_pillars["beauty"] * 0.20,
                family_pillars["serenity"] * 0.15,
                family_pillars["forever"] * 0.05,
            ]
        ),
        4,
    )

    return family_pillars


def get_upcoming_meetings() -> dict[str, Any]:
    """다가오는 가족 미팅 정보"""
    return {
        "daily_standup": {
            "time": "19:00",
            "duration": 15,
            "participants": ["jay", "julie", "jayden"],
            "agenda": ["오늘 하루 요약", "내일 계획 공유"],
        },
        "weekly_review": {
            "time": "일요일 10:00",
            "duration": 30,
            "participants": ["jay", "julie"],
            "agenda": ["이번 주 성과 리뷰", "다음 주 계획 수립"],
        },
    }


def get_family_goals() -> dict[str, Any]:
    """가족 목표 현황"""
    return {
        "family_harmony": {
            "title": "가족 전체 5기둥 점수 95% 이상 유지",
            "target": 0.95,
            "current": 0.966,
            "progress": round((0.966 / 0.95) * 100, 1),
            "status": "excellent",
        },
        "jayden_language": {
            "title": "Jayden 영어 실력 향상",
            "owner": "jayden",
            "target": "intermediate",
            "current": "beginner",
            "progress": 60,
            "status": "on_track",
        },
    }


def generate_daily_family_message(family_pillars: dict[str, float]) -> dict[str, str]:
    """오늘의 가족 메시지 생성"""
    overall = family_pillars.get("overall", 0)

    if overall >= 0.95:
        return {
            "message": "오늘도 가족 모두가 완벽한 조화를 이루고 있어요! 💫",
            "emoji": "✨",
            "type": "excellent",
        }
    elif overall >= 0.90:
        return {
            "message": "가족 모두가 좋은 상태를 유지하고 있어요! 😊",
            "emoji": "😊",
            "type": "good",
        }
    else:
        return {
            "message": "가족 모두가 서로를 챙기며 더 가까워질 수 있어요! 💙",
            "emoji": "💙",
            "type": "supportive",
        }


# 실시간 가족 데이터 관리 API (Phase 23-E+)
@router.post("/family/hub/member/update", summary="가족 구성원 데이터 업데이트")
async def update_member_data(member: MemberScore) -> dict[str, Any]:
    """개별 가족 구성원이 자신의 데이터를 업데이트"""
    global family_members_data

    # 데이터 업데이트
    family_members_data[member.name] = {
        "truth": member.truth,
        "goodness": member.goodness,
        "beauty": member.beauty,
        "serenity": member.serenity,
        "forever": member.forever,
        "message": member.message,
        "last_update": datetime.now().isoformat(),
    }

    # 파일에 저장
    save_family_data(family_members_data)

    print(f"📝 가족 데이터 업데이트: {member.name}")
    return {
        "status": "success",
        "member": member.name,
        "updated_at": datetime.now().isoformat(),
    }


@router.get("/family/hub/data", summary="실시간 가족 허브 데이터 조회")
async def get_family_hub_data() -> dict[str, Any]:
    """실시간 가족 허브 데이터 조회 (프론트엔드에서 사용)"""
    global family_members_data

    # 기본값 설정
    default_data = {
        "형님": {
            "truth": 0.97,
            "goodness": 0.96,
            "beauty": 0.96,
            "serenity": 0.99,
            "forever": 0.998,
            "message": "오늘도 완벽합니다 👑",
            "last_update": datetime.now().isoformat(),
        },
        "Julie": {
            "truth": 0.98,
            "goodness": 0.98,
            "beauty": 0.92,
            "serenity": 0.97,
            "forever": 0.99,
            "message": "세무 마감 끝! 💼",
            "last_update": datetime.now().isoformat(),
        },
        "Jayden": {
            "truth": 0.94,
            "goodness": 0.95,
            "beauty": 0.97,
            "serenity": 0.98,
            "forever": 0.97,
            "message": "영어 100점! 🌟",
            "last_update": datetime.now().isoformat(),
        },
    }

    # 저장된 데이터와 기본값 병합
    current_data = default_data.copy()
    current_data.update(family_members_data)

    # 1시간 이상 된 데이터는 기본값으로 리셋
    for member, data in current_data.items():
        if "last_update" in data:
            last_update = datetime.fromisoformat(data["last_update"])
            if datetime.now() - last_update > timedelta(hours=1):
                current_data[member] = default_data.get(member, data)

    return current_data


import sys as _sys

print("✅ 5기둥 API Router loaded successfully", file=_sys.stderr)
print("   - GET /api/5pillars/current (현재 5기둥 점수 조회)", file=_sys.stderr)
print("   - POST /api/5pillars/live (LangFlow 실시간 평가 - Phase 23-D)", file=_sys.stderr)
print("   - GET /api/5pillars/family/hub (가족 허브 전체 상태 - Phase 23-E)", file=_sys.stderr)
print(
    "   - POST /api/5pillars/family/hub/member/update (가족 구성원 데이터 업데이트)",
    file=_sys.stderr,
)
print("   - GET /api/5pillars/family/hub/data (실시간 가족 허브 데이터)", file=_sys.stderr)
