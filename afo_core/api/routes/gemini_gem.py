# Trinity Score: 90.0 (Established by Chancellor)
"""
Gemini Gem API Router - Chat Widget Backend

Provides REST API endpoints for the Gemini Gem chat widget.
Emulates Gem behavior using Gemini API with system_instruction.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.gemini_gem_service import gemini_gem_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gemini-gem", tags=["Gemini Gem"])


# --- Pydantic Models ---


class GemChatRequest(BaseModel):
    """Chat message request for Gemini Gem."""

    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    session_id: str | None = Field(
        default=None, description="Session ID for conversation continuity"
    )


class GemChatResponse(BaseModel):
    """Chat message response from Gemini Gem."""

    success: bool
    response: str | None = None
    error: str | None = None
    session_id: str
    timestamp: str


class GemSessionInfo(BaseModel):
    """Session information."""

    session_id: str
    created_at: str
    updated_at: str
    message_count: int


class GemStatusResponse(BaseModel):
    """Service status response."""

    available: bool
    model: str
    active_sessions: int
    max_sessions: int
    gem_url: str


# --- Endpoints ---


@router.post("/chat", response_model=GemChatResponse, summary="Send chat message to Gem")
async def gem_chat(request: GemChatRequest) -> GemChatResponse:
    """
    Send a message to the Gemini Gem and receive a response.

    - Maintains conversation history per session
    - Uses AFO Kingdom system instruction for Gem emulation
    - Supports Korean and English
    """
    result = await gemini_gem_service.chat(message=request.message, session_id=request.session_id)

    return GemChatResponse(
        success=result.get("success", False),
        response=result.get("response"),
        error=result.get("error"),
        session_id=result.get("session_id", "unknown"),
        timestamp=result.get("timestamp", datetime.now().isoformat()),
    )


@router.post("/clear/{session_id}", summary="Clear session history")
async def clear_session(session_id: str) -> dict[str, bool | str]:
    """Clear the conversation history for a specific session."""
    success = gemini_gem_service.clear_session(session_id)
    if success:
        return {"success": True, "message": f"Session {session_id} cleared"}
    raise HTTPException(status_code=404, detail=f"Session {session_id} not found")


@router.get("/session/{session_id}", response_model=GemSessionInfo, summary="Get session info")
async def get_session_info(session_id: str) -> GemSessionInfo:
    """Get information about a specific conversation session."""
    info = gemini_gem_service.get_session_info(session_id)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return GemSessionInfo(
        session_id=info["session_id"],
        created_at=info["created_at"],
        updated_at=info["updated_at"],
        message_count=info["message_count"],
    )


@router.get("/status", response_model=GemStatusResponse, summary="Get service status")
async def get_status() -> GemStatusResponse:
    """Get the current status of the Gemini Gem service."""
    status = gemini_gem_service.get_service_status()
    return GemStatusResponse(
        available=status["available"],
        model=status["model"],
        active_sessions=status["active_sessions"],
        max_sessions=status["max_sessions"],
        gem_url=status["gem_url"],
    )


@router.get("/health", summary="Health check")
async def health_check() -> dict[str, str | bool]:
    """Health check endpoint for the Gemini Gem service."""
    status = gemini_gem_service.get_service_status()
    return {
        "status": "healthy" if status["available"] else "degraded",
        "gemini_available": status["available"],
        "model": status["model"],
    }
