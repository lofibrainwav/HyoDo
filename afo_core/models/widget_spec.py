from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Trinity Score: 90.0 (Established by Chancellor)
"""Widget Specification Models (Pydantic v2)

Contract validation for generated/widgets.json
Used in CI/local validation and optional FastAPI endpoints.
NOT used in frontend build path.
"""


class LegacyInfo(BaseModel):
    """Legacy HTML metadata"""

    tag: str | None = None


class BaseWidgetSpec(BaseModel):
    """Base widget specification"""

    model_config = ConfigDict(extra="ignore", frozen=False)

    id: str = Field(..., description="Unique widget identifier")
    source: str = Field(..., description="Widget source type")
    order: int = Field(default=0, description="Display order")
    title: str | None = Field(default=None, description="Widget title")
    route: str | None = Field(default=None, description="Widget route path")
    legacy: LegacyInfo | None = Field(default=None, description="Legacy HTML metadata")


class GeneratedWidgetSpec(BaseWidgetSpec):
    """Generated widget from HTML parsing"""

    source: str = "generated"
    dataWidgetId: str | None = Field(default=None)
    sourceId: str | None = Field(default=None, description="Legacy field (fallback)")
    html_section_id: str | None = Field(default=None, description="Legacy field (fallback)")
    fragment_key: str | None = Field(
        default=None,
        description="[Ticket 3] 표준 fragment 포인터. HTML fragment 추출 시 사용. 읽을 때 fallback: fragment_key ?? html_section_id ?? sourceId",
    )
    preview: str | None = Field(default=None, description="Preview text")
    visibility: Literal["public", "internal", "hidden"] | None = Field(default="internal")
    category: Literal["card", "panel", "chart", "legacy"] | None = Field(default="panel")
    defaultEnabled: bool | None = Field(default=True)
    tags: list[str] | None = Field(default_factory=list)


class ManualWidgetSpec(BaseWidgetSpec):
    """Manually registered widget"""

    source: str = "manual"
    description: str | None = None
    category: Literal["card", "panel", "chart", "legacy"] | None = None
    visibility: Literal["public", "internal", "hidden"] | None = None
    defaultEnabled: bool | None = None
    tags: list[str] | None = None


class ApiWidgetSpec(BaseWidgetSpec):
    """API-generated widget"""

    source: str = "api"
    endpoint: str | None = None
    method: Literal["GET", "POST", "PUT", "DELETE"] | None = None


# Discriminated union by source
# Note: For now, we accept any widget that matches BaseWidgetSpec
# Future: Use discriminated union when all widget types are fully defined
WidgetUnion = BaseWidgetSpec | GeneratedWidgetSpec | ManualWidgetSpec | ApiWidgetSpec


# For validation, we'll use a more permissive approach
# that accepts the actual JSON structure
class WidgetSpecFlexible(BaseModel):
    """Flexible widget spec that accepts the actual JSON structure"""

    model_config = ConfigDict(extra="allow")

    id: str
    source: str
    order: int | None = 0
    title: str | None = None
    route: str | None = None
    dataWidgetId: str | None = None
    sourceId: str | None = None  # Legacy field (fallback)
    html_section_id: str | None = None  # Legacy field (fallback)
    fragment_key: str | None = None  # [Ticket 3] 표준 fragment 포인터
    preview: str | None = None
    visibility: str | None = None
    category: str | None = None
    defaultEnabled: bool | None = None
    tags: list[str] | None = None
    legacy: dict[str, Any] | None = None


class WidgetsPayloadFlexible(BaseModel):
    """Flexible container for widgets list"""

    model_config = ConfigDict(extra="allow")

    source: str
    generatedAt: str
    count: int
    widgets: list[WidgetSpecFlexible]


class WidgetsPayload(BaseModel):
    """Container for widgets list"""

    model_config = ConfigDict(extra="ignore")

    source: str = Field(..., description="Source file path")
    generatedAt: str = Field(..., description="Generation timestamp")
    count: int = Field(..., description="Widget count")
    widgets: list[WidgetUnion] = Field(..., description="List of widgets")
