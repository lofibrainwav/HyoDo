"""
Core Analysis Router (AI Stream)
Exposes the Real Agent Intelligence endpoints for Streaming Analysis.
Connects L4 API -> L3 Agent Orchestrator.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from AFO.utils.standard_shield import shield
from application.agents.orchestrator import agent_orchestrator

router = APIRouter(prefix="/api/ai", tags=["AI Analysis (L4)"])


class AnalysisRequest(BaseModel):
    query: str
    persona: str = "tax_analyst"
    context_filters: dict[str, Any] | None = None


@shield(pillar="善")
@router.post("/analyze")
async def analyze_stream(request: Request, body: AnalysisRequest):
    """
    Streams AI analysis for the given query using the Agent Orchestrator.
    This replaces the legacy mock /analyze endpoints.
    """

    async def stream_generator():
        try:
            async for chunk in agent_orchestrator.orchestrate_analysis(
                original_query=body.query,
                persona=body.persona,
                context_filters=body.context_filters,
            ):
                # Format as Server-Sent Events or raw text stream depending on client need.
                # Vercel AI SDK 'useChat' often prefers simple text stream or specific protocol.
                # For this implementation, we assume raw text stream is handled by the Vercel adapter on client.
                # But to be safe and standard, we just yield the chunk string.
                yield chunk
        except Exception as e:
            yield f"\n[ERROR: {e!s}]"

    return StreamingResponse(stream_generator(), media_type="text/plain")


@shield(pillar="善")
@router.post("/review")
async def review_stream(request: Request, body: AnalysisRequest):
    """
    Review endpoint (Auditor Persona).
    """
    # Force auditor persona
    body.persona = "auditor"
    return await analyze_stream(request, body)
