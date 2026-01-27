import asyncio
from typing import Any, AsyncGenerator

from application.agents.orchestrator import agent_orchestrator
from domain.trinity.models import DebateResolution, StrategistType


class TrinityDebateService:
    """
    Service to orchestrate the 'Council of Three' debate.
    """

    async def _get_strategist_stream(
        self, query: str, persona: StrategistType
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Invokes the Agent Orchestrator and yields chunks with persona metadata.
        """
        async for chunk in agent_orchestrator.orchestrate_analysis(query, persona=persona.value):
            yield {"persona": persona.value, "chunk": chunk}

    async def conduct_debate_stream(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """
        Conducts a parallel debate and yields chunks as they arrive from each strategist.
        """
        print(f"🏛️ [TrinityStreamingDebate] convened for: {query}")

        # We need to run 3 streams in parallel and merge them.
        # This is a bit tricky with async generators, so we use a queue pattern.
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        active_streams = 3

        async def _stream_to_queue(persona: StrategistType) -> None:
            nonlocal active_streams
            try:
                async for chunk_data in self._get_strategist_stream(query, persona):
                    await queue.put(chunk_data)
            finally:
                active_streams -= 1
                if active_streams == 0:
                    await queue.put(None)  # Sentinel to close the main generator

        # Start parallel producers
        asyncio.create_task(_stream_to_queue(StrategistType.JANG_YEONG_SIL))
        asyncio.create_task(_stream_to_queue(StrategistType.YI_SUN_SIN))
        asyncio.create_task(_stream_to_queue(StrategistType.SHIN_SAIMDANG))

        # Consumer
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

        # Final Synthesis (Mock synthesis for the end of the stream)
        yield {
            "persona": "synthesis",
            "chunk": "\n\n# Final Verdict\nThe council resonance is complete. The path is clear.",
        }

    async def conduct_debate(self, query: str) -> DebateResolution:
        # Keeping compatibility for now or refactoring to use the stream
        # (Omitted for brevity as we'll focus on the streaming endpoint)
        raise NotImplementedError("Use conduct_debate_stream instead.")


trinity_service = TrinityDebateService()
