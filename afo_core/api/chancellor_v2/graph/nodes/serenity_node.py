from __future__ import annotations

import asyncio
import json
import os
from typing import TYPE_CHECKING

from AFO.llm_router import llm_router

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""SERENITY Node - Automation and failure recovery evaluation (孝: Serenity)."""


async def serenity_node(state: GraphState) -> GraphState:
    """Evaluate automation, error recovery, and user friction reduction aspects.

    孝 (Serenity) - 평온·연속성, 자동화, 실패 복구 용이성 (8% 가중치)
    Scholar: Yeongdeok (Ollama / Local Scholar)
    """
    skill_id = state.plan.get("skill_id", "")
    query = state.plan.get("query", "")

    # 1. Real-Time Friction Analysis (Log Probing)
    # The system audits its own serenity based on recent error frequency
    from AFO.health.friction import get_friction_metrics

    friction_data = get_friction_metrics()
    f_score = 1.0 - friction_data.get("friction_score", 0.0)
    error_count = friction_data.get("error_count_last_100", 0)

    f_issues = []
    if error_count > 0:
        f_issues.append(f"System Friction Detected: {error_count} errors in last 100 logs.")

    # Heuristic component
    automation_potential_score = _evaluate_automation_potential(query)
    heuristic_score = automation_potential_score * 0.4 + f_score * 0.6

    # 2. Scholar Assessment (Yeongdeok)
    prompt = f"""
    You are Yeongdeok (孝), the Serenity Strategist of the AFO Kingdom.
    Analyze the following execution plan for automation potential and friction reduction.

    Current System Friction Level: {friction_data.get("friction_score", 0.0) * 100}%
    Recent Errors: {error_count}

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
    reasoning = "Heuristic assessment based on automation and friction indicators."
    issues = f_issues
    assessment_mode = "Heuristic (Fallback)"
    scholar_model = "None"

    pillar_timeout = float(os.getenv("AFO_PILLAR_TIMEOUT", "8.0"))

    try:
        response = await asyncio.wait_for(
            llm_router.call_scholar_via_ssot(
                query=prompt,
                scholar_key="serenity_scholar",
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
                issues.extend(data.get("issues", []))
                assessment_mode = "LLM (Scholar)"
                scholar_model = response.get("model", "Ollama/Yeongdeok")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
    except Exception as e:
        state.errors.append(f"Yeongdeok (SERENITY) assessment failed: {e}")

    # Combine: 30% Heuristic + 70% Scholar
    final_score = (heuristic_score * 0.3) + (scholar_score * 0.7)

    evaluation = {
        "score": round(final_score, 3),
        "reasoning": reasoning,
        "issues": list(set(issues)),
        "metadata": {
            "mode": assessment_mode,
            "scholar": "Yeongdeok (孝)",
            "model": scholar_model,
            "real_time_friction": f"{friction_data.get('friction_score', 0.0) * 100}%",
        },
    }

    state.outputs["SERENITY"] = evaluation
    return state


def _evaluate_automation_potential(query: str) -> float:
    """평온(孝): 자동화 잠재력 평가 - AFO 왕국 특화"""
    if not query:
        return 0.7  # AFO 왕국은 기본적으로 고도 자동화 지향

    query_lower = query.lower()

    # AFO 왕국 자동화 키워드 확장 (CI/CD, MCP, Chancellor Graph 등 고려)
    automation_keywords = {
        # 기존 키워드
        "auto": 0.9,
        "automate": 0.9,
        "automatic": 0.9,
        "batch": 0.8,
        "script": 0.8,
        "pipeline": 0.8,
        "schedule": 0.7,
        "cron": 0.7,
        "workflow": 0.7,
        "deploy": 0.6,
        "build": 0.6,
        "test": 0.6,
        # AFO 왕국 특화 키워드 (고점수)
        "mcp": 0.95,
        "chancellor": 0.95,
        "graph": 0.95,
        "trinity": 0.95,
        "orchestrate": 0.9,
        "coordinate": 0.9,
        "parallel": 0.9,
        "async": 0.85,
        "concurrent": 0.85,
        "distributed": 0.85,
        "ci/cd": 0.85,
        "webhook": 0.85,
        "trigger": 0.85,
        "event-driven": 0.85,
        "reactive": 0.85,
        # 일반 자동화 키워드 (중간 점수)
        "integration": 0.75,
        "stream": 0.75,
        "queue": 0.75,
        "cache": 0.7,
        "optimize": 0.7,
        "scale": 0.7,
        "monitor": 0.65,
        "alert": 0.65,
        "dashboard": 0.65,
    }

    max_score = 0.0
    keyword_count = 0

    for keyword, score in automation_keywords.items():
        if keyword in query_lower:
            max_score = max(max_score, score)
            keyword_count += 1

    # 다중 키워드 보너스 (자동화 복합성이 높을수록 점수 상승)
    if keyword_count >= 3:
        max_score = min(max_score + 0.1, 1.0)
    elif keyword_count >= 2:
        max_score = min(max_score + 0.05, 1.0)

    return max_score if max_score > 0 else 0.8  # AFO 왕국 기본 자동화 수준 향상


def _evaluate_error_recovery(skill_id: str) -> float:
    """연속성(孝): 오류 복구 용이성 평가"""
    if not skill_id:
        return 0.5

    skill_lower = skill_id.lower()

    # 복구 용이한 스킬 평가
    recovery_indicators = {
        "backup": 0.9,
        "restore": 0.9,
        "rollback": 0.9,
        "retry": 0.8,
        "fallback": 0.8,
        "circuit": 0.8,
        "health": 0.7,
        "monitor": 0.7,
        "alert": 0.7,
    }

    recovery_score = 0.0
    for indicator, score in recovery_indicators.items():
        if indicator in skill_lower:
            recovery_score = max(recovery_score, score)

    # 기본 복구 용이성 (대부분의 작업은 어느 정도 복구 가능)
    return max(recovery_score, 0.7)


def _evaluate_friction_reduction(state: GraphState) -> float:
    """마찰 제거(孝): 사용자 경험 개선 평가"""
    # 기존 outputs 확인으로 마찰 감소 평가
    outputs = state.outputs or {}

    friction_score = 0.0

    # 다른 노드들의 평가가 있는지 확인 (협력적 평가)
    if "TRUTH" in outputs:
        friction_score += 0.2  # 타입 안전성으로 인지 부하 감소

    if "GOODNESS" in outputs:
        friction_score += 0.2  # 보안 검증으로 신뢰성 향상

    if "BEAUTY" in outputs:
        friction_score += 0.2  # 일관된 UX로 학습 비용 감소

    # 기본 마찰 감소 점수 (어떤 자동화든 어느 정도 도움)
    base_friction = 0.4

    return min(friction_score + base_friction, 1.0)
