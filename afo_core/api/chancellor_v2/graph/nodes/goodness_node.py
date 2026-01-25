from __future__ import annotations

import asyncio
import json
import os
from typing import TYPE_CHECKING

from AFO.llm_router import llm_router

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""GOODNESS Node - Ethical/security evaluation (善: Goodness)."""


async def goodness_node(state: GraphState) -> GraphState:
    """Evaluate ethical and security aspects.

    善 (Goodness) - 인간 중심, 윤리·안정성, 보안, 비용 최적화 평가
    Scholar: Pangtong (GPT-4o / OpenAI)
    """
    skill_id = state.plan.get("skill_id", "")
    query = state.plan.get("query", "")

    # 1. Real-Time Constitution Probing
    # The system audits its own goodness based on the AFO Constitution
    from AFO.constitution.constitutional_ai import AFOConstitution

    c_score = 1.0
    c_issues = []

    # Evaluate compliance of the user query vs plan
    proposed_summary = f"Execute {skill_id} with query: {query}"
    is_compliant, reason = AFOConstitution.evaluate_compliance(
        query=query, proposed_action=proposed_summary
    )

    if not is_compliant:
        c_score = 0.0
        c_issues.append(f"CONSTITUTION VIOLATION: {reason}")

    # Heuristic component
    security_score = _evaluate_security(skill_id, query)
    heuristic_score = (security_score * 0.5 + c_score * 0.5) if c_score > 0 else 0.0

    # 2. Scholar Assessment (Pangtong)
    prompt = f"""
    You are Pangtong (善), the Ethical & Security Strategist of the AFO Kingdom.
    Analyze the following execution plan for semantic security, privacy, and cost-efficiency.

    Constitution Status: {"Compliant" if c_score > 0 else "VIOLATION"}
    Issues Found: {", ".join(c_issues) if c_issues else "None"}

    Plan:
    - Skill: {skill_id}
    - Query: {query}
    - Command: {state.input.get("command", "")}

    Provide your assessment in JSON:
    {{
      "score": float (0.0 to 1.0),
      "reasoning": string,
      "issues": list[string]
    }}
    """

    scholar_score = heuristic_score
    reasoning = "Heuristic assessment based on security keyword matching."
    issues = c_issues
    assessment_mode = "Heuristic (Fallback)"
    scholar_model = "None"

    pillar_timeout = float(os.getenv("AFO_PILLAR_TIMEOUT", "8.0"))

    try:
        response = await asyncio.wait_for(
            llm_router.call_scholar_via_ssot(
                query=prompt,
                scholar_key="goodness_scholar",
                context={"provider": "openai", "quality_tier": "premium"},
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
                issues.extend(data.get("issues", []))
                assessment_mode = "LLM (Scholar)"
                scholar_model = response.get("model", "OpenAI/Pangtong")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
    except Exception as e:
        state.errors.append(f"Pangtong (GOODNESS) assessment failed: {e}")

    # Zero Tolerance: If constitution fails, score is 0
    final_score = (heuristic_score * 0.3 + scholar_score * 0.7) if c_score > 0 else 0.0

    evaluation = {
        "score": round(final_score, 3),
        "reasoning": reasoning,
        "issues": list(set(issues)),
        "metadata": {
            "mode": assessment_mode,
            "scholar": "Pangtong (善)",
            "model": scholar_model,
            "constitution_compliance": "Healthy" if c_score > 0 else "Violation",
        },
    }

    state.outputs["GOODNESS"] = evaluation
    return state


def _evaluate_security(skill_id: str, query: str) -> float:
    """보안성 평가"""
    if not skill_id and not query:
        return 0.6

    combined_text = f"{skill_id} {query}".lower()

    # 보안 관련 키워드 평가
    security_indicators = {
        "security": 0.9,
        "secure": 0.9,
        "auth": 0.9,
        "authentication": 0.9,
        "encrypt": 0.9,
        "encryption": 0.9,
        "ssl": 0.8,
        "tls": 0.8,
        "firewall": 0.8,
        "audit": 0.8,
        "logging": 0.8,
        "sanitize": 0.7,
        "validate": 0.7,
        "escape": 0.7,
        "csrf": 0.8,
        "xss": 0.8,
        "injection": 0.8,
    }

    security_score = 0.0
    for indicator, score in security_indicators.items():
        if indicator in combined_text:
            security_score = max(security_score, score)

    return max(security_score, 0.6)  # 기본 보안 수준


def _evaluate_privacy_compliance(query: str) -> float:
    """개인정보 보호 평가"""
    if not query:
        return 0.7

    query_lower = query.lower()

    # 개인정보 관련 키워드 평가
    privacy_indicators = {
        "gdpr": 0.9,
        "ccpa": 0.9,
        "privacy": 0.9,
        "pii": 0.9,
        "consent": 0.8,
        "anonymize": 0.8,
        "pseudonymize": 0.8,
        "data retention": 0.8,
        "data deletion": 0.8,
        "user data": 0.7,
        "personal data": 0.7,
    }

    privacy_score = 0.0
    for indicator, score in privacy_indicators.items():
        if indicator in query_lower:
            privacy_score = max(privacy_score, score)

    return max(privacy_score, 0.7)  # 기본 개인정보 보호 준수


def _evaluate_cost_efficiency(skill_id: str) -> float:
    """비용 효율성 평가"""
    if not skill_id:
        return 0.6

    skill_lower = skill_id.lower()

    # 비용 효율성 관련 키워드 평가
    cost_indicators = {
        "optimize": 0.9,
        "efficient": 0.9,
        "performance": 0.8,
        "cache": 0.8,
        "memory": 0.7,
        "cpu": 0.7,
        "local": 0.8,
        "lightweight": 0.8,
        "minimal": 0.8,
        "batch": 0.7,
        "async": 0.7,
        "streaming": 0.7,
    }

    cost_score = 0.0
    for indicator, score in cost_indicators.items():
        if indicator in skill_lower:
            cost_score = max(cost_score, score)

    return max(cost_score, 0.6)  # 기본 비용 효율성


def _evaluate_ethical_considerations(query: str) -> float:
    """윤리적 고려 평가"""
    if not query:
        return 0.7

    query_lower = query.lower()

    # 윤리적 고려 관련 키워드 평가
    ethical_indicators = {
        "ethical": 0.9,
        "fair": 0.9,
        "bias": 0.9,
        "responsible": 0.9,
        "inclusive": 0.8,
        "accessible": 0.8,
        "diversity": 0.8,
        "transparency": 0.8,
        "explainable": 0.8,
        "accountability": 0.8,
        "sustainable": 0.7,
        "environment": 0.7,
        "social impact": 0.7,
    }

    ethical_score = 0.0
    for indicator, score in ethical_indicators.items():
        if indicator in query_lower:
            ethical_score = max(ethical_score, score)

    return max(ethical_score, 0.7)  # 기본 윤리적 고려
