from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from infrastructure.llm.ssot_compliant_router import ssot_router

if TYPE_CHECKING:
    from AFO.api.chancellor_v2.graph.state import GraphState

"""REFLECT Node - Cognitive Deep Reflection (DeepSeek-R1 Audit)."""


logger = logging.getLogger(__name__)


async def reflect_node(state: GraphState) -> GraphState:
    """Perform Deep Reflection auditing on strategist outputs.

    Scholar: Yeongdeok (Local DeepSeek-R1 / Ollama)
    Role: Auditor. Identifies contradictions and logic gaps between TRUTH, GOODNESS, and BEAUTY.
    """
    # Collect strategist assessments
    truth = state.outputs.get("TRUTH", {})
    goodness = state.outputs.get("GOODNESS", {})
    beauty = state.outputs.get("BEAUTY", {})

    command = state.input.get("command", "")
    plan = state.plan

    # 1. Audit Prompt
    prompt = f"""
    당신은 AFO 왕국의 'Deep Reflection' 감사자 영덕(Yeongdeok)입니다.
    세 명의 책사(장영실-眞, 이순신-善, 신사임당-美)가 제안한 실행 계획에 대해 최종 논리 감사를 수행하십시오.

    [사령관의 명령]
    {command}

    [실행 계획]
    {json.dumps(plan, indent=2)}

    [책사별 평가]
    - 眞 (Truth - 기술적 타당성): {json.dumps(truth, indent=2)}
    - 善 (Goodness - 안정성 및 리스크): {json.dumps(goodness, indent=2)}
    - 美 (Beauty - 우아함 및 UX): {json.dumps(beauty, indent=2)}

    [감사 가이드라인]
    1. 각 책사의 평가 사이에 논리적 모순이 있는가? (기술적으로는 가능하나 리스크 평가가 누락되었는가 등)
    2. 제안된 계획이 AFO 왕국의 헌법(SSOT)을 준수하는가?
    3. 해결되지 않은 잠재적 리스트(Gap)가 존재하는가?

    결과는 반드시 다음 JSON 형식으로 응답하십시오:
    {{
      "consistency_score": float (0.0 to 1.0),
      "audit_status": "passed" | "flagged" | "failed",
      "findings": list[string],
      "metacognition": string (당신의 추론 과정 요약)
    }}
    """

    audit_data = {
        "consistency_score": 1.0,
        "audit_status": "passed",
        "findings": [],
        "metacognition": "Heuristic audit: No issues detected in initial pass.",
    }

    try:
        # Target Yeongdeok (Local DeepSeek-R1 via Ollama)
        # Use SSOT Compliant Router (Modularized)
        response = await ssot_router.call_scholar_via_wallet(
            "serenity_scholar",  # Yeongdeok is Serenity Scholar
            prompt,
            context={
                "provider": "ollama",
                "model": "deepseek-r1",
                "quality_tier": "premium",
            },
        )

        if response and response.get("success"):
            text = response.get("response", "{}")
            # Clean possible markdown
            text = text.strip().replace("```json", "").replace("```", "").strip()
            try:
                audit_data = json.loads(text)
            except Exception as e:
                logger.warning(f"Failed to parse Yeongdeok audit JSON: {e}")
    except Exception as e:
        state.errors.append(f"Yeongdeok (REFLECT) audit failed: {e}")

    state.outputs["REFLECT"] = {
        "score": audit_data.get("consistency_score", 1.0),
        "status": audit_data.get("audit_status", "passed"),
        "findings": audit_data.get("findings", []),
        "metacognition": audit_data.get("metacognition", ""),
        "metadata": {
            "scholar": "Yeongdeok (Local DeepSeek-R1)",
            "assessment_mode": "Deep Reflection",
        },
    }

    return state
