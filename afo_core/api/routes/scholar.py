"""
Scholar Bridge API Routes
구글 클래스룸과 AFO 왕국을 연결하는 학문의 다리
"""

import hashlib
import json
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ics import Calendar, Event

from AFO.julie_cpa_pillar_evaluation import julie_cpa_evaluator
from AFO.utils.standard_shield import shield

router = APIRouter()

# 구글 OAuth 설정 (AFO 철학 준수: 眞善美)
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
]

# 설정 파일 경로들
CLIENT_SECRET_PATH = "config/client_secret.json"  # noqa: S105
TOKEN_STORAGE_PATH = "tokens/jayden_token.json"  # noqa: S105

# 글로벌 상태 관리 (AFO Kingdom 철학)
auth_flows: dict[str, Flow] = {}  # 세션별 OAuth 플로우 저장
connection_status = {"connected": False, "last_sync": None, "error_count": 0, "trinity_score": 0.0}


async def validate_google_credentials() -> bool:
    """구글 인증 정보 유효성 검증 (眞 - Truth)"""
    try:
        if httpx.AsyncClient().get("https://oauth2.googleapis.com/token").status_code != 200:
            return False

        creds = Credentials.from_authorized_user_file(TOKEN_STORAGE_PATH, SCOPES)
        if creds.expired:
            return False

        # Trinity Score 기반 검증
        score = await julie_cpa_evaluator.evaluate_julie_cpa_agent(
            "scholar_bridge",
            {
                "credentials_valid": True,
                "token_expiry": creds.expiry.isoformat() if creds.expiry else None,
            },
        )

        connection_status["trinity_score"] = score.get("consolidated_score", {}).get(
            "trinity_score", 0.0
        )
        return True

    except Exception as e:
        connection_status["error_count"] += 1
        # 善 (Goodness): Shield Log
        import logging

        logging.getLogger(__name__).error(
            f"Credential validation failed: {e}",
            extra={"pillar": "善", "error_type": type(e).__name__},
        )
        return False


@router.get("/auth/google")
@shield(pillar="眞", reraise=True)
@router.get("/auth/callback")
@shield(pillar="善", reraise=True)
@router.get("/sync/json")
async def sync_homework_to_json() -> dict[str, bool | str | float | int | list[dict[str, object]]]:
    """
    구글 클래스룸 숙제를 JSON 포맷으로 동기화
    퀘스트 보드용 실시간 데이터 제공
    """
    try:
        if not connection_status["connected"]:
            return {
                "connected": False,
                "quests": [],
                "message": "구글 클래스룸이 연결되지 않았습니다",
            }

        # 인증 검증
        creds_data = json.load(open(TOKEN_STORAGE_PATH))
        creds = Credentials(
            token=creds_data["token"],
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data["token_uri"],
            client_id=creds_data["client_id"],
            client_secret=creds_data["client_secret"],
            scopes=creds_data["scopes"],
        )

        # API 클라이언트 생성
        service = build("classroom", "v1", credentials=creds)

        # 숙제 데이터 수집
        quest_list = []
        courses = service.courses().list(studentId="me").execute().get("courses", [])

        for course in courses:
            try:
                course_id = course["id"]
                course_name = course["name"]

                # 미완료 숙제 조회
                works = (
                    service.courses()
                    .courseWork()
                    .list(courseId=course_id, courseWorkStates=["PUBLISHED"])
                    .execute()
                    .get("courseWork", [])
                )

                for work in works:
                    # 마감일 정보 추출
                    due_date = work.get("dueDate")
                    due_time = work.get("dueTime", {})

                    if due_date:
                        deadline = datetime(
                            due_date["year"],
                            due_date["month"],
                            due_date["day"],
                            due_time.get("hours", 23),
                            due_time.get("minutes", 59),
                        )

                        # 마감 임박한 숙제만 포함 (AFO 철학: 孝)
                        if deadline > datetime.now():
                            quest_list.append(
                                {
                                    "id": abs(hash(f"{course_id}_{work['id']}")),
                                    "title": f"[{course_name[:15]}] {work['title']}",
                                    "xp": 50,  # 교육적 가치를 고려한 XP
                                    "completed": False,
                                    "source": "google_classroom",
                                    "link": work.get("alternateLink", ""),
                                    "deadline": deadline.isoformat(),
                                    "course_id": course_id,
                                }
                            )

            except HttpError as e:
                # 개별 코스 실패는 전체 실패로 처리하지 않음 (善 - Stability)
                continue

        # 동기화 완료 상태 업데이트
        connection_status["last_sync"] = datetime.now().isoformat()

        # Trinity Score 기반 품질 평가
        evaluation = await julie_cpa_evaluator.evaluate_julie_cpa_agent(
            "scholar_bridge",
            {
                "sync_success": True,
                "quests_found": len(quest_list),
                "courses_processed": len(courses),
            },
        )

        return {
            "connected": True,
            "quests": quest_list,
            "sync_timestamp": connection_status["last_sync"],
            "trinity_score": evaluation.get("consolidated_score", {}).get("trinity_score", 0.0),
            "courses_count": len(courses),
            "message": f"✅ {len(quest_list)}개의 숙제 동기화 완료 (眞善美)",
        }

    except Exception as e:
        connection_status["error_count"] += 1
        connection_status["connected"] = False

        return {
            "connected": False,
            "quests": [],
            "error": f"[방패/Shield] {e!s}",
            "message": "동기화 실패 - 재연결 필요 (永 - Eternity 보장)",
        }


@router.get("/sync/ical")
@router.get("/status")
@router.post("/disconnect")
# 모듈 레벨 초기화
async def initialize_scholar_bridge():
    """Scholar Bridge 초기화 (AFO Kingdom 부팅 시 호출)"""
    try:
        connection_status["connected"] = await validate_google_credentials()
        if connection_status["connected"]:
            print("🎓 Scholar Bridge: 구글 클래스룸 연결 상태 양호")

            # 초기 동기화 테스트
            test_sync = await sync_homework_to_json()
            if test_sync["connected"]:
                print(f"📚 초기 동기화 완료: {len(test_sync['quests'])}개 숙제 발견")
            else:
                print("⚠️ 초기 동기화 실패 - 재연결 필요")
        else:
            print("📖 Scholar Bridge: 인증 필요")

    except Exception as e:
        print(f"❌ [방패/Shield] Scholar Bridge 초기화 실패: {e}")


# FastAPI 앱 시작 시 자동 초기화
@router.on_event("startup")
async def startup_event():
    await initialize_scholar_bridge()


__all__ = ["router", "initialize_scholar_bridge"]
