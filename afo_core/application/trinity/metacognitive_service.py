import asyncio
from typing import Any, AsyncGenerator

from application.agents.orchestrator import agent_orchestrator
from domain.trinity.models import StrategistType


class MetacognitiveAuditService:
    """
    L3 Service for system self-reflection and audit.
    """

    async def _get_strategist_reflection(
        self, target: str, persona: StrategistType
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Asks a strategist to reflect on a specific target (Phase/File).
        """
        print(f"DEBUG: Reflection started for {persona.value}")
        query = f"Execute a metacognitive audit of: {target}. Analyze the logic, risks, and UX from your pillar's perspective."

        async for chunk in agent_orchestrator.orchestrate_analysis(query, persona=persona.value):
            print(f"DEBUG: Chunk from {persona.value}: {chunk[:20]}")
            yield {"persona": persona.value, "chunk": chunk}
        print(f"DEBUG: Reflection finished for {persona.value}")

    async def audit_system_stream(self, target: str) -> AsyncGenerator[dict[str, Any], None]:
        """
        Streams reflections from all three strategists regarding the target.
        """
        print(f"🧠 [MetacognitiveResonance] Initiated for: {target}")

        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        active_counts = {"val": 3}
        tasks = []

        async def _stream_to_queue(persona: StrategistType) -> None:
            try:
                print(f"DEBUG: Task for {persona.value} entering loop")
                async for chunk_data in self._get_strategist_reflection(target, persona):
                    await queue.put(chunk_data)
            except Exception as e:
                print(f"DEBUG: Task for {persona.value} failed: {e}")
            finally:
                active_counts["val"] -= 1
                print(f"DEBUG: Task for {persona.value} exiting, remaining: {active_counts['val']}")
                if active_counts["val"] == 0:
                    await queue.put(None)

        tasks.append(asyncio.create_task(_stream_to_queue(StrategistType.ZHUGE_LIANG)))
        tasks.append(asyncio.create_task(_stream_to_queue(StrategistType.SIMA_YI)))
        tasks.append(asyncio.create_task(_stream_to_queue(StrategistType.ZHOU_YU)))

        while True:
            item = await queue.get()
            if item is None:
                break
            yield item


metacognitive_service = MetacognitiveAuditService()
