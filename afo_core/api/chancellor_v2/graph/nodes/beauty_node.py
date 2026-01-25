from __future__ import annotations

import asyncio
import json
import os
from typing import TYPE_CHECKING

from AFO.llm_router import llm_router

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""BEAUTY Node - UX/beauty evaluation (美: Beauty)."""


async def beauty_node(state: GraphState) -> GraphState:
    """Evaluate UX and aesthetic aspects.

    美 (Beauty) - 구조적 단순함, 모듈화, 일관된 API/UI 평가
    Scholar: Lushun (Gemini 2.0 Flash / Google)
    """
    skill_id = state.plan.get("skill_id", "")
    query = state.plan.get("query", "")

    # 1. Heuristic Evaluation
    ux_friendliness_score = _evaluate_ux_friendliness(query)
    structural_simplicity_score = _evaluate_structural_simplicity(skill_id)
    api_consistency_score = _evaluate_api_consistency(skill_id, query)
    modularity_score = _evaluate_modularity(skill_id)
    heuristic_score = (
        ux_friendliness_score * 0.3
        + structural_simplicity_score * 0.3
        + api_consistency_score * 0.2
        + modularity_score * 0.2
    )

    # 2. Scholar Assessment (Lushun)

    prompt = f"""
    You are Lushun (美), the UX & Aesthetic Strategist of the AFO Kingdom.
    Analyze the following execution plan for structure, simplicity, and user experience.

    Plan:
    - Skill: {skill_id}
    - Query: {query}
    - Command: {state.input.get("command", "")}

    Guidelines:
    - Evaluate the structural simplicity of the proposed plan.
    - Assess if the query is UX-friendly (clear, non-confusing).
    - Check for redundant complexity or "API clutter".

    Provide your assessment in JSON:
    {{
      "score": float (0.0 to 1.0),
      "reasoning": string,
      "issues": list[string]
    }}
    """

    scholar_score = heuristic_score
    reasoning = "Heuristic assessment based on structural complexity analysis."
    issues = []
    assessment_mode = "Heuristic (Fallback)"
    scholar_model = "None"

    # Get timeout from environment (default 8 seconds for pillar nodes in dev)
    pillar_timeout = float(os.getenv("AFO_PILLAR_TIMEOUT", "8.0"))

    try:
        response = await asyncio.wait_for(
            llm_router.call_scholar_via_ssot(
                query=prompt,
                scholar_key="beauty_scholar",
                context={"provider": "gemini", "quality_tier": "standard"},
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
                scholar_model = response.get("model", "Gemini/Lushun")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass  # Fall back to heuristic scores
    except Exception as e:
        state.errors.append(f"Lushun (BEAUTY) assessment failed: {e}")

    # Combine: 30% Heuristic + 70% Scholar
    final_score = (heuristic_score * 0.3) + (scholar_score * 0.7)

    evaluation = {
        "score": round(final_score, 3),
        "reasoning": reasoning,
        "issues": issues,
        "metadata": {
            "mode": assessment_mode,
            "scholar": "Lushun (美)",
            "model": scholar_model,
        },
    }

    state.outputs["BEAUTY"] = evaluation
    return state


def _evaluate_ux_friendliness(query: str) -> float:
    """UX 친화성 평가"""
    if not query:
        return 0.6

    query_lower = query.lower()

    # UX 관련 키워드 평가
    ux_indicators = {
        "user experience": 0.9,
        "ux": 0.9,
        "ui": 0.9,
        "interface": 0.8,
        "usability": 0.8,
        "accessible": 0.8,
        "responsive": 0.8,
        "intuitive": 0.8,
        "user-friendly": 0.8,
        "ergonomic": 0.7,
        "design": 0.7,
        "aesthetic": 0.7,
        "visual": 0.6,
    }

    ux_score = 0.0
    for indicator, score in ux_indicators.items():
        if indicator in query_lower:
            ux_score = max(ux_score, score)

    return max(ux_score, 0.6)  # 기본 UX 수준


def _evaluate_structural_simplicity(skill_id: str) -> float:
    """구조적 단순함 평가"""
    if not skill_id:
        return 0.6

    skill_lower = skill_id.lower()

    # 단순함 관련 키워드 평가
    simplicity_indicators = {
        "simple": 0.9,
        "clean": 0.9,
        "minimal": 0.9,
        "straightforward": 0.9,
        "refactor": 0.8,
        "simplify": 0.8,
        "optimize": 0.8,
        "readable": 0.7,
        "maintainable": 0.7,
        "elegant": 0.7,
        "concise": 0.7,
        "clear": 0.7,
        "intuitive": 0.6,
    }

    simplicity_score = 0.0
    for indicator, score in simplicity_indicators.items():
        if indicator in skill_lower:
            simplicity_score = max(simplicity_score, score)

    return max(simplicity_score, 0.6)  # 기본 구조적 단순함


def _evaluate_api_consistency(skill_id: str, query: str) -> float:
    """API 일관성 평가"""
    combined_text = f"{skill_id} {query}".lower()

    # API 일관성 관련 키워드 평가
    consistency_indicators = {
        "consistent": 0.9,
        "standard": 0.9,
        "convention": 0.9,
        "pattern": 0.8,
        "rest": 0.8,
        "restful": 0.8,
        "graphql": 0.8,
        "openapi": 0.8,
        "swagger": 0.7,
        "schema": 0.7,
        "contract": 0.7,
        "interface": 0.6,
        "protocol": 0.6,
        "specification": 0.6,
    }

    consistency_score = 0.0
    for indicator, score in consistency_indicators.items():
        if indicator in combined_text:
            consistency_score = max(consistency_score, score)

    return max(consistency_score, 0.7)  # 기본 API 일관성


def _evaluate_modularity(skill_id: str) -> float:
    """모듈화 평가"""
    if not skill_id:
        return 0.6

    skill_lower = skill_id.lower()

    # 모듈화 관련 키워드 평가
    modularity_indicators = {
        "modular": 0.9,
        "module": 0.9,
        "component": 0.8,
        "service": 0.8,
        "microservice": 0.8,
        "plugin": 0.8,
        "extension": 0.8,
        "separation": 0.7,
        "concern": 0.7,
        "layer": 0.7,
        "architecture": 0.6,
        "design pattern": 0.6,
        "solid": 0.6,
    }

    modularity_score = 0.0
    for indicator, score in modularity_indicators.items():
        if indicator in skill_lower:
            modularity_score = max(modularity_score, score)

    return max(modularity_score, 0.6)  # 기본 모듈화 수준
