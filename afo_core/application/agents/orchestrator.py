"""
Agent Orchestrator
Coordinates the AI analysis workflow:
1. PII Redaction
2. RAG Context Retrieval
3. Prompt Engineering
4. AI Gateway Inference (Streaming)
"""

from typing import Any, AsyncGenerator

from domain.ai.models import AIRequest
from domain.ai.prompts import get_prompt_template
from infrastructure.ai.gateway import AIGateway, ai_gateway
from infrastructure.middleware.pii_redactor import PIIRedactor
from infrastructure.rag.engine import RAGEngine


class AgentOrchestrator:
    """
    L3 Service that orchestrates the 'Real Agent Intelligence' workflow.
    """

    def __init__(
        self, gateway: AIGateway = ai_gateway, rag_engine: RAGEngine | None = None
    ) -> None:
        self.gateway = gateway
        self.rag_engine = rag_engine or RAGEngine()

    async def orchestrate_analysis(
        self,
        original_query: str,
        persona: str = "tax_analyst",
        context_filters: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Executes the full analysis pipeline and yields streaming chunks.
        """

        # 1. Redact PII
        redacted_query = PIIRedactor.redact_query(original_query)

        # 2. Retrieve Context (RAG)
        context_chunks = await self.rag_engine.retrieve_context(
            redacted_query, filters=context_filters
        )
        context_text = "\n\n".join([f"[{c.source}]: {c.content}" for c in context_chunks])

        if not context_chunks:
            context_text = "No specific IRS context found. Use general tax knowledge."

        # 3. Construct Prompt
        prompt_template = get_prompt_template(persona)
        full_prompt = prompt_template.format(context=context_text, query=redacted_query)

        # 4. Create AI Request
        # Note: We pass the constructed prompt as 'query' to the Gateway for now.
        # In a more advanced Chat API usage, we'd structure messages=[{"role": "system", ...}, ...]
        ai_request = AIRequest(
            query=full_prompt,  # Gateway treats this as the prompt content
            context_filters={"sources": [c.source for c in context_chunks]},
            persona=persona,
        )

        # 5. Stream Interface
        async for chunk in self.gateway.generate_stream(ai_request):
            yield chunk


# Singleton
agent_orchestrator = AgentOrchestrator()
