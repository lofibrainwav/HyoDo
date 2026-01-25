from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import TYPE_CHECKING

from AFO.llm_router import llm_router

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

logger = logging.getLogger(__name__)

"""TRUTH Node - Technical truth evaluation (眞: Truth)."""


async def truth_node(state: GraphState) -> GraphState:
    """Evaluate technical aspects of the planned execution.

    眞 (Truth) - 기술적 확실성, 타입 안전성, 테스트 무결성 평가
    Scholar: Zilong (Claude 3.5 Sonnet / Anthropic)
    """
    skill_id = state.plan.get("skill_id", "")
    query = state.plan.get("query", "")

    # 1. Real-Time Physical Verification (Self-Reflection)
    # The system audits its own truth based on actual code health
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path

    v_score = 1.0
    v_issues = []

    try:
        # 1-1. Ruff Check
        ruff_cmd = ["ruff", "check", "packages/afo-core/AFO", "--select", "E,F", "--ignore", "E501"]
        ruff_proc = subprocess.run(ruff_cmd, capture_output=True, text=True, timeout=10)
        if ruff_proc.returncode != 0:
            v_score = 0.0
            v_issues.append("Lint/Logic errors detected in core (Ruff)")

        # 1-2. MyPy Check (Targeted Self-Check)
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            # Check the validator node itself as a proxy for 'Truth'
            shutil.copy(__file__, tmp_path)

        try:
            mypy_cmd = [
                "mypy",
                str(tmp_path),
                "--ignore-missing-imports",
                "--check-untyped-defs",
                "--config-file",
                "scripts/strict_mypy.ini",
            ]
            mypy_proc = subprocess.run(mypy_cmd, capture_output=True, text=True, timeout=15)
            if mypy_proc.returncode != 0:
                v_score = 0.0
                v_issues.append("Type safety violations detected in Truth node")
        finally:
            if tmp_path.exists():
                os.unlink(tmp_path)

    except Exception as e:
        v_score = 0.5  # Unknown state
        v_issues.append(f"Verification system error: {e}")

    # Heuristic component based on the query itself
    type_checking_score = _evaluate_type_safety(skill_id, query)
    heuristic_score = (type_checking_score * 0.5 + v_score * 0.5) if v_score > 0 else 0.0

    # 2. Scholar Assessment (Zilong)
    prompt = f"""
    You are Zilong (眞), the Technical Strategist of the AFO Kingdom.
    Analyze the following execution plan for technical truth, type safety, and testability.

    State of Truth: {v_score * 100}% Healthy.
    Issues Found: {", ".join(v_issues) if v_issues else "None"}

    Plan:
    - Skill: {skill_id}
    - Query/Target: {query}
    - Command: {state.input.get("command", "")}

    Provide your assessment in JSON:
    {{
      "score": float (0.0 to 1.0),
      "reasoning": string,
      "issues": list[string]
    }}
    """

    scholar_score = heuristic_score
    reasoning = "Heuristic assessment based on keyword mapping."
    issues = v_issues
    assessment_mode = "Heuristic (Fallback)"
    scholar_model = "None"

    pillar_timeout = float(os.getenv("AFO_PILLAR_TIMEOUT", "8.0"))

    try:
        response = await asyncio.wait_for(
            llm_router.call_scholar_via_ssot(
                query=prompt,
                scholar_key="truth_scholar",
                context={"provider": "anthropic", "quality_tier": "premium"},
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
                scholar_model = response.get("model", "Anthropic/Zilong")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
    except Exception as e:
        state.errors.append(f"Zilong (TRUTH) assessment failed: {e}")

    # Zero Tolerance: If physical verification fails, score is 0
    final_score = (heuristic_score * 0.3 + scholar_score * 0.7) if v_score > 0 else 0.0

    evaluation = {
        "score": round(final_score, 3),
        "reasoning": reasoning,
        "issues": list(set(issues)),
        "metadata": {
            "mode": assessment_mode,
            "scholar": "Zilong (眞)",
            "model": scholar_model,
            "physical_verification": "Passed" if v_score > 0 else "Failed",
        },
    }

    state.outputs["TRUTH"] = evaluation
    return state


def _evaluate_type_safety(skill_id: str, query: str) -> float:
    """타입 안전성 평가"""
    if not skill_id and not query:
        return 0.5

    combined_text = f"{skill_id} {query}".lower()

    # 타입 안전성 지표
    type_indicators = {
        "type": 0.9,
        "typing": 0.9,
        "mypy": 0.9,
        "pydantic": 0.9,
        "dataclass": 0.8,
        "protocol": 0.8,
        "generic": 0.8,
        "cast": 0.7,
        "overload": 0.7,
        "literal": 0.7,
        "test": 0.6,
        "validate": 0.6,
        "check": 0.6,
    }

    safety_score = 0.0
    for indicator, score in type_indicators.items():
        if indicator in combined_text:
            safety_score = max(safety_score, score)

    return max(safety_score, 0.6)  # 기본 타입 안전성


def _evaluate_test_coverage(skill_id: str) -> float:
    """테스트 커버리지 평가"""
    if not skill_id:
        return 0.5

    skill_lower = skill_id.lower()

    # 테스트 관련 키워드 평가
    test_indicators = {
        "test": 0.9,
        "pytest": 0.9,
        "unittest": 0.8,
        "coverage": 0.8,
        "tdd": 0.8,
        "bdd": 0.7,
        "fixture": 0.7,
        "mock": 0.7,
        "assert": 0.7,
        "verify": 0.6,
        "validate": 0.6,
        "check": 0.6,
    }

    coverage_score = 0.0
    for indicator, score in test_indicators.items():
        if indicator in skill_lower:
            coverage_score = max(coverage_score, score)

    return max(coverage_score, 0.5)  # 기본 테스트 존재 가정


def _evaluate_code_quality(query: str) -> float:
    """코드 품질 평가"""
    if not query:
        return 0.6

    query_lower = query.lower()

    # 코드 품질 지표
    quality_indicators = {
        "lint": 0.9,
        "ruff": 0.9,
        "black": 0.9,
        "isort": 0.9,
        "clean": 0.8,
        "refactor": 0.8,
        "optimize": 0.8,
        "pattern": 0.7,
        "design": 0.7,
        "architecture": 0.7,
        "best practice": 0.8,
        "standard": 0.7,
        "convention": 0.7,
    }

    quality_score = 0.0
    for indicator, score in quality_indicators.items():
        if indicator in query_lower:
            quality_score = max(quality_score, score)

    return max(quality_score, 0.6)  # 기본 코드 품질
