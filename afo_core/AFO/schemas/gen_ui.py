# Trinity Score: 90.0 (Established by Chancellor)
"""GenUI Schemas (GenUIRequest, GenUIResponse)
Phase 9: Self-Expanding Kingdom (Serenity)

Defines the data structures for autonomous UI generation.
Truth (眞): Strict checking of prompt and requirements.
"""

from typing import Any

from pydantic import BaseModel, Field

from AFO.api.models.persona import PersonaTrinityScore as TrinityScore


class GenUIRequest(BaseModel):
    """Request to generate a new UI component."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt": "A modern majestic dashboard card",
                "component_name": "MajesticCard",
                "trinity_threshold": 0.8,
            }
        },
        "strict": True,
    }

    prompt: str = Field(..., description="Natural language description of the component")
    component_name: str = Field(..., description="Desired React component name (PascalCase)")
    context: dict[str, Any] | None = Field(
        default_factory=dict, description="Additional context or props"
    )
    trinity_threshold: float = Field(
        0.8, description="Minimum Trinity Score required for auto-approval"
    )


class GenUIResponse(BaseModel):
    """Response containing the generated component."""

    component_id: str = Field(..., description="Unique ID for the generated artifact")
    component_name: str = Field(..., description="React component name")
    code: str = Field(..., description="The generated React/TypeScript code")
    description: str = Field(..., description="Summary of what was built")
    trinity_score: TrinityScore = Field(..., description="Self-assessed Trinity Score")
    risk_score: int = Field(0, description="Risk assessment (0-100), automated")
    status: str = Field("draft", description="Union[Union[draft, approved], rejected]")
    error: str | None = None
