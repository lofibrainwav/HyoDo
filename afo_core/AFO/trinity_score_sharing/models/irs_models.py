"""IRS Regulation and Impact Models.

법령 메타데이터, 변경 영향도 분석 및 IRS 변경 로그 모델.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .enums import ChangeType, ImpactLevel, ValidationStatus


class RegulationMetadata(BaseModel):
    """법령 메타데이터."""

    source_id: str = Field(description="RSS/API Source ID")
    regulation_code: str = Field(description="법령/규정 코드")
    title: str = Field(max_length=256)
    publication_date: datetime
    effective_date: datetime
    url: str = Field(pattern=r"https?://.*")
    tags: list[str] = Field(default_factory=list)


class ChangeImpactAnalysis(BaseModel):
    """변경 영향도 분석 모델."""

    analysis_id: UUID = Field(default_factory=uuid4)
    impact_level: ImpactLevel
    affected_modules: list[str] = Field(default_factory=list)
    estimated_adaptation_effort: float = Field(description="적응 예상 공수 (Man-hours)")
    jang_yeong_sil_opinion: str | None = Field(None, description="기술적 분석 (眞)")
    yi_sun_sin_opinion: str | None = Field(None, description="안정성 분석 (善)")
    shin_saimdang_opinion: str | None = Field(None, description="UX 분석 (美)")
    requires_manual_intervention: bool = True


class IRSChangeLog(BaseModel):
    """IRS 변경 로그 (SSOT)."""

    change_id: UUID = Field(default_factory=uuid4)
    metadata: RegulationMetadata
    change_type: ChangeType = ChangeType.AMENDMENT
    status: ValidationStatus = ValidationStatus.PENDING
    detected_at: datetime = Field(default_factory=datetime.now)
    summary: str = ""
    full_text_hash: str = ""
    impact_analysis: ChangeImpactAnalysis | None = None

    def is_critical(self) -> bool:
        """긴급 대응 필요 여부 판정."""
        if self.impact_analysis:
            return self.impact_analysis.impact_level == ImpactLevel.CRITICAL
        return False
