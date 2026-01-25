from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO Skill Models (domain/skills/models.py)

眞善美孝 philosophy alignment and structured skill definitions.
"""


# ============================================================================
# Enums
# ============================================================================


class SkillCategory(str, Enum):
    """Skill categories aligned with AFO architecture"""

    STRATEGIC_COMMAND = "strategic_command"  # LangGraph orchestration
    RAG_SYSTEMS = "rag_systems"  # Ultimate RAG, Trinity Loop, etc.
    WORKFLOW_AUTOMATION = "workflow_automation"  # n8n, Speckit
    HEALTH_MONITORING = "health_monitoring"  # 11-organ health
    MEMORY_MANAGEMENT = "memory_management"  # Redis, PostgreSQL, ChromaDB
    BROWSER_AUTOMATION = "browser_automation"  # Playwright
    ANALYSIS_EVALUATION = "analysis_evaluation"  # Ragas, Lyapunov
    INTEGRATION = "integration"  # External APIs, MCP
    METACOGNITION = "metacognition"  # Self-reflection, Vibe Coding
    SECURITY = "security"  # Security scanning & patching
    CODE_ANALYSIS = "code_analysis"  # Static analysis & linting
    DATA_ENGINEERING = "data_engineering"  # Data pipeline & optimization
    DEVOPS = "devops"  # CI/CD, Infrastructure, Profiling
    SUSTAINABILITY = "sustainability"  # Energy monitoring & Green AI
    CREATIVE_AI = "creative_ai"  # GenUI, Creative generation
    INTELLIGENCE = "intelligence"  # Context7, Awesome-Skills
    GOVERNANCE = "governance"  # Compliance, Constitution, Trinity Protocol


class SkillStatus(str, Enum):
    """Skill lifecycle status"""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"
    MAINTENANCE = "maintenance"


class ExecutionMode(str, Enum):
    """Skill execution modes"""

    SYNC = "sync"
    ASYNC = "async"
    STREAMING = "streaming"
    BACKGROUND = "background"


# ============================================================================
# Models
# ============================================================================


class PhilosophyScore(BaseModel):
    """
    眞善美孝 philosophy alignment scores

    - 眞 (Truth): Technical certainty, provability (0-100)
    - 善 (Goodness): Ethical priority, stability (0-100)
    - 美 (Beauty): Clear storytelling, UX (0-100)
    - 孝 (Serenity): Frictionless operation (0-100)
    """

    model_config = ConfigDict(frozen=True)

    truth: Annotated[int, Field(ge=0, le=100, description="眞 (Truth) - Technical certainty")]
    goodness: Annotated[int, Field(ge=0, le=100, description="善 (Goodness) - Ethical priority")]
    beauty: Annotated[int, Field(ge=0, le=100, description="美 (Beauty) - Clear storytelling")]
    serenity: Annotated[
        int, Field(ge=0, le=100, description="孝 (Serenity) - Frictionless operation")
    ]

    @property
    def average(self) -> float:
        """Overall philosophy alignment score"""
        return (self.truth + self.goodness + self.beauty + self.serenity) / 4.0

    @property
    def summary(self) -> str:
        """Human-readable summary"""
        return f"眞{self.truth}% 善{self.goodness}% 美{self.beauty}% 孝{self.serenity}% (Avg: {self.average:.1f}%)"


class MCPConfig(BaseModel):
    """MCP (Model Context Protocol) configuration for skill"""

    mcp_server_url: HttpUrl | None = Field(
        default=None, description="MCP server endpoint (if external)"
    )
    mcp_version: str = Field(default="2025.1", description="MCP protocol version")
    capabilities: list[str] = Field(
        default_factory=list,
        description="MCP capabilities (e.g., 'tools', 'prompts', 'resources')",
    )
    authentication_required: bool = Field(
        default=False, description="Whether MCP server requires authentication"
    )


class SkillParameter(BaseModel):
    """Single skill parameter definition"""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (e.g., 'string', 'int', 'list[str]')")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Any | None = Field(default=None, description="Default value if not required")
    validation_rules: dict[str, Any] | None = Field(
        default=None, description="Validation rules (e.g., {'min': 0, 'max': 100})"
    )


class SkillIOSchema(BaseModel):
    """Input/Output schema for skill"""

    parameters: list[SkillParameter] = Field(default_factory=list, description="List of parameters")
    example: dict[str, Any] | None = Field(default=None, description="Example input/output")


class AFOSkillCard(BaseModel):
    """
    AFO Skill Card - Complete skill metadata
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skill_id": "skill_001_youtube_spec_gen",
                "name": "YouTube to n8n Spec Generator",
                "description": "Converts YouTube tutorial transcripts to executable n8n workflow specifications using GPT-4o-mini",
                "category": "workflow_automation",
                "version": "1.0.0",
                "capabilities": [
                    "youtube_transcript_extraction",
                    "llm_spec_generation",
                    "n8n_workflow_creation",
                ],
                "philosophy_scores": {
                    "truth": 95,
                    "goodness": 90,
                    "beauty": 92,
                    "serenity": 88,
                },
            }
        }
    )

    # Core Identity
    skill_id: str = Field(
        ...,
        description="Unique skill identifier (e.g., 'skill_001_youtube_spec_gen')",
        pattern=r"^skill_\d{3}_[a-z0-9_]+$",
    )
    name: str = Field(..., description="Human-readable skill name", min_length=3, max_length=100)
    description: str = Field(
        ..., description="Detailed skill description", min_length=10, max_length=1000
    )

    # Classification
    category: SkillCategory = Field(..., description="Skill category")
    tags: list[str] = Field(default_factory=list, description="Searchable tags", max_length=20)

    # Versioning & Status
    version: str = Field(
        ..., description="Semantic version (e.g., '1.0.0')", pattern=r"^\d+\.\d+\.\d+$"
    )
    status: SkillStatus = Field(default=SkillStatus.ACTIVE, description="Skill lifecycle status")

    # Capabilities & Dependencies
    capabilities: list[str] = Field(
        default_factory=list, description="List of skill capabilities", max_length=50
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Required dependencies (skill_ids or package names)",
        max_length=30,
    )

    # Execution Configuration
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.ASYNC, description="How the skill executes"
    )
    endpoint: HttpUrl | None = Field(
        default=None, description="API endpoint for skill execution (if applicable)"
    )
    estimated_duration_ms: int | None = Field(
        default=None, ge=0, description="Estimated execution time in milliseconds"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Default configuration parameters"
    )

    # Input/Output Schemas
    input_schema: SkillIOSchema = Field(
        default_factory=SkillIOSchema, description="Input parameters schema"
    )
    output_schema: SkillIOSchema = Field(default_factory=SkillIOSchema, description="Output schema")

    # Philosophy Alignment
    philosophy_scores: PhilosophyScore = Field(
        ..., description="眞善美孝 philosophy alignment scores"
    )

    # MCP Integration
    mcp_config: MCPConfig | None = Field(
        default=None, description="MCP configuration (if MCP-compatible)"
    )

    # Metadata
    author: str = Field(default="AFO Kingdom", description="Skill author/maintainer")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Skill creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    documentation_url: str | None = Field(
        default=None, description="Link to detailed documentation"
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Ensure tags are lowercase and unique"""
        return list({tag.lower().strip() for tag in v})

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: list[str]) -> list[str]:
        """Ensure capabilities are unique"""
        return list(set(v))


class SkillExecutionRequest(BaseModel):
    """Request model for executing a skill."""

    skill_id: str = Field(..., description="ID of the skill to execute")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Execution parameters")
    dry_run: bool = Field(False, description="If True, simulate execution without side effects")
    context: dict[str, Any] | None = Field(default=None, description="Additional execution context")
    async_execution: bool = Field(default=False, description="Whether to execute asynchronously")


class SkillExecutionResult(BaseModel):
    """Result model for skill execution."""

    skill_id: str
    status: str
    result: dict[str, Any]
    dry_run: bool
    error: str | None = None
    success: bool = Field(default=True, description="Legacy success flag")
    execution_time_ms: int = Field(default=0, description="Execution time")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
