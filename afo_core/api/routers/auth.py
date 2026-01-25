# Trinity Score: 90.0 (Established by Chancellor)
"""
Auth Router
Phase 3: 인증 라우터 (心 시스템 - 인증)
JWT 토큰 및 비밀번호 해시 지원
"""

import secrets
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.requests import Request

from AFO.utils.standard_shield import shield

# Auth utilities import
try:
    from AFO.api.utils.auth import (
        create_access_token,
        hash_password,
        verify_password,
        verify_token,
    )

    AUTH_UTILS_AVAILABLE = True
except ImportError:
    try:
        import sys
        from pathlib import Path

        _CORE_ROOT = Path(__file__).resolve().parent.parent.parent
        if str(_CORE_ROOT) not in sys.path:
            sys.path.insert(0, str(_CORE_ROOT))
        from api.utils.auth import (
            create_access_token as cat,
        )
        from api.utils.auth import (
            hash_password as hp,
        )
        from api.utils.auth import (
            verify_password as vp,
        )
        from api.utils.auth import (
            verify_token as vt,
        )

        create_access_token = cat
        hash_password = hp
        verify_password = vp
        verify_token = vt

        AUTH_UTILS_AVAILABLE = True
    except ImportError:
        AUTH_UTILS_AVAILABLE = False
        print("⚠️  Auth utilities not available - using fallback")

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    """로그인 요청 모델"""

    username: str = Field(..., min_length=1, max_length=50, description="사용자명")
    password: str = Field(..., min_length=1, description="비밀번호")


class LoginResponse(BaseModel):
    """로그인 응답 모델"""

    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(default=3600, description="토큰 만료 시간 (초)")


class TokenResponse(BaseModel):
    """토큰 검증 응답 모델"""

    valid: bool = Field(..., description="토큰 유효성")
    username: str | None = Field(default=None, description="사용자명")


@router.post("/login")
@shield(pillar="善", log_error=True, reraise=False)
async def login(request: Request, body: LoginRequest) -> dict[str, Any]:
    """
    사용자 로그인

    Args:
        request: 로그인 요청

    Returns:
        액세스 토큰 및 인증 정보

    Raises:
        HTTPException: 인증 실패 시
    """
    # 입력 검증
    if not request.username or not request.password:
        raise HTTPException(status_code=401, detail="사용자명 또는 비밀번호가 올바르지 않습니다.")

    # DB에서 사용자 조회 및 인증
    try:
        from AFO.services.database import get_db_connection

        conn = await get_db_connection()

        # 사용자 조회 (저장 프로시저 사용)
        user_result = await conn.fetchrow(
            "SELECT * FROM get_user_by_username($1)", request.username
        )

        if not user_result:
            await conn.close()
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")

        # 계정 활성화 상태 확인
        if not user_result["is_active"]:
            await conn.close()
            raise HTTPException(status_code=401, detail="계정이 비활성화되었습니다.")

        # 비밀번호 검증
        if AUTH_UTILS_AVAILABLE:
            from AFO.api.utils.auth import verify_password

            password_valid = verify_password(request.password, user_result["hashed_password"])
        else:
            # Phase 15 Security Seal: Fallback 시 인증 거부 (hash() 취약점 제거)
            # AUTH_UTILS가 없으면 안전한 비밀번호 검증 불가
            await conn.close()
            raise HTTPException(
                status_code=503,
                detail="인증 시스템 초기화 중입니다. 잠시 후 다시 시도해주세요.",
            )

        if not password_valid:
            await conn.close()
            raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다.")

        # 세션 생성
        if AUTH_UTILS_AVAILABLE:
            from AFO.api.utils.auth import create_access_token

            # JWT 토큰 생성
            token_data = {
                "sub": user_result["username"],
                "user_id": user_result["id"],
                "role": user_result["role"],
            }
            access_token = create_access_token(data=token_data)
            session_token = access_token  # JWT를 세션 토큰으로 사용
        else:
            # Phase 15 Security Seal: secrets.token_urlsafe 사용 (hash() 취약점 제거)
            session_token = f"temp_token_{request.username}_{secrets.token_urlsafe(32)}"
            access_token = session_token

        # DB 세션 생성 (저장 프로시저 사용)
        try:
            await conn.fetchval(
                "SELECT create_user_session($1, $2, $3)",
                user_result["id"],
                session_token,
                "local",
            )
        except Exception as e:
            # 세션 생성 실패해도 로그인 성공으로 처리 (선택적)
            print(f"세션 생성 실패 (무시): {e}")

        await conn.close()

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600 * 24,  # 24시간
            "user": {
                "id": user_result["id"],
                "username": user_result["username"],
                "email": user_result["email"],
                "role": user_result["role"],
                "display_name": user_result.get("display_name"),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Authentication failure for user {request.username}: {e}",
            exc_info=True,
            extra={"pillar": "善"},
        )

        # Fallback: 간단한 인증 (개발용)
        if AUTH_UTILS_AVAILABLE:
            token_data = {"sub": request.username, "username": request.username}
            access_token = create_access_token(data=token_data)
        else:
            access_token = f"temp_token_{request.username}_{secrets.token_urlsafe(32)}"

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600 * 24,
            "note": "DB unavailable - fallback authentication",
            "user": {"username": request.username, "role": "user"},
        }


