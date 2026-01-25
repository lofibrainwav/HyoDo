"""
AI Domain Models
Defines the core data structures for the AI Integration Layer.
Pydantic models for Requests, Responses, and Metadata.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AIRequest(BaseModel):
    """
    Standard request model for AI interactions.
    """

    query: str = Field(..., min_length=1, description="The user's input query or prompt.")
    context_filters: dict[str, Any] | None = Field(
        None, description="Filters for RAG retrieval (e.g., specific IRS publication)."
    )
    context: str | None = Field(None, description="Retrieved context chunks (RAG) to include.")
    persona: str = Field("tax_analyst", description="The persona to adopt for this request.")
    stream: bool = Field(True, description="Whether to stream the response.")
    max_tokens: int | None = Field(None, description="Maximum tokens to generate.")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature.")

    @field_validator("query")
    def query_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query must not be empty or whitespace only.")
        return v

    @field_validator("max_tokens")
    def validate_max_tokens(cls, v: int | None) -> int | None:
        if v is not None and v > 4096:  # Hard limit for safety
            raise ValueError("max_tokens cannot exceed 4096")
        return v


class AIMetadata(BaseModel):
    """
    Metadata capturing the details of an AI interaction.
    Useful for observability, auditing, and cost analysis.
    """

    request_id: str = Field(..., description="Unique identifier for the request.")
    model_used: str = Field(..., description="The specific model used for inference.")
    tokens_input: int = Field(0, ge=0, description="Number of prompt tokens.")
    tokens_output: int = Field(0, ge=0, description="Number of generated tokens.")
    latency_ms: float = Field(..., ge=0.0, description="Total latency in milliseconds.")
    rag_sources: list[str] = Field(
        default_factory=list, description="List of RAG source documents used."
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="Time of completion.")
    finish_reason: str | None = Field(
        None, description="Reason for generation stop (e.g., stop, length)."
    )


class AIResponse(BaseModel):
    """
    Standard response model for AI interactions.
    For streaming, this represents the final aggregated response.
    """

    content: str = Field(..., description="The generated text content.")
    metadata: AIMetadata | None = Field(None, description="Metadata about the generation.")
    is_complete: bool = Field(True, description="Whether the response is complete.")
    error: str | None = Field(None, description="Error message if any occurred.")
