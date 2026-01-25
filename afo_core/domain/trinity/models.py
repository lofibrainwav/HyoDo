from enum import Enum

from pydantic import BaseModel, Field


class StrategistType(str, Enum):
    ZHUGE_LIANG = "jang_yeong_sil"  # Truth (眞) - Logic, Facts, Code
    SIMA_YI = "sima_yi"  # Goodness (善) - Risk, Safety, Conservative
    ZHOU_YU = "zhou_yu"  # Beauty (美) - UX, Narrative, Empathy


class StrategistOpinion(BaseModel):
    persona: StrategistType
    analysis: str = Field(..., description="The core analysis content from this strategist.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in this opinion.")
    key_points: list[str] = Field(default_factory=list, description="Bulleted key takeaways.")


class ReflectionPoint(BaseModel):
    pillar: str = Field(..., description="The Trinity pillar affected (眞/善/美/孝/永)")
    insight: str = Field(..., description="Metacognitive insight or observation.")
    action_item: str | None = Field(None, description="Recommended course of correction.")


class MetacognitiveAuditResult(BaseModel):
    target: str = Field(..., description="The component or phase being audited.")
    reflections: list[ReflectionPoint]
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    metacognitive_delta: float = Field(..., description="Change in self-awareness or score.")


class DebateResolution(BaseModel):
    query: str
    opinions: list[StrategistOpinion]
    synthesis: str = Field(..., description="Final harmonized answer combining all perspectives.")
    final_trinity_score: float = Field(..., description="Projected Trinity Score of the answer.")
    winning_strategist: StrategistType | None = Field(None, description="Whose view dominated?")
