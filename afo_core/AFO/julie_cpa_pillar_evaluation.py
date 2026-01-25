"""
Julie CPA Pillar Scholar Evaluation System

Uses AFO Kingdom's 5 Pillar Scholars (眞善美孝永) to evaluate and improve
Julie CPA's Trinity Score and overall performance.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from infrastructure.llm.ssot_compliant_router import call_scholar


class JulieCPAPillarEvaluator:
    """Julie CPA 평가를 위한 Pillar Scholar 시스템"""

    def __init__(self) -> None:
        self.pillar_scholars = [
            "truth_scholar",  # 眞 - 기술적 확실성 평가
            "goodness_scholar",  # 善 - 윤리적 안정성 평가
            "beauty_scholar",  # 美 - UX/서사 일관성 평가
            "serenity_scholar",  # 孝 - 평온/마찰 제거 평가
            "eternity_scholar",  # 永 - 영속성/문서화 평가
        ]

    async def evaluate_julie_cpa_agent(
        self, agent_type: str, agent_output: dict[str, Any]
    ) -> dict[str, Any]:
        """Julie CPA Agent의 출력을 Pillar Scholars로 종합 평가"""

        evaluation_tasks = []
        for scholar in self.pillar_scholars:
            task = self._evaluate_with_scholar(scholar, agent_type, agent_output)
            evaluation_tasks.append(task)

        # 모든 Pillar Scholar 평가를 병렬로 실행
        scholar_evaluations = await asyncio.gather(*evaluation_tasks, return_exceptions=True)

        # 평가 결과 종합
        consolidated_evaluation = self._consolidate_evaluations(scholar_evaluations, agent_type)

        return {
            "agent_type": agent_type,
            "evaluation_timestamp": datetime.now().isoformat(),
            "pillar_evaluations": scholar_evaluations,
            "consolidated_score": consolidated_evaluation,
            "recommendations": self._generate_improvement_recommendations(consolidated_evaluation),
        }

    async def _evaluate_with_scholar(
        self, scholar_key: str, agent_type: str, agent_output: dict[str, Any]
    ) -> dict[str, Any]:
        """특정 Pillar Scholar로 평가 수행"""

        scholar_prompts = {
            "truth_scholar": f"""
            Evaluate the technical accuracy and correctness of this Julie CPA {agent_type} output.
            Focus on: data accuracy, calculation correctness, IRS compliance, evidence validation.
            Rate the technical truthfulness on a scale of 0-1.0.

            Agent Output: {json.dumps(agent_output, indent=2)}

            Provide detailed reasoning and a truth score.
            """,
            "goodness_scholar": f"""
            Evaluate the ethical soundness and regulatory compliance of this Julie CPA {agent_type} output.
            Focus on: client privacy, regulatory adherence, risk management, professional standards.
            Rate the ethical goodness on a scale of 0-1.0.

            Agent Output: {json.dumps(agent_output, indent=2)}

            Provide detailed reasoning and a goodness score.
            """,
            "beauty_scholar": f"""
            Evaluate the user experience and clarity of this Julie CPA {agent_type} output.
            Focus on: readability, structure, professional presentation, stakeholder understanding.
            Rate the aesthetic beauty on a scale of 0-1.0.

            Agent Output: {json.dumps(agent_output, indent=2)}

            Provide detailed reasoning and a beauty score.
            """,
            "serenity_scholar": f"""
            Evaluate how well this Julie CPA {agent_type} output reduces friction and maintains peace.
            Focus on: simplicity, conflict avoidance, stakeholder satisfaction, smooth workflows.
            Rate the serene harmony on a scale of 0-1.0.

            Agent Output: {json.dumps(agent_output, indent=2)}

            Provide detailed reasoning and a serenity score.
            """,
            "eternity_scholar": f"""
            Evaluate the durability and documentation quality of this Julie CPA {agent_type} output.
            Focus on: audit trail completeness, record preservation, future usability, compliance longevity.
            Rate the eternal preservation on a scale of 0-1.0.

            Agent Output: {json.dumps(agent_output, indent=2)}

            Provide detailed reasoning and an eternity score.
            """,
        }

        try:
            prompt = scholar_prompts.get(
                scholar_key, "Please evaluate this output comprehensively."
            )
            response = await call_scholar(prompt, scholar_key)

            # Scholar 응답에서 점수 추출 (간단한 파싱)
            response_text = response.get("response", "").lower()
            score = self._extract_score_from_response(response_text)

            return {
                "scholar": scholar_key,
                "evaluation": response.get("response", ""),
                "score": score,
                "trinity_score": response.get("trinity_score", {}),
                "success": response.get("success", False),
            }

        except Exception as e:
            return {
                "scholar": scholar_key,
                "evaluation": f"Evaluation failed: {e!s}",
                "score": 0.5,  # 중립 점수
                "error": str(e),
                "success": False,
            }

    def _extract_score_from_response(self, response_text: str) -> float:
        """Scholar 응답에서 점수 추출"""
        import re

        # 다양한 점수 표현 패턴 매칭
        patterns = [
            r"score:?\s*([0-1]?\.?\d+)",  # "score: 0.85"
            r"rate:?\s*([0-1]?\.?\d+)",  # "rate: 0.9"
            r"([0-1]?\.?\d+)\s*/?\s*1\.?0?",  # "0.85/1.0" 또는 "0.85"
            r"(\d+)%",  # "85%" - 백분율을 소수로 변환
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            if matches:
                score = float(matches[0])
                if "%" in matches[0]:
                    score = score / 100.0  # 백분율 변환
                return min(1.0, max(0.0, score))  # 0-1 범위 제한

        return 0.8  # 기본 중립 점수

    def _consolidate_evaluations(
        self, scholar_evaluations: list[Any], agent_type: str
    ) -> dict[str, Any]:
        """모든 Pillar Scholar 평가를 종합"""

        # 성공한 평가만 수집
        successful_evaluations = [
            e for e in scholar_evaluations if isinstance(e, dict) and e.get("success", False)
        ]

        if not successful_evaluations:
            return {
                "error": "No successful evaluations",
                "trinity_score": 50.0,
                "individual_scores": {},
            }

        # 개별 Pillar 점수 수집
        pillar_scores = {}
        for eval in successful_evaluations:
            scholar_key = eval.get("scholar", "").replace("_scholar", "")
            score = eval.get("score", 0.5)
            pillar_scores[scholar_key] = score

        # Trinity Score 계산 (AFO Kingdom 표준 가중치)
        trinity_score = (
            pillar_scores.get("truth", 0.8) * 0.35
            + pillar_scores.get("goodness", 0.8) * 0.35
            + pillar_scores.get("beauty", 0.8) * 0.20
            + pillar_scores.get("serenity", 0.8) * 0.08
            + 0.02  # eternity는 항상 최소값
        ) * 100

        return {
            "trinity_score": round(trinity_score, 1),
            "individual_scores": pillar_scores,
            "evaluation_count": len(successful_evaluations),
            "agent_type": agent_type,
            "evaluation_quality": "high" if len(successful_evaluations) >= 4 else "medium",
        }

    def _generate_improvement_recommendations(self, consolidated: dict[str, Any]) -> list[str]:
        """개선 권장사항 생성"""

        recommendations = []
        individual_scores = consolidated.get("individual_scores", {})

        # 각 Pillar별 개선 권장사항
        if individual_scores.get("truth", 1.0) < 0.8:
            recommendations.append(
                "Improve technical accuracy: enhance IRS regulation compliance and calculation precision"
            )

        if individual_scores.get("goodness", 1.0) < 0.8:
            recommendations.append(
                "Strengthen ethical safeguards: add more client privacy protections and regulatory compliance checks"
            )

        if individual_scores.get("beauty", 1.0) < 0.8:
            recommendations.append(
                "Enhance user experience: improve output formatting and stakeholder communication clarity"
            )

        if individual_scores.get("serenity", 1.0) < 0.8:
            recommendations.append(
                "Reduce friction: simplify workflows and minimize stakeholder conflicts"
            )

        # Trinity Score 기반 일반 권장사항
        trinity_score = consolidated.get("trinity_score", 0.0)
        if trinity_score < 85:
            recommendations.append(
                "Implement comprehensive quality improvement program across all pillars"
            )
        elif trinity_score < 95:
            recommendations.append("Focus on pillar-specific optimizations to achieve excellence")

        return recommendations

    async def continuous_improvement_cycle(
        self, agent_type: str, agent_output: dict[str, Any]
    ) -> dict[str, Any]:
        """지속적 개선 사이클 실행"""

        # 1. 현재 성능 평가
        evaluation = await self.evaluate_julie_cpa_agent(agent_type, agent_output)

        # 2. 개선 영역 식별
        improvement_areas = []
        individual_scores = evaluation.get("consolidated_score", {}).get("individual_scores", {})

        for pillar, score in individual_scores.items():
            if score < 0.85:
                improvement_areas.append(pillar)

        # 3. 개선 전략 수립
        improvement_strategy = await self._develop_improvement_strategy(
            improvement_areas, agent_type
        )

        return {
            "evaluation": evaluation,
            "improvement_areas": improvement_areas,
            "improvement_strategy": improvement_strategy,
            "next_evaluation_cycle": "weekly",  # 주기적 재평가 권장
        }

    async def _develop_improvement_strategy(
        self, improvement_areas: list[str], agent_type: str
    ) -> dict[str, Any]:
        """개선 전략 개발"""

        strategy = {
            "immediate_actions": [],
            "medium_term_goals": [],
            "long_term_vision": f"Achieve 95+ Trinity Score for {agent_type}",
            "success_metrics": [],
        }

        # 개선 영역별 전략
        for area in improvement_areas:
            if area == "truth":
                strategy["immediate_actions"].extend(
                    [
                        "Add automated IRS regulation cross-referencing",
                        "Implement calculation validation against multiple sources",
                    ]
                )
                strategy["success_metrics"].append("95%+ technical accuracy rate")

            elif area == "goodness":
                strategy["immediate_actions"].extend(
                    ["Strengthen audit trail generation", "Add automated compliance checking"]
                )
                strategy["success_metrics"].append("Zero regulatory compliance incidents")

            elif area == "beauty":
                strategy["immediate_actions"].extend(
                    [
                        "Redesign output templates for better readability",
                        "Add stakeholder-specific formatting options",
                    ]
                )
                strategy["success_metrics"].append("95%+ user satisfaction scores")

            elif area == "serenity":
                strategy["immediate_actions"].extend(
                    ["Simplify approval workflows", "Reduce manual intervention points"]
                )
                strategy["success_metrics"].append("50% reduction in processing friction")

        strategy["medium_term_goals"] = [
            "Achieve 90+ Trinity Score across all pillars",
            "Implement automated quality monitoring",
            "Establish continuous improvement feedback loops",
        ]

        return strategy


# 글로벌 인스턴스
julie_cpa_evaluator = JulieCPAPillarEvaluator()


async def evaluate_julie_cpa_output(
    agent_type: str, agent_output: dict[str, Any]
) -> dict[str, Any]:
    """
    Julie CPA 출력을 Pillar Scholars로 평가하는 헬퍼 함수

    Args:
        agent_type: Agent 타입 ("associate", "manager", "auditor")
        agent_output: Agent 출력 데이터

    Returns:
        종합 평가 결과
    """
    return await julie_cpa_evaluator.evaluate_julie_cpa_agent(agent_type, agent_output)


async def run_continuous_improvement(
    agent_type: str, agent_output: dict[str, Any]
) -> dict[str, Any]:
    """
    지속적 개선 사이클 실행 헬퍼 함수

    Args:
        agent_type: Agent 타입
        agent_output: Agent 출력 데이터

    Returns:
        개선 전략 및 다음 단계
    """
    return await julie_cpa_evaluator.continuous_improvement_cycle(agent_type, agent_output)


# 모듈 테스트
if __name__ == "__main__":

    async def test_evaluation():
        # 샘플 Julie CPA Associate 출력
        sample_output = {
            "draft_data": {
                "client_id": "SAMPLE_CLIENT",
                "tax_year": 2025,
                "issue_type": "roth_conversion",
                "calculations": {
                    "conversion_amount": 50000,
                    "marginal_rate": 0.22,
                    "tax_liability": 11000,
                },
            },
            "evidence_links": [
                {"type": "irs_publication", "reference": "IRS Pub 590-B"},
                {"type": "tax_document", "reference": "Client W-2"},
            ],
            "trinity_score": 0.82,
        }

        print("🧪 Testing Julie CPA Pillar Scholar Evaluation...")
        result = await evaluate_julie_cpa_output("associate", sample_output)

        print(
            f"📊 Trinity Score: {result.get('consolidated_score', {}).get('trinity_score', 'N/A')}"
        )
        print(f"📋 Recommendations: {len(result.get('recommendations', []))}")

        print("✅ Evaluation test completed!")

    asyncio.run(test_evaluation())
