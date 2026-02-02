# Trinity Score: 93.0 (Phase 30 API Refactoring)
"""Input Server API Endpoints - RESTful API Routes"""

import hashlib
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

# Graceful imports for optional modules
try:
    from input_storage import get_input_history, get_input_statistics, save_input_to_db
except ImportError:
    # Fallback stubs when input_storage is not available
    def get_input_history() -> list[Any]:  # type: ignore[misc]
        return []

    def get_input_statistics() -> dict[str, Any]:  # type: ignore[misc]
        return {"total": 0, "today": 0}

    def save_input_to_db(data: dict[str, Any]) -> bool:  # type: ignore[misc]
        return False


from AFO.config.settings import get_settings

try:
    from api_wallet import APIWallet
except ImportError:
    APIWallet = None  # type: ignore[assignment, misc]

from .templates import get_home_template
from .utils import import_single_key, is_api_wallet_available, parse_env_text


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================
class AddKeyRequest(BaseModel):
    """Request model for adding a single API key via JSON."""

    name: str = Field(..., description="API key name (identifier)")
    provider: str = Field(..., description="Service provider (e.g., openai, anthropic)")
    key: str = Field(..., description="The API key value")
    description: str | None = Field(None, description="Optional description")


class AddKeyResponse(BaseModel):
    """Response model for add_key operations."""

    status: str = Field(..., description="Operation status (success/error)")
    message: str = Field(..., description="Human-readable message")
    name: str | None = Field(None, description="Name of the added key")
    provider: str | None = Field(None, description="Provider of the added key")


class BulkImportRequest(BaseModel):
    """Request model for bulk importing environment variables via JSON."""

    bulk_text: str = Field(..., description="Environment variables text (KEY=VALUE format)")


class BulkImportResponse(BaseModel):
    """Response model for bulk_import operations."""

    status: str = Field(..., description="Operation status (success/partial/error)")
    message: str = Field(..., description="Human-readable summary message")
    counts: dict[str, int] = Field(
        default_factory=dict, description="Counts: success, skipped, failed"
    )
    failed_keys: list[str] = Field(default_factory=list, description="List of failed key names")


# Input Storage 모듈 import
try:
    INPUT_STORAGE_AVAILABLE = True
except ImportError:
    INPUT_STORAGE_AVAILABLE = False
    print("⚠️  WARNING: input_storage module not available. PostgreSQL storage disabled.")

# API Wallet 서버 URL (중앙 설정 사용 - Phase 1 리팩토링)
try:
    settings = get_settings()
    API_WALLET_URL = settings.API_WALLET_URL
except ImportError:
    API_WALLET_URL = "http://localhost:8000"  # fallback


async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "AFO Input Server", "organ": "胃 (Stomach)"}


async def home_page(
    request: Request, success: str | None = None, error: str | None = None
) -> HTMLResponse:
    """
    홈페이지 - API 키 입력 폼

    Query Parameters:
    - success: 성공 메시지
    - error: 에러 메시지
    """
    # 현재 등록된 API 키 목록 조회
    api_keys = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_WALLET_URL}/api/wallet/list")
            if response.status_code == 200:
                data = response.json()
                api_keys = data.get("keys", [])
    except Exception as e:
        print(f"⚠️  API Wallet 조회 실패: {e}")

    # HTML 폼 렌더링
    html_content = get_home_template(success, error, api_keys)
    return HTMLResponse(content=html_content)


