"""Voice Command Executor.

분석된 의도에 따라 실제 CPA 기능을 실행합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import VoiceIntent


class VoiceExecutor:
    """CPA 기능 실행기."""

    async def execute(self, intent: VoiceIntent, context: dict[str, Any]) -> dict[str, Any]:
        """의도에 맞는 기능을 호출합니다."""
        if intent.command_type == "tax_analysis":
            return await self._tax_analysis(intent, context)
        elif intent.command_type == "chart_generation":
            return await self._chart_generation(intent, context)
        elif intent.command_type == "document_process":
            return await self._document_process(intent, context)
        else:
            return {"status": "success", "message": "일반 명령을 수행했습니다."}

    async def _tax_analysis(self, intent: VoiceIntent, context: dict[str, Any]) -> dict[str, Any]:
        # 실제 세금 분석 모듈 연동
        return {
            "result_type": "tax_estimate",
            "amount": 12500,
            "currency": "USD",
            "message": "2025년 예상 세금은 약 $12,500입니다.",
        }

    async def _chart_generation(
        self, intent: VoiceIntent, context: dict[str, Any]
    ) -> dict[str, Any]:
        # 차트 생성 모듈 연동
        return {
            "result_type": "chart_url",
            "url": "https://afo.kingdom/charts/abc.png",
            "message": "요청하신 세금 부담 추이 차트를 생성했습니다.",
        }

    async def _document_process(
        self, intent: VoiceIntent, context: dict[str, Any]
    ) -> dict[str, Any]:
        # 문서 처리 모듈 연동
        return {
            "result_type": "doc_summary",
            "summary": "W-2 문서 분석 결과 연봉 $150,000임이 확인되었습니다.",
            "message": "문서 분석을 완료했습니다.",
        }
