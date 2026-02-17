# Trinity Score: 90.0 (Established by Chancellor)
"""Modal Data Router for AFO Kingdom
모달 데이터 API - Dynamic modal content management.

Provides endpoints for fetching and managing modal dialog content
for the dashboard UI components.
"""

import logging
from datetime import UTC, datetime
from typing import Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from AFO.utils.standard_shield import shield

logger = logging.getLogger("AFO.ModalData")
router = APIRouter(tags=["Modal Data"])


# --- Pydantic Models ---


class ModalContent(BaseModel):
    """Modal content structure."""

    id: str
    title: str
    content: str
    modal_type: str = Field(default="info", description="info, warning, error, success, form")
    actions: list[dict[str, str]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class CreateModalRequest(BaseModel):
    """Request to create modal content."""

    id: str
    title: str
    content: str
    modal_type: str = "info"
    actions: list[dict[str, str]] = Field(default_factory=list)


# --- In-Memory Storage with Default Modals ---
_modals: dict[str, ModalContent] = {
    "welcome": ModalContent(
        id="welcome",
        title="Welcome to AFO Kingdom",
        content="승상 시스템이 활성화되었습니다. 眞善美孝永 5기둥 철학을 기반으로 운영됩니다.",
        modal_type="info",
        actions=[{"label": "시작하기", "action": "close"}],
    ),
    "trinity_info": ModalContent(
        id="trinity_info",
        title="Trinity Score 안내",
        content="Trinity Score = 0.18×眞 + 0.18×善 + 0.12×美 + 0.40×孝 + 0.12×永",
        modal_type="info",
        actions=[{"label": "확인", "action": "close"}],
    ),
    "dry_run_warning": ModalContent(
        id="dry_run_warning",
        title="⚠️ DRY RUN 모드",
        content="현재 DRY RUN 모드로 실행 중입니다. 실제 변경사항은 적용되지 않습니다.",
        modal_type="warning",
        actions=[
            {"label": "계속", "action": "close"},
            {"label": "WET RUN으로 전환", "action": "switch_wet"},
        ],
    ),
}


# --- Endpoints ---


@shield(pillar="善")
@router.get("/health")
async def modal_health() -> dict[str, Any]:
    """Check Modal Data service health."""
    return {
        "status": "healthy",
        "service": "Modal Data",
        "modals_count": len(_modals),
        "default_modals": ["welcome", "trinity_info", "dry_run_warning"],
    }


@shield(pillar="善")
@router.get("/list")
async def list_modals() -> dict[str, Any]:
    """List all available modal IDs."""
    return {
        "modals": list(_modals.keys()),
        "count": len(_modals),
    }


@shield(pillar="善")
@router.get("/{modal_id}", response_model=ModalContent)
async def get_modal(modal_id: str) -> ModalContent:
    """Get modal content by ID."""
    if modal_id not in _modals:
        raise HTTPException(status_code=404, detail=f"Modal {modal_id} not found")
    return _modals[modal_id]


@shield(pillar="善")
@router.post("/", response_model=ModalContent)
async def create_modal(request: CreateModalRequest) -> ModalContent:
    """Create or update modal content."""
    modal = ModalContent(
        id=request.id,
        title=request.title,
        content=request.content,
        modal_type=request.modal_type,
        actions=request.actions,
    )

    _modals[request.id] = modal
    logger.info(f"📦 Modal created/updated: {request.id}")
    return modal


@shield(pillar="善")
@router.delete("/{modal_id}")
async def delete_modal(modal_id: str) -> dict[str, str]:
    """Delete a modal by ID."""
    if modal_id not in _modals:
        raise HTTPException(status_code=404, detail=f"Modal {modal_id} not found")

    del _modals[modal_id]
    return {"status": "deleted", "modal_id": modal_id}