async def add_api_key(
    name: str = Form(...),
    provider: str = Form(...),
    key: str = Form(...),
    description: str | None = Form(None),
) -> RedirectResponse:
    """
    API 키 추가 (API Wallet으로 전송 + PostgreSQL 저장)

    Form Parameters:
    - name: API 키 이름
    - provider: 제공자
    - key: API 키 값
    - description: 설명 (선택)
    """
    try:
        # 1. API Wallet으로 전송 (암호화 저장)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{API_WALLET_URL}/api/wallet/add",
                json={
                    "name": name,
                    "provider": provider,
                    "key": key,
                    "description": description or "",
                    "metadata": {
                        "source": "input_server",
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                },
            )

            if response.status_code != 200:
                error_detail = response.json().get("detail", "Unknown error")
                print(f"❌ API 키 저장 실패: {error_detail}")
                return RedirectResponse(url=f"/?error=저장 실패: {error_detail}", status_code=303)

        # 2. PostgreSQL에 메타데이터 저장 (API 키는 제외, 善 - Goodness 원칙)
        if INPUT_STORAGE_AVAILABLE:
            # API 키의 해시값만 저장 (보안)
            key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]

            save_input_to_db(
                category="api_key",
                key=f"api_key_{name}_{key_hash}",
                value=None,  # API 키 값은 저장하지 않음 (보안)
                metadata={
                    "name": name,
                    "provider": provider,
                    "description": description,
                    "key_hash": key_hash,  # 해시만 저장
                    "source": "input_server",
                },
                confidence=1.0,
                source="input_server",
            )

        print(f"✅ API 키 저장 성공: {name} ({provider})")
        return RedirectResponse(
            url=f"/?success=API 키 '{name}'이(가) 성공적으로 저장되었습니다",
            status_code=303,
        )

    except httpx.ConnectError:
        print(f"❌ API Wallet 서버 연결 실패 ({API_WALLET_URL})")
        return RedirectResponse(
            url="/?error=API Wallet 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.",
            status_code=303,
        )
    except Exception as e:
        print(f"❌ API 키 저장 중 에러: {e}")
        return RedirectResponse(url=f"/?error=저장 중 오류가 발생했습니다: {e!s}", status_code=303)


async def api_status() -> dict[str, Any]:
    """
    Input Server 상태 조회

    Returns:
        JSON: 서버 상태 정보
    """
    # API Wallet 연결 확인
    api_wallet_connected = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{API_WALLET_URL}/health")
            api_wallet_connected = response.status_code == 200
    except Exception:
        pass

    # PostgreSQL 연결 확인
    postgres_connected = False
    input_stats: dict[str, Any] = {}
    if INPUT_STORAGE_AVAILABLE:
        try:
            stats = get_input_statistics()
            if stats:
                postgres_connected = True
                input_stats = stats
        except Exception:
            pass

    return {
        "status": "healthy",
        "service": "AFO Input Server",
        "organ": "胃 (Stomach)",
        "port": 4200,
        "api_wallet_url": API_WALLET_URL,
        "api_wallet_connected": api_wallet_connected,
        "postgres_connected": postgres_connected,
        "input_statistics": input_stats,
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def bulk_import(bulk_text: str = Form(...)) -> RedirectResponse:
    """대량 환경 변수 임포트 (Refactored)"""
    try:
        parsed = parse_env_text(bulk_text)
        if not parsed:
            return RedirectResponse(url="/?error=파싱된 환경 변수가 없습니다.", status_code=303)

        # Wallet 인스턴스 준비
        wallet = None
        try:
            wallet = APIWallet()
        except Exception:
            pass

        server_url = API_WALLET_URL if await is_api_wallet_available(API_WALLET_URL) else None

        counts = {"success": 0, "skipped": 0, "failed": 0}
        failed_names = []

        for name, value, service in parsed:
            res = await import_single_key(name, value, service, wallet, server_url)
            if res == "success":
                counts["success"] += 1
            elif res == "skipped":
                counts["skipped"] += 1
            else:
                counts["failed"] += 1
                failed_names.append(f"{name}({res})")

        # 요약 메시지 생성
        summary = []
        if counts["success"]:
            summary.append(f"✅ {counts['success']}개 성공")
        if counts["skipped"]:
            summary.append(f"⚠️ {counts['skipped']}개 스킵")
        if counts["failed"]:
            summary.append(f"❌ {counts['failed']}개 실패")

        result_msg = " | ".join(summary)
        if failed_names:
            result_msg += (
                f" (실패: {', '.join(failed_names[:3])}{'...' if len(failed_names) > 3 else ''})"
            )

        return RedirectResponse(url=f"/?success={result_msg}", status_code=303)

    except Exception as e:
        return RedirectResponse(url=f"/?error=임포트 중 오류: {e!s}", status_code=303)


async def get_history(category: str | None = None, limit: int = 100) -> Any:
    """
    Input 히스토리 조회

    Query Parameters:
    - category: 카테고리 필터 (선택)
    - limit: 최대 조회 개수 (기본값: 100)

    Returns:
        JSON: Input 히스토리 리스트
    """
    if not INPUT_STORAGE_AVAILABLE:
        return JSONResponse(status_code=503, content={"error": "PostgreSQL storage not available"})

    try:
        history = get_input_history(category=category, limit=limit)
        return {"status": "success", "count": len(history), "history": history}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ============================================================================
# JSON-based API Endpoints (RESTful)
# ============================================================================
async def api_add_key(request: AddKeyRequest) -> AddKeyResponse:
    """
    Add a single API key via JSON request.

    This endpoint provides a RESTful JSON interface for adding API keys,
    suitable for programmatic access and API clients.

    Args:
        request: AddKeyRequest with name, provider, key, and optional description

    Returns:
        AddKeyResponse with operation status and details

    Raises:
        HTTPException: On connection errors or API Wallet failures
    """
    try:
        # 1. Send to API Wallet (encrypted storage)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{API_WALLET_URL}/api/wallet/add",
                json={
                    "name": request.name,
                    "provider": request.provider,
                    "key": request.key,
                    "description": request.description or "",
                    "metadata": {
                        "source": "input_server_api",
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                },
            )

            if response.status_code != 200:
                error_detail = response.json().get("detail", "Unknown error")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"API Wallet error: {error_detail}",
                )

        # 2. Save metadata to PostgreSQL (key value excluded for security)
        if INPUT_STORAGE_AVAILABLE:
            key_hash = hashlib.sha256(request.key.encode()).hexdigest()[:16]
            save_input_to_db(
                category="api_key",
                key=f"api_key_{request.name}_{key_hash}",
                value=None,  # Never store the actual key
                metadata={
                    "name": request.name,
                    "provider": request.provider,
                    "description": request.description,
                    "key_hash": key_hash,
                    "source": "input_server_api",
                },
                confidence=1.0,
                source="input_server_api",
            )

        return AddKeyResponse(
            status="success",
            message=f"API key '{request.name}' successfully added",
            name=request.name,
            provider=request.provider,
        )

    except httpx.ConnectError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to API Wallet server at {API_WALLET_URL}",
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add API key: {e!s}",
        ) from e


