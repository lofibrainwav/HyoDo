"""
🎯 AFO Kingdom Metis Agent (Phase 80)
계획 검토 및 최적화 특화 에이전트

작성자: 승상 (Chancellor)
날짜: 2026-01-22

역할: 계획 타당성 검증, 대안 분석, 최적화 기회 식별
모델: Claude Sonnet 4.5 (균형 잡힌 평가용)
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from AFO.background_agents import BackgroundAgent
from AFO.meritocracy_router import SelectionEvidence, meritocracy_router

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluationCriteria(Enum):
    """평가 기준 열거형"""

    FEASIBILITY = "feasibility"
    IMPACT = "impact"
    EFFORT = "effort"
    RISK = "risk"
    ALIGNMENT = "alignment"
    SCALABILITY = "scalability"


@dataclass
class PlanEvaluation:
    """계획 평가 결과 데이터 클래스"""

    evaluation_id: str
    plan_id: str
    plan_type: str  # 'strategic_goal', 'task', 'roadmap', 'resource_plan'
    evaluator_agent: str
    evaluation_criteria: dict[str, float]  # 기준별 점수 (0.0 - 1.0)
    overall_score: float  # 종합 점수
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    alternative_solutions: list[dict[str, Any]]
    confidence_level: float
    evaluation_date: float
    validity_period: int  # 유효 기간 (일)


@dataclass
class OptimizationOpportunity:
    """최적화 기회 데이터 클래스"""

    opportunity_id: str
    target_type: str  # 'process', 'resource', 'timeline', 'quality'
    target_id: str
    description: str
    potential_impact: float  # 잠재적 개선 효과 (0.0 - 1.0)
    implementation_effort: str  # 'low', 'medium', 'high'
    dependencies: list[str]
    risk_level: str  # 'low', 'medium', 'high'
    priority_score: float  # 자동 계산된 우선순위
    status: str  # 'identified', 'analyzing', 'recommended', 'implemented'
    identified_date: float
    recommended_actions: list[str]


class MetisAgent(BackgroundAgent):
    """
    Metis Agent: 계획 검토 및 최적화 특화 에이전트

    역할:
    - 계획 타당성 검증
    - 대안 시나리오 분석
    - 최적화 기회 식별
    - 실행 가능성 평가
    """

    def __init__(self):
        super().__init__("metis", "Metis Agent")
        self.plan_evaluations: dict[str, PlanEvaluation] = {}
        self.optimization_opportunities: dict[str, OptimizationOpportunity] = {}
        self.evaluation_cache: dict[str, dict[str, Any]] = {}

        # 평가 파라미터
        self.min_confidence_threshold = 0.7  # 최소 신뢰도 임계값
        self.evaluation_validity_days = 7  # 평가 유효 기간
        self.optimization_priority_threshold = 0.6  # 최적화 우선순위 임계값

        # Meritocracy Router 통합
        self.meritocracy_router = meritocracy_router
        self.current_model = "claude-sonnet-4.5"  # 초기 기본값
        self.last_model_selection: SelectionEvidence | None = None

        logger.info("Metis Agent initialized with Meritocracy Router")

    async def execute_cycle(self) -> None:
        """
        Metis Agent의 주요 실행 로직

        수행 작업:
        1. 계획 평가 및 검증
        2. 최적화 기회 탐색
        3. 대안 시나리오 분석
        4. 실행 가능성 재평가
        """

        try:
            # 1. 계획 평가 업데이트
            await self._update_plan_evaluations()

            # 2. 최적화 기회 탐색
            await self._discover_optimization_opportunities()

            # 3. 대안 분석
            await self._analyze_alternative_scenarios()

            # 4. 실행 가능성 검증
            await self._validate_feasibility()

            logger.info("Metis cycle completed. Plan evaluation and optimization updated.")

        except Exception as e:
            logger.error(f"Metis cycle error: {e}")
            self.status.error_count += 1

    async def _update_plan_evaluations(self) -> None:
        """계획 평가 업데이트"""
        current_time = time.time()

        # 만료된 평가 정리
        expired_evaluations = [
            eval_id
            for eval_id, evaluation in self.plan_evaluations.items()
            if current_time - evaluation.evaluation_date
            > (evaluation.validity_period * 24 * 60 * 60)
        ]

        for eval_id in expired_evaluations:
            del self.plan_evaluations[eval_id]

        # 새로운 평가 대상 식별 및 평가
        new_evaluation_targets = await self._identify_evaluation_targets()

        for target in new_evaluation_targets:
            evaluation = await self._evaluate_plan(target)
            self.plan_evaluations[evaluation.evaluation_id] = evaluation

    async def _discover_optimization_opportunities(self) -> None:
        """최적화 기회 탐색"""
        # 다양한 영역에서 최적화 기회 식별
        optimization_areas = [
            "process_efficiency",
            "resource_utilization",
            "timeline_optimization",
            "quality_improvement",
            "risk_mitigation",
        ]

        for area in optimization_areas:
            opportunities = await self._analyze_area_for_optimization(area)

            for opp_data in opportunities:
                opportunity = OptimizationOpportunity(
                    opportunity_id=f"opt_{int(time.time())}_{len(self.optimization_opportunities)}",
                    target_type=opp_data["target_type"],
                    target_id=opp_data["target_id"],
                    description=opp_data["description"],
                    potential_impact=opp_data["potential_impact"],
                    implementation_effort=opp_data["implementation_effort"],
                    dependencies=opp_data["dependencies"],
                    risk_level=opp_data["risk_level"],
                    priority_score=self._calculate_optimization_priority(opp_data),
                    status="identified",
                    identified_date=time.time(),
                    recommended_actions=opp_data["recommended_actions"],
                )
                self.optimization_opportunities[opportunity.opportunity_id] = opportunity

        # 우선순위 재계산 및 정리
        await self._prioritize_optimization_opportunities()

    async def _analyze_alternative_scenarios(self) -> None:
        """대안 시나리오 분석"""
        # 주요 계획에 대한 대안 시나리오 개발
        critical_plans = await self._identify_critical_plans()

        for plan in critical_plans:
            alternatives = await self._generate_alternative_scenarios(plan)

            # 각 평가에 대안 추가
            for eval_id, evaluation in self.plan_evaluations.items():
                if evaluation.plan_id == plan["id"]:
                    evaluation.alternative_solutions = alternatives
                    break

    async def _validate_feasibility(self) -> None:
        """실행 가능성 검증"""
        # 모든 계획의 실행 가능성 재검증
        for evaluation in self.plan_evaluations.values():
            if evaluation.confidence_level < self.min_confidence_threshold:
                await self._reevaluate_plan_feasibility(evaluation)

    # 평가 관련 헬퍼 메서드들

    async def _identify_evaluation_targets(self) -> list[dict[str, Any]]:
        """평가 대상 식별"""
        # 실제로는 다른 에이전트나 시스템에서 계획을 가져옴
        # 현재는 시뮬레이션

        evaluation_targets = [
            {
                "id": "goal_multi_agent_orchestration",
                "type": "strategic_goal",
                "description": "Multi-Agent 오케스트레이션 시스템 완성",
                "priority": "critical",
            },
            {
                "id": "resource_plan_q1",
                "type": "resource_plan",
                "description": "Q1 자원 할당 계획",
                "priority": "high",
            },
        ]

        return evaluation_targets

    async def _evaluate_plan(self, plan: dict[str, Any]) -> PlanEvaluation:
        """계획 평가 수행"""
        evaluation_id = f"eval_{plan['id']}_{int(time.time())}"

        # 각 평가 기준에 대한 점수 계산 (시뮬레이션)
        criteria_scores = {}
        for criterion in EvaluationCriteria:
            criteria_scores[criterion.value] = await self._evaluate_criterion(plan, criterion)

        overall_score = sum(criteria_scores.values()) / len(criteria_scores)

        # 강점, 약점, 권장사항 식별 (시뮬레이션)
        strengths, weaknesses, recommendations = await self._analyze_plan_qualities(
            plan, criteria_scores
        )

        return PlanEvaluation(
            evaluation_id=evaluation_id,
            plan_id=plan["id"],
            plan_type=plan["type"],
            evaluator_agent=self.agent_id,
            evaluation_criteria=criteria_scores,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            alternative_solutions=[],  # 대안 분석에서 추가됨
            confidence_level=0.85,
            evaluation_date=time.time(),
            validity_period=self.evaluation_validity_days,
        )

    async def _evaluate_criterion(
        self, plan: dict[str, Any], criterion: EvaluationCriteria
    ) -> float:
        """특정 평가 기준에 대한 점수 계산"""
        # 실제로는 복잡한 분석 로직
        # 현재는 시뮬레이션

        base_scores = {
            EvaluationCriteria.FEASIBILITY: 0.8,
            EvaluationCriteria.IMPACT: 0.9,
            EvaluationCriteria.EFFORT: 0.6,
            EvaluationCriteria.RISK: 0.7,
            EvaluationCriteria.ALIGNMENT: 0.85,
            EvaluationCriteria.SCALABILITY: 0.75,
        }

        score = base_scores[criterion]

        # 계획 특성에 따른 조정
        if plan["priority"] == "critical":
            score += 0.1
        elif plan["priority"] == "low":
            score -= 0.1

        return min(1.0, max(0.0, score))

    async def _analyze_plan_qualities(
        self, plan: dict[str, Any], criteria_scores: dict[str, float]
    ) -> tuple[list[str], list[str], list[str]]:
        """계획의 강점, 약점, 권장사항 분석"""
        strengths = []
        weaknesses = []
        recommendations = []

        # 강점 식별
        for criterion, score in criteria_scores.items():
            if score >= 0.8:
                strengths.append(f"{criterion} 측면에서 우수한 성과 예상")
            elif score <= 0.6:
                weaknesses.append(f"{criterion} 측면에서 개선이 필요함")

        # 권장사항 생성
        if any(score < 0.7 for score in criteria_scores.values()):
            recommendations.append("리스크 평가 및 완화 전략 강화 고려")

        if criteria_scores.get("scalability", 0) < 0.8:
            recommendations.append("장기적 확장성 확보를 위한 아키텍처 검토")

        if criteria_scores.get("effort", 0) > 0.8:
            recommendations.append("구현 난이도 재평가 및 자원 추가 투입 고려")

        return strengths, weaknesses, recommendations

    # 최적화 관련 헬퍼 메서드들

    async def _analyze_area_for_optimization(self, area: str) -> list[dict[str, Any]]:
        """특정 영역의 최적화 기회 분석"""
        # 실제로는 해당 영역의 메트릭과 데이터를 분석
        # 현재는 시뮬레이션

        opportunities_by_area = {
            "process_efficiency": [
                {
                    "target_type": "process",
                    "target_id": "agent_orchestration",
                    "description": "에이전트 간 통신 프로토콜 최적화로 20% 성능 향상 가능",
                    "potential_impact": 0.8,
                    "implementation_effort": "medium",
                    "dependencies": ["communication_bus"],
                    "risk_level": "low",
                    "recommended_actions": ["비동기 메시지 큐 도입", "프로토콜 압축 적용"],
                }
            ],
            "resource_utilization": [
                {
                    "target_type": "resource",
                    "target_id": "compute_allocation",
                    "description": "자원 할당 알고리즘 개선으로 15% 효율성 향상 가능",
                    "potential_impact": 0.6,
                    "implementation_effort": "low",
                    "dependencies": ["resource_manager"],
                    "risk_level": "low",
                    "recommended_actions": ["동적 할당 알고리즘 구현", "사용량 모니터링 강화"],
                }
            ],
            "timeline_optimization": [
                {
                    "target_type": "timeline",
                    "target_id": "critical_path",
                    "description": "병렬 처리 도입으로 25% 일정 단축 가능",
                    "potential_impact": 0.7,
                    "implementation_effort": "high",
                    "dependencies": ["task_scheduler"],
                    "risk_level": "medium",
                    "recommended_actions": ["병렬 실행 파이프라인 구축", "의존성 그래프 최적화"],
                }
            ],
        }

        return opportunities_by_area.get(area, [])

    def _calculate_optimization_priority(self, opportunity_data: dict[str, Any]) -> float:
        """최적화 기회 우선순위 계산"""
        impact = opportunity_data["potential_impact"]
        effort_multipliers = {"low": 1.0, "medium": 0.8, "high": 0.6}
        risk_multipliers = {"low": 1.0, "medium": 0.9, "high": 0.7}

        effort_multiplier = effort_multipliers[opportunity_data["implementation_effort"]]
        risk_multiplier = risk_multipliers[opportunity_data["risk_level"]]

        priority = impact * effort_multiplier * risk_multiplier
        return min(1.0, priority)

    async def _prioritize_optimization_opportunities(self) -> None:
        """최적화 기회 우선순위 재계산 및 정리"""
        # 우선순위 임계값 이상인 기회만 유지
        high_priority_opportunities = {
            opp_id: opp
            for opp_id, opp in self.optimization_opportunities.items()
            if opp.priority_score >= self.optimization_priority_threshold
        }

        self.optimization_opportunities = high_priority_opportunities

        # 우선순위별 정렬 (상위 10개만 유지)
        sorted_opportunities = sorted(
            self.optimization_opportunities.values(), key=lambda x: x.priority_score, reverse=True
        )

        if len(sorted_opportunities) > 10:
            keep_ids = {opp.opportunity_id for opp in sorted_opportunities[:10]}
            self.optimization_opportunities = {
                opp_id: opp
                for opp_id, opp in self.optimization_opportunities.items()
                if opp_id in keep_ids
            }

    # 대안 분석 관련 헬퍼 메서드들

    async def _identify_critical_plans(self) -> list[dict[str, Any]]:
        """중요 계획 식별"""
        # 평가 점수가 낮거나 우선순위가 높은 계획들
        critical_plans = []

        for evaluation in self.plan_evaluations.values():
            if evaluation.overall_score < 0.8 or evaluation.plan_type == "strategic_goal":
                critical_plans.append(
                    {
                        "id": evaluation.plan_id,
                        "type": evaluation.plan_type,
                        "current_score": evaluation.overall_score,
                    }
                )

        return critical_plans[:5]  # 최대 5개

    async def _generate_alternative_scenarios(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        """대안 시나리오 생성"""
        alternatives = []

        # 기본 전략에 대한 대안들 생성
        if plan["type"] == "strategic_goal":
            alternatives = [
                {
                    "scenario_name": "Accelerated Approach",
                    "description": "빠른 프로토타이핑과 반복적 개선 중심 접근",
                    "pros": ["빠른 결과 도출", "유연한 방향 전환 가능"],
                    "cons": ["품질 저하 위험", "기술 부채 축적 가능"],
                    "estimated_effort": "medium",
                    "estimated_impact": "high",
                },
                {
                    "scenario_name": "Conservative Approach",
                    "description": "철저한 계획 수립과 단계적 구현",
                    "pros": ["안정적인 진행", "높은 품질 보장"],
                    "cons": ["느린 진행 속도", "기회 손실 가능"],
                    "estimated_effort": "high",
                    "estimated_impact": "medium",
                },
                {
                    "scenario_name": "Hybrid Approach",
                    "description": "핵심 부분은 신속하게, 세부 사항은 철저하게",
                    "pros": ["균형 잡힌 접근", "리스크 분산"],
                    "cons": ["복잡한 관리 필요"],
                    "estimated_effort": "medium",
                    "estimated_impact": "high",
                },
            ]

        return alternatives

    async def _reevaluate_plan_feasibility(self, evaluation: PlanEvaluation) -> None:
        """계획 실행 가능성 재평가"""
        # 실행 가능성에 영향을 미치는 새로운 요인들 고려
        # 실제로는 최신 데이터와 상황을 반영한 재평가

        evaluation.confidence_level = min(1.0, evaluation.confidence_level + 0.1)
        evaluation.evaluation_date = time.time()

        logger.info(
            f"Re-evaluated feasibility for plan {evaluation.plan_id}: "
            f"confidence now {evaluation.confidence_level:.2f}"
        )

    async def get_metrics(self) -> dict[str, Any]:
        """Metis Agent 메트릭 반환"""
        total_evaluations = len(self.plan_evaluations)
        total_opportunities = len(self.optimization_opportunities)

        avg_evaluation_score = (
            sum(e.overall_score for e in self.plan_evaluations.values()) / total_evaluations
            if total_evaluations > 0
            else 0
        )

        avg_opportunity_impact = (
            sum(o.potential_impact for o in self.optimization_opportunities.values())
            / total_opportunities
            if total_opportunities > 0
            else 0
        )

        # 평가 상태 분포
        evaluation_status = {}
        for evaluation in self.plan_evaluations.values():
            status = (
                "valid"
                if evaluation.confidence_level >= self.min_confidence_threshold
                else "needs_review"
            )
            evaluation_status[status] = evaluation_status.get(status, 0) + 1

        # 최적화 기회 상태 분포
        opportunity_status = {}
        for opportunity in self.optimization_opportunities.values():
            opportunity_status[opportunity.status] = (
                opportunity_status.get(opportunity.status, 0) + 1
            )

        return {
            "agent_type": "metis",
            "plan_evaluations": total_evaluations,
            "optimization_opportunities": total_opportunities,
            "avg_evaluation_score": avg_evaluation_score,
            "avg_opportunity_impact": avg_opportunity_impact,
            "evaluation_status_distribution": evaluation_status,
            "opportunity_status_distribution": opportunity_status,
            "current_model": self.current_model,
            "meritocracy_enabled": True,
        }

    # Public API methods

    async def evaluate_plan(self, plan_data: dict[str, Any]) -> PlanEvaluation:
        """
        계획 평가 수행

        Args:
            plan_data: 평가할 계획 데이터

        Returns:
            평가 결과
        """
        return await self._evaluate_plan(plan_data)

    async def get_optimization_recommendations(self, limit: int = 5) -> list[dict[str, Any]]:
        """
        최적화 추천사항 조회

        Args:
            limit: 반환할 추천사항 수

        Returns:
            우선순위별 최적화 추천사항
        """
        sorted_opportunities = sorted(
            self.optimization_opportunities.values(), key=lambda x: x.priority_score, reverse=True
        )

        recommendations = []
        for opportunity in sorted_opportunities[:limit]:
            recommendations.append(
                {
                    "id": opportunity.opportunity_id,
                    "description": opportunity.description,
                    "impact": opportunity.potential_impact,
                    "effort": opportunity.implementation_effort,
                    "priority": opportunity.priority_score,
                    "actions": opportunity.recommended_actions,
                }
            )

        return recommendations

    async def analyze_alternatives(self, plan_id: str) -> list[dict[str, Any]]:
        """
        계획에 대한 대안 분석

        Args:
            plan_id: 분석할 계획 ID

        Returns:
            대안 시나리오 리스트
        """
        # 해당 계획의 평가에서 대안 가져오기
        for evaluation in self.plan_evaluations.values():
            if evaluation.plan_id == plan_id:
                return evaluation.alternative_solutions

        return []

    async def validate_feasibility(self, plan_data: dict[str, Any]) -> dict[str, Any]:
        """
        실행 가능성 검증

        Args:
            plan_data: 검증할 계획 데이터

        Returns:
            실행 가능성 평가 결과
        """
        evaluation = await self._evaluate_plan(plan_data)

        return {
            "feasible": evaluation.overall_score >= 0.7,
            "confidence": evaluation.confidence_level,
            "score": evaluation.overall_score,
            "strengths": evaluation.strengths,
            "weaknesses": evaluation.weaknesses,
            "recommendations": evaluation.recommendations,
        }


# 글로벌 인스턴스
metis_agent = MetisAgent()


# 유틸리티 함수들
async def evaluate_plan(plan_data: dict[str, Any]) -> PlanEvaluation:
    """계획 평가 유틸리티"""
    return await metis_agent.evaluate_plan(plan_data)


async def get_optimization_recommendations(limit: int = 5) -> list[dict[str, Any]]:
    """최적화 추천 유틸리티"""
    return await metis_agent.get_optimization_recommendations(limit)


async def analyze_alternatives(plan_id: str) -> list[dict[str, Any]]:
    """대안 분석 유틸리티"""
    return await metis_agent.analyze_alternatives(plan_id)


async def validate_feasibility(plan_data: dict[str, Any]) -> dict[str, Any]:
    """실행 가능성 검증 유틸리티"""
    return await metis_agent.validate_feasibility(plan_data)


if __name__ == "__main__":
    # 직접 실행 시 데모
    async def demo():
        print("🎯 Metis Agent Phase 80 데모")
        print("=" * 50)

        # 초기화
        agent = MetisAgent()

        # 계획 평가 데모
        plan_data = {
            "id": "test_plan",
            "type": "strategic_goal",
            "description": "AI 에이전트 시스템 구축",
            "priority": "high",
        }

        evaluation = await agent.evaluate_plan(plan_data)
        print(f"✅ 계획 평가 완료: {evaluation.evaluation_id}")
        print(f"   종합 점수: {evaluation.overall_score:.2f}")
        print(f"   신뢰도: {evaluation.confidence_level:.2f}")

        # 메트릭 출력
        metrics = await agent.get_metrics()
        print("\n📊 Metis Agent 메트릭:")
        print(f"  • 계획 평가: {metrics['plan_evaluations']}개")
        print(f"  • 최적화 기회: {metrics['optimization_opportunities']}개")
        print(f"  • 평균 평가 점수: {metrics['avg_evaluation_score']:.2f}")
        print(f"  • 평균 최적화 영향: {metrics['avg_opportunity_impact']:.2f}")

        # 최적화 추천사항
        recommendations = await agent.get_optimization_recommendations(3)
        print("\n💡 최적화 추천사항:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['description'][:60]}... (영향도: {rec['impact']:.1f})")

        print("\n✅ Metis Agent 데모 완료!")

    asyncio.run(demo())
