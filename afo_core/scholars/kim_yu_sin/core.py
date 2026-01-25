import logging
from typing import Any

from .adapter import OllamaAdapter
from .evaluator import QualityEvaluator
from .sages import ThreeSages
from .tools import RoyalTools

logger = logging.getLogger(__name__)


class KimYuSinScholar:
    """
    김유신 (KimYuSin) - 기록 및 보안 담당 학자
    Ollama (Local LLM) 기반의 아카이비스트
    Modularized Implementation (Phase 72)
    """

    def __init__(self) -> None:
        self.adapter = OllamaAdapter()
        self.evaluator = QualityEvaluator()
        self.sages = ThreeSages(self.adapter, self.evaluator)
        self.tools = RoyalTools(self.sages)

    # -------------------------------------------------------------------------
    # Delegate Methods to Components
    # -------------------------------------------------------------------------

    async def consult_samahwi(
        self,
        query: str,
        trinity_score: float | None = None,
        force_escalate: bool = False,
    ) -> str:
        return await self.sages.consult_samahwi(query, trinity_score, force_escalate)

    async def consult_samahwi_with_escalation(self, query: str) -> tuple[str, float, bool]:
        return await self.sages.consult_samahwi_with_escalation(query)

    async def consult_jwaja(self, query: str) -> str:
        return await self.sages.consult_jwaja(query)

    async def consult_hwata(
        self,
        query: str,
        trinity_score: float | None = None,
        force_precise: bool = False,
    ) -> str:
        return await self.sages.consult_hwata(query, trinity_score, force_precise)

    async def consult_hwata_with_escalation(
        self,
        query: str,
    ) -> tuple[str, float | None, bool]:
        return await self.sages.consult_hwata_with_escalation(query)

    async def document_code(self, code: str) -> str:
        return await self.tools.document_code(code)

    async def summarize_log(self, logs: str) -> str:
        return await self.tools.summarize_log(logs)

    async def security_scan(self, content: str) -> str:
        return await self.tools.security_scan(content)

    async def use_tool(self, tool_name: str, **kwargs: Any) -> str:
        return await self.tools.use_tool(tool_name, **kwargs)
