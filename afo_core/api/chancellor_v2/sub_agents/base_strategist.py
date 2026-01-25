"""Base Strategist - 추상 베이스 클래스.

3 Strategists 서브에이전트의 공통 인터페이스를 정의합니다.

AFO 철학:
- 眞 (Truth): 명확한 인터페이스 정의
- 善 (Goodness): 에러 처리 및 Fallback 보장
- 美 (Beauty): 일관된 평가 구조
"""

from __future__ import annotations

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from infrastructure.json_fast import loads as json_loads_fast

if TYPE_CHECKING:
    from ..orchestrator.strategist_context import StrategistContext

logger = logging.getLogger(__name__)


class BaseStrategist(ABC):
    """3 Strategists 서브에이전트 추상 베이스 클래스.

    각 Strategist는 독립 컨텍스트에서 실행되며,
    자신의 Pillar에 대한 평가만 수행합니다.

    Subclasses must define:
        - PILLAR: 담당 기둥 (TRUTH / GOODNESS / BEAUTY)
        - SCHOLAR_KEY: LLM Router Scholar 키
        - WEIGHT: Trinity Score 가중치
        - NAME_KO: 한글 이름
        - NAME_EN: 영문 이름

    Subclasses must implement:
        - get_prompt(): Strategist 전용 프롬프트 생성
        - heuristic_evaluate(): 휴리스틱 평가 (Fallback)
    """

    # 서브클래스에서 정의
    PILLAR: str = ""
    SCHOLAR_KEY: str = ""
    WEIGHT: float = 0.0
    NAME_KO: str = ""
    NAME_EN: str = ""

    def __init__(self) -> None:
        """Strategist 초기화."""
        self._timeout = float(os.getenv("AFO_PILLAR_TIMEOUT", "30.0"))

    @property
    def display_name(self) -> str:
        """표시 이름 (한글 + 영문)."""
        return f"{self.NAME_EN} ({self.NAME_KO})"

    async def evaluate(self, ctx: StrategistContext) -> StrategistContext:
        """컨텍스트 기반 평가 수행.

        LLM 평가를 시도하고, 실패 시 휴리스틱 Fallback을 사용합니다.

        Args:
            ctx: 격리된 실행 컨텍스트

        Returns:
            score, reasoning, issues가 채워진 컨텍스트
        """
        ctx.mark_started()

        # 1. 휴리스틱 평가 (기본값)
        heuristic_score = self.heuristic_evaluate(ctx)

        # 2. LLM 평가 시도
        scholar_score = heuristic_score
        reasoning = f"Heuristic assessment for {self.PILLAR}"
        issues: list[str] = []
        assessment_mode = "Heuristic (Fallback)"
        model_name = "None"

        try:
            from AFO.llm_router import llm_router

            prompt = self.get_prompt(ctx)

            response = await asyncio.wait_for(
                llm_router.call_scholar_via_ssot(
                    query=prompt,
                    scholar_key=self.SCHOLAR_KEY,
                    context={"provider": self._get_provider(), "quality_tier": "standard"},
                ),
                timeout=self._timeout,
            )

            if response and response.get("response"):
                parsed = self._parse_llm_response(response["response"])
                if parsed:
                    scholar_score = parsed.get("score", heuristic_score)
                    reasoning = parsed.get("reasoning", reasoning)
                    issues = parsed.get("issues", [])
                    assessment_mode = "LLM (Scholar)"
                    model_name = response.get("model", self.SCHOLAR_KEY)

        except TimeoutError:
            ctx.errors.append(f"{self.display_name} assessment timed out after {self._timeout}s")
            logger.warning(f"{self.PILLAR} evaluation timed out")
        except Exception as e:
            ctx.errors.append(f"{self.display_name} assessment failed: {e}")
            logger.error(f"{self.PILLAR} evaluation failed: {e}")

        # 3. 최종 점수 계산 (30% Heuristic + 70% Scholar)
        final_score = (heuristic_score * 0.3) + (scholar_score * 0.7)

        # 4. 컨텍스트 업데이트
        ctx.score = round(final_score, 3)
        ctx.reasoning = reasoning
        ctx.issues = issues
        ctx.metadata = {
            "mode": assessment_mode,
            "scholar": self.display_name,
            "model": model_name,
            "heuristic_score": round(heuristic_score, 3),
            "scholar_score": round(scholar_score, 3),
        }

        ctx.mark_completed()
        return ctx

    @abstractmethod
    def get_prompt(self, ctx: StrategistContext) -> str:
        """Strategist 전용 프롬프트 생성.

        Args:
            ctx: 실행 컨텍스트

        Returns:
            LLM에 전달할 프롬프트
        """
        pass

    @abstractmethod
    def heuristic_evaluate(self, ctx: StrategistContext) -> float:
        """휴리스틱 기반 빠른 평가 (LLM 실패 시 Fallback).

        Args:
            ctx: 실행 컨텍스트

        Returns:
            휴리스틱 점수 (0.0 ~ 1.0)
        """
        pass

    def _get_provider(self) -> str:
        """Scholar별 LLM Provider 반환."""
        # 기본 구현: 서브클래스에서 오버라이드 가능
        return "ollama"

    def _parse_llm_response(self, response_text: str) -> dict[str, Any] | None:
        """LLM 응답 JSON 파싱.

        Args:
            response_text: LLM 응답 텍스트

        Returns:
            파싱된 딕셔너리 또는 None
        """
        try:
            text = response_text.strip()
            # JSON 블록 추출
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json_loads_fast(text)

            # 필수 필드 검증
            if "score" not in data:
                return None

            return {
                "score": float(data.get("score", 0.0)),
                "reasoning": str(data.get("reasoning", "")),
                "issues": list(data.get("issues", [])),
            }
        except (ValueError, KeyError, TypeError) as e:
            logger.debug(f"Failed to parse LLM response: {e}")
            return None

    def _build_base_prompt(self, ctx: StrategistContext, guidelines: str) -> str:
        """공통 프롬프트 템플릿 생성.

        Args:
            ctx: 실행 컨텍스트
            guidelines: Strategist별 가이드라인

        Returns:
            완성된 프롬프트
        """
        return f"""
You are {self.display_name}, the {self.PILLAR} Strategist of the AFO Kingdom.
Analyze the following execution plan.

Plan:
- Skill: {ctx.skill_id}
- Query: {ctx.query}
- Command: {ctx.command}

Guidelines:
{guidelines}

Provide your assessment in JSON:
{{
  "score": float (0.0 to 1.0),
  "reasoning": string,
  "issues": list[string]
}}
"""
