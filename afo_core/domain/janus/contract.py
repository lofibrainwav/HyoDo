# Trinity Score: 90.0 (Established by Chancellor)
from typing import Literal

from pydantic import BaseModel, Field


class BBox(BaseModel):
    """Normalized Bounding Box (0.0 to 1.0)"""

    x: float = Field(..., ge=0.0, le=1.0, description="X coordinate (0-1)")
    y: float = Field(..., ge=0.0, le=1.0, description="Y coordinate (0-1)")
    w: float = Field(..., ge=0.0, le=1.0, description="Width (0-1)")
    h: float = Field(..., ge=0.0, le=1.0, description="Height (0-1)")


class VisualAction(BaseModel):
    """Step 1: Action Contract (SSOT)
    Defines the strict schema for Visual Agent actions.
    """

    type: Literal["click", "type", "scroll", "wait", "goto", "done"] = Field(
        ..., description="The type of action to perform"
    )
    bbox: BBox | None = Field(
        None, description="Target coordinates for the action (required for click)"
    )
    text: str | None = Field(None, description="Text to type or reason for waiting")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model's confidence score")
    why: str = Field(..., description="Reasoning for this specific action (Chain of Thought)")
    safety: Literal["safe", "confirm", "block"] = Field(
        "safe", description="Safety assessment of the action"
    )


class VisualPlan(BaseModel):
    """The full plan output from the Visual Agent"""

    goal: str = Field(..., description="The high-level goal being achieved")
    actions: list[VisualAction] = Field(
        ..., max_length=5, description="List of atomic actions (max 5 per turn)"
    )
    stop: bool = Field(False, description="Whether the task is considered complete")
    summary: str = Field(..., description="Brief summary of the plan")
