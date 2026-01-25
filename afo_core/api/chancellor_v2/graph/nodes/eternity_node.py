from __future__ import annotations

import asyncio
import json
import os
from typing import TYPE_CHECKING

from AFO.llm_router import llm_router

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""ETERNITY Node - Persistence and reproducibility evaluation (永: Eternity)."""


async def eternity_node(state: GraphState) -> GraphState:
    """Evaluate persistence, documentation, and reproducibility aspects.

    永 (Eternity) - 영속성, 기록 보존, 재현 가능성 (2% 가중치)
    Scholar: Yeongdeok (Ollama / Local Scholar)
    """
    skill_id = state.plan.get("skill_id", "")
    query = state.plan.get("query", "")

    # 1. Heuristic Evaluation
    documentation_quality_score = _evaluate_documentation_quality(query)
    reproducibility_score = _evaluate_reproducibility(skill_id)
    persistence_guarantees_score = _evaluate_persistence_guarantees(state)
    heuristic_score = (
        documentation_quality_score * 0.4
        + reproducibility_score * 0.3
        + persistence_guarantees_score * 0.3
    )

    # 2. Scholar Assessment (Yeongdeok)

    prompt = f"""
    You are Yeongdeok (永), the Eternity Strategist of the AFO Kingdom.
    Analyze the following execution plan for persistence, reproducibility, and documentation.

    Plan:
    - Skill: {skill_id}
    - Query: {query}
    - Command: {state.input.get("command", "")}

    Guidelines:
    - Evaluate if the results of this plan will be persisted correctly.
    - Assess if the execution is reproducible.
    - Check if documentation requirements are met.

    Provide your assessment in JSON:
    {{
      "score": float (0.0 to 1.0),
      "reasoning": string,
      "issues": list[string]
    }}
    """

    scholar_score = heuristic_score
    reasoning = "Heuristic assessment based on persistence and documentation indicators."
    issues = []
    assessment_mode = "Heuristic (Fallback)"
    scholar_model = "None"

    # Get timeout from environment (default 8 seconds for pillar nodes in dev)
    pillar_timeout = float(os.getenv("AFO_PILLAR_TIMEOUT", "8.0"))

    try:
        response = await asyncio.wait_for(
            llm_router.call_scholar_via_ssot(
                query=prompt,
                scholar_key="eternity_scholar",
                context={"provider": "ollama", "quality_tier": "standard"},
            ),
            timeout=pillar_timeout,
        )
        if response and response.get("response"):
            try:
                text = (
                    response["response"].strip().replace("```json", "").replace("```", "").strip()
                )
                data = json.loads(text)
                scholar_score = data.get("score", heuristic_score)
                reasoning = data.get("reasoning", reasoning)
                issues = data.get("issues", [])
                assessment_mode = "LLM (Scholar)"
                scholar_model = response.get("model", "Ollama/Yeongdeok")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass  # Fall back to heuristic scores
    except Exception as e:
        state.errors.append(f"Yeongdeok (ETERNITY) assessment failed: {e}")

    # Combine: 30% Heuristic + 70% Scholar
    final_score = (heuristic_score * 0.3) + (scholar_score * 0.7)

    evaluation = {
        "score": round(final_score, 3),
        "reasoning": reasoning,
        "issues": issues,
        "metadata": {
            "mode": assessment_mode,
            "scholar": "Yeongdeok (永)",
            "model": scholar_model,
        },
    }

    state.outputs["ETERNITY"] = evaluation
    return state


def _evaluate_documentation_quality(query: str) -> float:
    """영속성(永): 문서화 품질 평가 - AFO 왕국 특화"""
    if not query:
        return 0.6  # AFO 왕국은 기본적으로 고도 문서화 지향

    query_lower = query.lower()

    # AFO 왕국 문서화 키워드 확장 (SSOT, Trinity Score, Chancellor Graph 등 고려)
    documentation_keywords = {
        # 기존 키워드
        "docs": 0.9,
        "document": 0.9,
        "readme": 0.9,
        "guide": 0.8,
        "tutorial": 0.8,
        "manual": 0.8,
        "spec": 0.8,
        "specification": 0.8,
        "api": 0.8,
        "log": 0.7,
        "logging": 0.7,
        "audit": 0.7,
        "version": 0.6,
        "changelog": 0.6,
        "history": 0.6,
        # AFO 왕국 특화 키워드 (고점수)
        "ssot": 0.95,
        "evolution": 0.95,
        "trinity": 0.95,
        "chancellor": 0.95,
        "graph": 0.95,
        "context7": 0.95,
        "persona": 0.9,
        "orchestration": 0.9,
        "coordination": 0.9,
        "audit-trail": 0.9,
        "version-control": 0.9,
        "git": 0.85,
        "knowledge": 0.85,
        "library": 0.85,
        "archive": 0.85,
        # 일반 문서화 키워드 (중간 점수)
        "comment": 0.7,
        "docstring": 0.7,
        "annotation": 0.7,
        "metadata": 0.65,
        "schema": 0.65,
        "contract": 0.65,
        "trace": 0.6,
        "evidence": 0.6,
        "record": 0.6,
    }

    max_score = 0.0
    keyword_count = 0

    for keyword, score in documentation_keywords.items():
        if keyword in query_lower:
            max_score = max(max_score, score)
            keyword_count += 1

    # 다중 키워드 보너스 (문서화 포괄성이 높을수록 점수 상승)
    if keyword_count >= 3:
        max_score = min(max_score + 0.1, 1.0)
    elif keyword_count >= 2:
        max_score = min(max_score + 0.05, 1.0)

    return max_score if max_score > 0 else 0.7  # AFO 왕국 기본 문서화 수준 향상


def _evaluate_reproducibility(skill_id: str) -> float:
    """기록 보존(永): 재현 가능성 평가"""
    if not skill_id:
        return 0.4

    skill_lower = skill_id.lower()

    # 재현 가능성 관련 키워드 평가
    reproducibility_indicators = {
        "seed": 0.9,
        "deterministic": 0.9,
        "reproducible": 0.9,
        "cache": 0.8,
        "persistent": 0.8,
        "stable": 0.8,
        "versioned": 0.7,
        "tagged": 0.7,
        "immutable": 0.7,
        "backup": 0.6,
        "snapshot": 0.6,
        "archive": 0.6,
    }

    reproducibility_score = 0.0
    for indicator, score in reproducibility_indicators.items():
        if indicator in skill_lower:
            reproducibility_score = max(reproducibility_score, score)

    # 기본 재현 가능성 (대부분의 작업은 어느 정도 재현 가능)
    return max(reproducibility_score, 0.6)


def _evaluate_persistence_guarantees(state: GraphState) -> float:
    """영속성 보장(永): 데이터/상태 영속성 평가"""
    # 기존 outputs 확인으로 영속성 보장 평가
    outputs = state.outputs or {}

    persistence_score = 0.0

    # 다른 노드들의 평가가 있는지 확인 (영속성에 기여)
    if "TRUTH" in outputs:
        persistence_score += 0.15  # 타입 안전성으로 장기 안정성

    if "GOODNESS" in outputs:
        persistence_score += 0.15  # 보안 검증으로 데이터 무결성

    if "BEAUTY" in outputs:
        persistence_score += 0.15  # 일관된 구조로 유지보수성

    if "SERENITY" in outputs:
        persistence_score += 0.15  # 자동화로 운영 연속성

    # 기본 영속성 점수 (어떤 시스템이든 어느 정도 영속성 보장)
    base_persistence = 0.4

    return min(persistence_score + base_persistence, 1.0)
