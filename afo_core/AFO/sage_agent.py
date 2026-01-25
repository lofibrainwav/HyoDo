"""
🎯 AFO Kingdom Sage Agent (Phase 83)
고전 지식과 현대 AI의 전략적 결합 특화 에이전트

작성자: 승상 (Chancellor)
날짜: 2026-01-22

역할: 손자병법, 마키아벨리, 클라우제비츠 원칙 기반 전략 조언
모델: Claude Opus 4.5 (전략적 사고용)
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from AFO.background_agents import BackgroundAgent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StrategicWisdom:
    """전략적 지혜 데이터 클래스"""

    wisdom_id: str
    source: str  # 'sun_tzu', 'machiavelli', 'clausewitz', 'modern_ai'
    principle: str
    application: str
    confidence: float
    created_at: float


@dataclass
class StrategicAdvice:
    """전략적 조언 데이터 클래스"""

    advice_id: str
    context: str
    situation: str
    advice: str
    reasoning: str
    risk_level: str  # 'low', 'medium', 'high'
    expected_impact: float
    sage_agent: str
    created_at: float


class SageAgent(BackgroundAgent):
    """
    Sage Agent: 고전 지식과 현대 AI의 전략적 결합 특화 에이전트

    전략적 원칙:
    - 손자병법: 지피지기면 백전백승 (Know thyself, know thy enemy)
    - 마키아벨리: 목적은 수단을 정당화한다 (The ends justify the means)
    - 클라우제비츠: 전쟁은 정책의 연장이다 (War is the continuation of policy)
    """

    def __init__(self):
        super().__init__("sage", "Sage Agent")

        # 전략적 지혜 저장소
        self.strategic_wisdom: dict[str, StrategicWisdom] = {}
        self.strategic_advice: dict[str, StrategicAdvice] = {}

        # 전략적 원칙
        self.strategic_principles = {
            "sun_tzu": {
                "know_thyself": "지피지기면 백전백승",
                "adaptability": "적에 맞추어 변화하라",
                "deception": "적을 속이고 기회를 노려라",
                "timing": "때를 놓치지 말라",
            },
            "machiavelli": {
                "realism": "이상보다 현실을 봐라",
                "power": "힘과 영향력을 유지하라",
                "flexibility": "상황에 따라 원칙을 조정하라",
            },
            "clausewitz": {
                "center_gravity": "적의 중심을 공격하라",
                "friction": "전쟁의 마찰을 고려하라",
                "escalation": "목표에 따라 강도를 조절하라",
            },
        }

        # 모델 설정
        self.model_name = "claude-opus-4.5"

        logger.info("Sage Agent initialized - 고전과 현대의 전략적 결합")

    async def execute_cycle(self) -> None:
        """
        Sage Agent의 주요 실행 로직

        수행 작업:
        1. 전략적 지혜 축적
        2. 상황 분석 및 조언 생성
        3. 전략적 원칙 적용 검증
        4. 지식 베이스 업데이트
        """

        try:
            # 1. 전략적 지혜 축적
            await self._accumulate_wisdom()

            # 2. 상황 분석 및 조언
            await self._analyze_situations()

            # 3. 전략적 원칙 적용
            await self._apply_strategic_principles()

            # 4. 지식 베이스 최적화
            await self._optimize_knowledge_base()

            logger.info("Sage cycle completed. Strategic wisdom accumulated.")

        except Exception as e:
            logger.error(f"Sage cycle error: {e}")
            self.status.error_count += 1

    async def _accumulate_wisdom(self) -> None:
        """전략적 지혜 축적"""
        # 새로운 전략적 통찰을 축적
        wisdom_sources = ["sun_tzu", "machiavelli", "clausewitz", "modern_ai"]

        for source in wisdom_sources:
            new_wisdom = await self._extract_wisdom_from_source(source)
            for wisdom_data in new_wisdom:
                wisdom = StrategicWisdom(
                    wisdom_id=f"wisdom_{int(time.time())}_{len(self.strategic_wisdom)}",
                    source=source,
                    principle=wisdom_data["principle"],
                    application=wisdom_data["application"],
                    confidence=wisdom_data["confidence"],
                    created_at=time.time(),
                )
                self.strategic_wisdom[wisdom.wisdom_id] = wisdom

    async def _analyze_situations(self) -> None:
        """상황 분석 및 전략적 조언 생성"""
        # 현재 상황들을 분석하고 조언 생성
        situations = await self._identify_strategic_situations()

        for situation in situations:
            advice = await self._generate_strategic_advice(situation)
            self.strategic_advice[advice.advice_id] = advice

    async def _apply_strategic_principles(self) -> None:
        """전략적 원칙 적용 검증"""
        # 축적된 지혜를 현재 상황에 적용
        pass

    async def _optimize_knowledge_base(self) -> None:
        """지식 베이스 최적화"""
        # 오래된 또는 낮은 신뢰도의 지혜 정리
        cutoff_time = time.time() - (90 * 24 * 60 * 60)  # 90일
        low_confidence_threshold = 0.6

        wisdoms_to_remove = []
        for wisdom_id, wisdom in self.strategic_wisdom.items():
            if wisdom.created_at < cutoff_time or wisdom.confidence < low_confidence_threshold:
                wisdoms_to_remove.append(wisdom_id)

        for wisdom_id in wisdoms_to_remove:
            del self.strategic_wisdom[wisdom_id]

    async def _extract_wisdom_from_source(self, source: str) -> list[dict[str, Any]]:
        """특정 소스로부터 전략적 지혜 추출"""
        # 시뮬레이션 기반 지혜 추출
        wisdom_templates = {
            "sun_tzu": [
                {
                    "principle": "지피지기면 백전백승",
                    "application": "상대방과 자신의 강점을 정확히 파악하라",
                    "confidence": 0.95,
                }
            ],
            "machiavelli": [
                {
                    "principle": "목적은 수단을 정당화한다",
                    "application": "결과를 위해 필요한 조치를 취하라",
                    "confidence": 0.90,
                }
            ],
            "clausewitz": [
                {
                    "principle": "전쟁은 정책의 연장이다",
                    "application": "모든 행동은 더 큰 목표를 지원해야 한다",
                    "confidence": 0.92,
                }
            ],
            "modern_ai": [
                {
                    "principle": "지속적 학습과 적응",
                    "application": "변화하는 환경에 맞춰 전략을 조정하라",
                    "confidence": 0.88,
                }
            ],
        }

        return wisdom_templates.get(source, [])

    async def _identify_strategic_situations(self) -> list[dict[str, Any]]:
        """전략적 상황 식별"""
        # 현재 시스템 상태 기반 상황 식별
        situations = [
            {
                "id": "trinity_score_maintenance",
                "description": "Trinity Score 95점+ 유지",
                "context": "지속적 모니터링과 개선 필요",
                "urgency": "high",
            },
            {
                "id": "agent_expansion",
                "description": "새로운 Agent 통합",
                "context": "시스템 확장 및 최적화",
                "urgency": "medium",
            },
        ]

        return situations

    async def _generate_strategic_advice(self, situation: dict[str, Any]) -> StrategicAdvice:
        """전략적 조언 생성"""
        advice_id = f"advice_{situation['id']}_{int(time.time())}"

        # 상황에 맞는 조언 생성 (시뮬레이션)
        advice_text = ""
        reasoning = ""
        risk_level = "medium"
        expected_impact = 0.8

        if situation["id"] == "trinity_score_maintenance":
            advice_text = "지속적 모니터링 시스템 구축과 자동 개선 파이프라인 도입"
            reasoning = "손자병법 '지피지기' 원칙 적용: 시스템 상태를 지속적으로 파악하고 개선"
            risk_level = "low"
            expected_impact = 0.9
        elif situation["id"] == "agent_expansion":
            advice_text = "검증된 Agent들을 우선 통합하고 단계적 확장"
            reasoning = "클라우제비츠 '중심 중력' 원칙: 핵심 기능을 강화한 후 확장"
            risk_level = "medium"
            expected_impact = 0.7

        return StrategicAdvice(
            advice_id=advice_id,
            context=situation["context"],
            situation=situation["description"],
            advice=advice_text,
            reasoning=reasoning,
            risk_level=risk_level,
            expected_impact=expected_impact,
            sage_agent=self.agent_id,
            created_at=time.time(),
        )

    async def get_metrics(self) -> dict[str, Any]:
        """Sage Agent 메트릭 반환"""
        total_wisdom = len(self.strategic_wisdom)
        total_advice = len(self.strategic_advice)

        # 지혜 소스 분포
        source_distribution = {}
        for wisdom in self.strategic_wisdom.values():
            source_distribution[wisdom.source] = source_distribution.get(wisdom.source, 0) + 1

        # 조언 위험도 분포
        risk_distribution = {}
        for advice in self.strategic_advice.values():
            risk_distribution[advice.risk_level] = risk_distribution.get(advice.risk_level, 0) + 1

        return {
            "agent_type": "sage",
            "strategic_wisdom_count": total_wisdom,
            "strategic_advice_count": total_advice,
            "wisdom_source_distribution": source_distribution,
            "advice_risk_distribution": risk_distribution,
            "model_name": self.model_name,
        }

    # Public API methods

    async def get_strategic_advice(self, situation: str) -> list[dict[str, Any]]:
        """
        전략적 조언 조회

        Args:
            situation: 상황 설명

        Returns:
            관련 조언 리스트
        """
        relevant_advice = []
        for advice in self.strategic_advice.values():
            if (
                situation.lower() in advice.situation.lower()
                or situation.lower() in advice.context.lower()
            ):
                relevant_advice.append(
                    {
                        "advice_id": advice.advice_id,
                        "situation": advice.situation,
                        "advice": advice.advice,
                        "reasoning": advice.reasoning,
                        "risk_level": advice.risk_level,
                        "expected_impact": advice.expected_impact,
                    }
                )

        return relevant_advice

    async def get_wisdom_by_source(self, source: str) -> list[dict[str, Any]]:
        """
        특정 소스의 지혜 조회

        Args:
            source: 지혜 소스 ('sun_tzu', 'machiavelli', 'clausewitz', 'modern_ai')

        Returns:
            해당 소스의 지혜 리스트
        """
        wisdom_list = []
        for wisdom in self.strategic_wisdom.values():
            if wisdom.source == source:
                wisdom_list.append(
                    {
                        "wisdom_id": wisdom.wisdom_id,
                        "principle": wisdom.principle,
                        "application": wisdom.application,
                        "confidence": wisdom.confidence,
                    }
                )

        return wisdom_list

    async def apply_strategic_principle(
        self, principle_source: str, situation: str
    ) -> dict[str, Any]:
        """
        전략적 원칙 적용

        Args:
            principle_source: 원칙 소스
            situation: 적용할 상황

        Returns:
            적용 결과
        """
        principles = self.strategic_principles.get(principle_source, {})

        if not principles:
            return {"error": f"Unknown principle source: {principle_source}"}

        # 가장 적합한 원칙 선택 (시뮬레이션)
        best_principle = next(iter(principles.keys()))
        application = principles[best_principle]

        return {
            "principle_source": principle_source,
            "selected_principle": best_principle,
            "application": application,
            "situation": situation,
            "confidence": 0.85,
        }


# 글로벌 인스턴스
sage_agent = SageAgent()


# 유틸리티 함수들
async def get_strategic_advice(situation: str) -> list[dict[str, Any]]:
    """전략적 조언 유틸리티"""
    return await sage_agent.get_strategic_advice(situation)


async def get_wisdom_by_source(source: str) -> list[dict[str, Any]]:
    """지혜 조회 유틸리티"""
    return await sage_agent.get_wisdom_by_source(source)


async def apply_strategic_principle(principle_source: str, situation: str) -> dict[str, Any]:
    """전략적 원칙 적용 유틸리티"""
    return await sage_agent.apply_strategic_principle(principle_source, situation)


if __name__ == "__main__":

    async def demo():
        print("🎯 Sage Agent Phase 83 데모")
        print("=" * 50)

        # 초기화
        agent = SageAgent()

        # 메트릭 출력
        metrics = await agent.get_metrics()
        print("\n📊 Sage Agent 메트릭:")
        print(f"  • 전략적 지혜: {metrics['strategic_wisdom_count']}개")
        print(f"  • 전략적 조언: {metrics['strategic_advice_count']}개")

        # 전략적 조언 테스트
        advice = await agent.get_strategic_advice("Trinity Score 유지")
        print("\n💡 전략적 조언:")
        for item in advice:
            print(f"  • {item['advice']}")

        # 지혜 조회 테스트
        sun_tzu_wisdom = await agent.get_wisdom_by_source("sun_tzu")
        print("\n📚 손자병법 지혜:")
        for wisdom in sun_tzu_wisdom:
            print(f"  • {wisdom['principle']}")

        print("\n✅ Sage Agent 데모 완료!")

    asyncio.run(demo())