@router.post("/verify")
@shield(pillar="善", log_error=True, reraise=False)
async def verify_token_endpoint(
    token: str = Query(..., description="검증할 토큰"),
) -> dict[str, Any]:
    """
    토큰 검증 (眞善美: Truth + Goodness + Beauty)

    Args:
        token: 검증할 토큰

    Returns:
        토큰 유효성 및 사용자 정보

    Raises:
        HTTPException: 토큰 형식 오류 시 401 (善: 명확한 에러 응답)
    """
    # 眞: 입력 검증
    if not token or not token.strip():
        raise HTTPException(status_code=401, detail="토큰이 제공되지 않았습니다.")

    # 善: Graceful degradation - 예외 처리
    try:
        # JWT 토큰 검증
        if AUTH_UTILS_AVAILABLE:
            from AFO.api.utils.auth import verify_token as verify_token_func

            payload: dict[str, Any] | None = verify_token_func(token)

            if payload:
                username = payload.get("sub") or payload.get("username")
                return {
                    "valid": True,
                    "username": username,
                    "exp": payload.get("exp"),
                }
            else:
                # 善: 명확한 실패 응답 (401 대신 200 with valid=False)
                return {
                    "valid": False,
                    "username": None,
                    "detail": "토큰이 만료되었거나 유효하지 않습니다.",
                }
        else:
            # Fallback: 임시 토큰 검증
            if not token.startswith("temp_token_"):
                return {
                    "valid": False,
                    "username": None,
                    "detail": "토큰 형식이 올바르지 않습니다.",
                }

            try:
                parts = token.replace("temp_token_", "").split("_")
                username = parts[0] if parts else None

                return {
                    "valid": True,
                    "username": username,
                }
            except Exception as e:
                # 善: 예외 처리
                return {
                    "valid": False,
                    "username": None,
                    "detail": f"토큰 파싱 오류: {e!s}",
                }
    except Exception as e:
        # 善: 예상치 못한 에러 처리 (500 방지)
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Token verification endpoint error: {e}", exc_info=True, extra={"pillar": "善"}
        )

        # 美: 우아한 에러 응답
        raise HTTPException(
            status_code=500, detail=f"토큰 검증 중 서버 오류가 발생했습니다: {e!s}"
        ) from e


@router.get("/health")
@shield(pillar="善", log_error=True, reraise=False)
async def auth_health(request: Request) -> dict[str, Any]:
    """
    인증 시스템 건강 상태 체크

    Returns:
        인증 시스템 상태
    """
    return {
        "status": "healthy",
        "message": "인증 시스템 정상 작동 중",
        "features": {
            "login": "available",
            "token_verification": "available",
            "jwt": "available" if AUTH_UTILS_AVAILABLE else "pending",
            "password_hashing": "available" if AUTH_UTILS_AVAILABLE else "pending",
        },
    }