async def api_bulk_import(request: BulkImportRequest) -> BulkImportResponse:
    """
    Bulk import environment variables via JSON request.

    This endpoint provides a RESTful JSON interface for bulk importing
    multiple API keys from environment variable format text.

    Supported formats:
    - KEY=VALUE
    - KEY: VALUE
    - "KEY": "VALUE"
    - KEY "VALUE"

    Args:
        request: BulkImportRequest with bulk_text containing env var definitions

    Returns:
        BulkImportResponse with counts and details of the import operation

    Raises:
        HTTPException: On parsing errors or when no valid entries found
    """
    try:
        # Parse environment variables from text
        parsed = parse_env_text(request.bulk_text)
        if not parsed:
            raise HTTPException(
                status_code=400,
                detail="No valid environment variables found in the input text",
            )

        # Prepare wallet instance
        wallet = None
        try:
            if APIWallet is not None:
                wallet = APIWallet()
        except Exception:
            pass

        # Check if API server is available
        server_url = API_WALLET_URL if await is_api_wallet_available(API_WALLET_URL) else None

        # Process each key
        counts: dict[str, int] = {"success": 0, "skipped": 0, "failed": 0}
        failed_keys: list[str] = []

        for name, value, service in parsed:
            result = await import_single_key(name, value, service, wallet, server_url)
            if result == "success":
                counts["success"] += 1
            elif result == "skipped":
                counts["skipped"] += 1
            else:
                counts["failed"] += 1
                failed_keys.append(f"{name}({result})")

        # Determine overall status
        if counts["failed"] == len(parsed):
            status = "error"
        elif counts["failed"] > 0:
            status = "partial"
        else:
            status = "success"

        # Build summary message
        summary_parts = []
        if counts["success"]:
            summary_parts.append(f"{counts['success']} succeeded")
        if counts["skipped"]:
            summary_parts.append(f"{counts['skipped']} skipped")
        if counts["failed"]:
            summary_parts.append(f"{counts['failed']} failed")

        return BulkImportResponse(
            status=status,
            message=" | ".join(summary_parts) if summary_parts else "No operations performed",
            counts=counts,
            failed_keys=failed_keys[:10],  # Limit to first 10 for response size
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Bulk import failed: {e!s}",
        ) from e
