# Trinity Score: 90.0 (Established by Chancellor)
# AFO Kingdom Serenity Router
# [Serenity] Autonomous UI Creation API
# 眞95% 善100% 美90% 孝95%


from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from AFO.serenity.creation_loop import serenity_loop

router = APIRouter(prefix="/serenity", tags=["Serenity (GenUI)"])


class SerenityCreateRequest(BaseModel):
    prompt: str


class SerenityCreateResponse(BaseModel):
    code: str
    screenshot_path: str | None
    trinity_score: float
    risk_score: float
    iteration: int
    success: bool
    feedback: str


@router.post("/create", response_model=SerenityCreateResponse)
async def create_ui(request: SerenityCreateRequest) -> SerenityCreateResponse:
    """[Project Serenity] Autonomous UI Creation Engine
    Triggers the GenUI-Playwright-Trinity loop to generate a verified component.
    """
    try:
        result = await serenity_loop.create_ui(request.prompt)
        return SerenityCreateResponse(
            code=result.code,
            screenshot_path=result.screenshot_path,
            trinity_score=result.trinity_score,
            risk_score=result.risk_score,
            iteration=result.iteration,
            success=result.success,
            feedback=result.feedback,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Serenity creation failed: {e!s}") from e


@router.get("/status")
async def get_serenity_status() -> dict[str, Any]:
    """Returns the status of the Serenity sandbox."""
    return {
        "sandbox_active": True,
        "sandbox_path": serenity_loop.sandbox_dir,
        "mode": "autonomous",
    }
