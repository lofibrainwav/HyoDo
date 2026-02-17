# Trinity Score: 95.0 (Established by Chancellor)
"""
🎯 AFO Kingdom Meritocracy Router

세종대왕의 통치술을 본받아 능력주의 기반 Agent 로테이션 시스템

📖 개요
- 각 Agent 업무에 대해 Trinity Score 기반 최적 AI 모델 선택
- 현명한 통치자처럼 가장 적합한 AI를 가장 중요한 업무에 배치
- 투명한 선택 근거(Evidence Bundle) 제공

👑 철학 (Philosophy)
- 眞善美孝永 5기둥 균형 유지
- 현명한 선택, 적재적소 배치, 투명한 거버넌스
- 세종대왕의 통치술: 적합한 인재를 적합한 자리에

📅 메타데이터
- 작성자: 승상 (Chancellor)
- 버전: 1.0.1
- 생성일: 2026-01-22
- SSOT: AFO_FINAL_SSOT.md
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any

from AFO.background_agents import BackgroundAgent
from AFO.meritocracy_models import (
    AgentRole,
    ModelCandidate,
    ModelProvider,
    SelectionEvidence,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeritocracyRouter(BackgroundAgent):
    """
    Meritocracy Router: 능력주의 기반 Agent 모델 로테이션 시스템

    세종대왕의 통치술 적용:
    - 현명한 선택: Trinity Score 기반 최적 모델 선발
    - 적재적소 배치: 각 업무에 가장 적합한 AI 배치
    - 투명한 거버넌스: 모든 선택의 Evidence Bundle 제공
    """

    def __init__(self):
        super().__init__("meritocracy_router", "Meritocracy Router")

        # 모델 후보군 초기화
        self.model_candidates: dict[str, ModelCandidate] = {}
        self._initialize_model_candidates()

        # Agent 역할 정의
        self.agent_roles: dict[str, AgentRole] = {}
        self._initialize_agent_roles()

        # 선택 히스토리 및 증거
        self.selection_history: list[SelectionEvidence] = []
        self.evidence_bundles: dict[str, SelectionEvidence] = {}

        # 로테이션 설정
        self.rotation_enabled = True
        self.confidence_threshold = 0.8
        self.performance_history_days = 7

        # 성능 모니터링
        self.selection_stats = {
            "total_selections": 0,
            "model_distribution": {},
            "success_rate": 0.0,
            "average_confidence": 0.0,
        }

        logger.info("🏛️ Meritocracy Router initialized - 세종대왕의 통치술 구현")

    def _initialize_model_candidates(self):
        """모델 후보군 초기화"""
        candidates_data = [
            {
                "model_id": "claude-opus-4.5",
                "provider": ModelProvider.ANTHROPIC,
                "model_name": "Claude Opus 4.5",
                "base_model": "claude-3-opus-20240229",
                "context_window": 200000,
                "max_tokens": 4096,
                "cost_per_token": 0.015,
                "specialty_tags": ["reasoning", "analysis", "strategy", "complexity", "wisdom"],
            },
            {
                "model_id": "claude-sonnet-4.5",
                "provider": ModelProvider.ANTHROPIC,
                "model_name": "Claude Sonnet 4.5",
                "base_model": "claude-3-5-sonnet-20241022",
                "context_window": 200000,
                "max_tokens": 8192,
                "cost_per_token": 0.003,
                "specialty_tags": ["balanced", "efficiency", "ux", "optimization", "versatility"],
            },
            {
                "model_id": "grok-2",
                "provider": ModelProvider.XAI,
                "model_name": "Grok 2",
                "base_model": "grok-2-1212",
                "context_window": 131072,
                "max_tokens": 8192,
                "cost_per_token": 0.002,
                "specialty_tags": ["exploration", "discovery", "search", "efficiency", "curiosity"],
            },
            {
                "model_id": "gemini-pro",
                "provider": ModelProvider.GOOGLE,
                "model_name": "Gemini Pro",
                "base_model": "gemini-pro",
                "context_window": 32768,
                "max_tokens": 8192,
                "cost_per_token": 0.00025,
                "specialty_tags": ["speed", "scalability", "multimodal", "cost_effective"],
            },
            {
                "model_id": "claude-haiku",
                "provider": ModelProvider.ANTHROPIC,
                "model_name": "Claude Haiku",
                "base_model": "claude-3-haiku-20240307",
                "context_window": 200000,
                "max_tokens": 4096,
                "cost_per_token": 0.00025,
                "specialty_tags": ["speed", "simplicity", "cost_effective", "basic_tasks"],
            },
            {
                "model_id": "qwen3-vl",
                "provider": ModelProvider.LOCAL,
                "model_name": "Qwen3-VL",
                "base_model": "qwen3-vl:latest",
                "context_window": 32768,
                "max_tokens": 4096,
                "cost_per_token": 0.0,
                "specialty_tags": ["vision", "local", "multimodal", "free"],
            },
        ]

        for data in candidates_data:
            candidate = ModelCandidate(**data)
            self.model_candidates[candidate.model_id] = candidate

        logger.info(f"📋 Initialized {len(self.model_candidates)} model candidates")

    def _initialize_agent_roles(self):
        """Agent 역할 정의 초기화"""
        roles_data = [
            {
                "agent_name": "librarian_agent",
                "role_description": "문서·연구 특화 에이전트",
                "primary_tasks": ["document_search", "knowledge_synthesis", "research_assistance"],
                "trinity_weights": {
                    "truth": 0.40,  # 정확한 정보 검색
                    "goodness": 0.30,  # 신뢰할 수 있는 출처
                    "beauty": 0.15,  # 명확한 정보 전달
                    "serenity": 0.10,  # 안정적인 검색
                    "eternity": 0.05,  # 지속적인 지식 관리
                },
                "model_candidates": [
                    "claude-opus-4.5",
                    "claude-sonnet-4.5",
                    "grok-2",
                    "gemini-pro",
                ],
                "min_trinity_threshold": 85.0,
            },
            {
                "agent_name": "explorer_agent",
                "role_description": "코드 탐색·분석 특화 에이전트",
                "primary_tasks": ["code_analysis", "pattern_discovery", "dependency_mapping"],
                "trinity_weights": {
                    "truth": 0.18,  # 정확한 코드 분석
                    "goodness": 0.18,  # 안전한 탐색
                    "beauty": 0.10,  # 깔끔한 구조화
                    "serenity": 0.15,  # 안정적인 분석
                    "eternity": 0.05,  # 지속적인 모니터링
                },
                "model_candidates": ["grok-2", "claude-sonnet-4.5", "gemini-pro", "claude-haiku"],
                "min_trinity_threshold": 82.0,
            },
            {
                "agent_name": "prometheus_agent",
                "role_description": "전략·리스크 관리 특화 에이전트",
                "primary_tasks": ["strategy_planning", "risk_assessment", "resource_optimization"],
                "trinity_weights": {
                    "truth": 0.30,  # 정확한 분석
                    "goodness": 0.40,  # 윤리적 판단
                    "beauty": 0.10,  # 전략적 명확성
                    "serenity": 0.15,  # 안정적인 계획
                    "eternity": 0.05,  # 장기적 지속
                },
                "model_candidates": [
                    "claude-opus-4.5",
                    "claude-sonnet-4.5",
                    "grok-2",
                    "gemini-pro",
                ],
                "min_trinity_threshold": 88.0,
            },
            {
                "agent_name": "metis_agent",
                "role_description": "계획 검토·최적화 특화 에이전트",
                "primary_tasks": [
                    "plan_evaluation",
                    "optimization_analysis",
                    "feasibility_assessment",
                ],
                "trinity_weights": {
                    "truth": 0.25,  # 정확한 평가
                    "goodness": 0.25,  # 공정한 판단
                    "beauty": 0.25,  # 명확한 최적화
                    "serenity": 0.15,  # 안정적인 검토
                    "eternity": 0.10,  # 지속적인 개선
                },
                "model_candidates": [
                    "claude-sonnet-4.5",
                    "claude-opus-4.5",
                    "grok-2",
                    "gemini-pro",
                ],
                "min_trinity_threshold": 85.0,
            },
            {
                "agent_name": "sage_agent",
                "role_description": "고전 지식과 현대 AI의 전략적 결합 특화 에이전트",
                "primary_tasks": [
                    "strategic_advice",
                    "wisdom_accumulation",
                    "principle_application",
                ],
                "trinity_weights": {
                    "truth": 0.30,  # 전략적 정확성
                    "goodness": 0.25,  # 윤리적 판단
                    "beauty": 0.12,  # 전략적 우아함
                    "serenity": 0.15,  # 평온한 전략
                    "eternity": 0.10,  # 영속적 지혜
                },
                "model_candidates": [
                    "claude-opus-4.5",  # 전략적 사고용
                    "claude-sonnet-4.5",
                    "grok-2",
                ],
                "min_trinity_threshold": 88.0,
            },
        ]

        for data in roles_data:
            role = AgentRole(**data)
            self.agent_roles[role.agent_name] = role

        logger.info(f"👥 Initialized {len(self.agent_roles)} agent roles")

    async def execute_cycle(self) -> None:
        """
        Meritocracy Router의 주요 실행 로직

        수행 작업:
        1. 모델 성능 모니터링 및 업데이트
        2. 로테이션 정책 최적화
        3. 선택 히스토리 정리 및 분석
        """

        try:
            # 1. 모델 성능 업데이트
            await self._update_model_performance()

            # 2. 로테이션 정책 최적화
            await self._optimize_rotation_policy()

            # 3. 선택 히스토리 분석
            await self._analyze_selection_history()

            logger.info("🏛️ Meritocracy cycle completed - 현명한 선택의 연속")

        except Exception as e:
            logger.error(f"Meritocracy cycle error: {e}")
            self.status.error_count += 1

    async def select_best_model(
        self, agent_name: str, task_context: dict[str, Any]
    ) -> tuple[str, SelectionEvidence]:
        """
        Agent와 업무에 대한 최적 모델 선택

        Args:
            agent_name: 에이전트 이름
            task_context: 업무 컨텍스트

        Returns:
            (선택된 모델 ID, 선택 근거 증거)
        """
        if not self.rotation_enabled:
            # 로테이션 비활성화 시 기본 모델 반환
            default_model = self._get_default_model(agent_name)
            evidence = self._create_default_evidence(agent_name, default_model, task_context)
            return default_model, evidence

        # Agent 역할 확인
        if agent_name not in self.agent_roles:
            raise ValueError(f"Unknown agent: {agent_name}")

        role = self.agent_roles[agent_name]
        task_type = task_context.get("task_type", "general")
        task_complexity = task_context.get("complexity", "medium")

        # 각 후보 모델의 Trinity Score 계산
        model_scores = {}
        for model_id in role.model_candidates:
            if model_id in self.model_candidates:
                candidate = self.model_candidates[model_id]
                trinity_score = candidate.calculate_trinity_score(
                    task_type, self.performance_history_days
                )

                # 작업 복잡도에 따른 조정
                complexity_multiplier = self._get_complexity_multiplier(task_complexity)
                adjusted_score = trinity_score * complexity_multiplier

                # 가중치 적용
                weighted_score = self._apply_role_weights(adjusted_score, role.trinity_weights)

                model_scores[model_id] = {
                    "raw_score": trinity_score,
                    "adjusted_score": adjusted_score,
                    "weighted_score": weighted_score,
                    "performance_records": len(candidate.get_recent_performance(task_type)),
                }

        # 최고 성능 모델 선택
        if not model_scores:
            # 점수가 없는 경우 기본 모델 선택
            selected_model = role.model_candidates[0]
            confidence = 0.5
        else:
            # 가중 점수 기준 최고 모델 선택
            sorted_models = sorted(
                model_scores.items(), key=lambda x: x[1]["weighted_score"], reverse=True
            )
            selected_model = sorted_models[0][0]
            best_score = sorted_models[0][1]["weighted_score"]
            confidence = min(1.0, best_score / 100.0)

        # 선택 근거 증거 생성
        evidence = self._create_selection_evidence(
            agent_name, selected_model, model_scores, task_context, confidence
        )

        # 선택 기록 저장
        self.selection_history.append(evidence)
        self.evidence_bundles[evidence.selection_id] = evidence

        # 통계 업데이트
        self._update_selection_stats(selected_model, confidence)

        logger.info(f"🏆 {agent_name} → {selected_model} (confidence: {confidence:.2f})")

        return selected_model, evidence

    def _get_default_model(self, agent_name: str) -> str:
        """기본 모델 반환"""
        role = self.agent_roles.get(agent_name)
        if role and role.model_candidates:
            return role.model_candidates[0]
        return "claude-sonnet-4.5"  # 안전한 기본값

    def _create_default_evidence(
        self, agent_name: str, model: str, task_context: dict[str, Any]
    ) -> SelectionEvidence:
        """기본 선택 증거 생성"""
        return SelectionEvidence(
            selection_id=f"default_{int(time.time())}_{agent_name}",
            agent_name=agent_name,
            task_description=task_context.get("description", "Default task"),
            selected_model=model,
            trinity_scores={model: 75.0},
            selection_reasoning="Rotation disabled - using default model",
            confidence_level=0.5,
            alternatives_considered=[],
            selection_timestamp=time.time(),
            selection_criteria={"rotation_enabled": False},
        )

    def _get_complexity_multiplier(self, complexity: str) -> float:
        """작업 복잡도에 따른 승수"""
        multipliers = {"low": 1.0, "medium": 1.0, "high": 1.1, "critical": 1.2}
        return multipliers.get(complexity, 1.0)

    def _apply_role_weights(self, score: float, weights: dict[str, float]) -> float:
        """역할별 가중치 적용 (단순화된 버전)"""
        # 가중치 총합 계산 (정규화용)
        weight_sum = sum(weights.values()) if weights else 1.0
        # 가중치 총합이 1.0에 가까우면 점수 유지, 아니면 정규화 적용
        multiplier = 1.0 if abs(weight_sum - 1.0) < 0.01 else weight_sum
        return score * multiplier

    def _create_selection_evidence(
        self,
        agent_name: str,
        selected_model: str,
        model_scores: dict[str, dict[str, Any]],
        task_context: dict[str, Any],
        confidence: float,
    ) -> SelectionEvidence:
        """선택 근거 증거 생성"""
        selection_id = f"sel_{int(time.time())}_{agent_name}_{hash(selected_model) % 1000}"

        # Trinity 점수 추출
        trinity_scores = {model: scores["weighted_score"] for model, scores in model_scores.items()}

        # 선택 근거 생성
        reasoning = self._generate_selection_reasoning(selected_model, model_scores, confidence)

        # 고려된 대안들
        alternatives = [model for model in model_scores.keys() if model != selected_model]

        evidence = SelectionEvidence(
            selection_id=selection_id,
            agent_name=agent_name,
            task_description=task_context.get("description", "Task execution"),
            selected_model=selected_model,
            trinity_scores=trinity_scores,
            selection_reasoning=reasoning,
            confidence_level=confidence,
            alternatives_considered=alternatives,
            selection_timestamp=time.time(),
            selection_criteria={
                "rotation_enabled": self.rotation_enabled,
                "performance_history_days": self.performance_history_days,
                "task_complexity": task_context.get("complexity", "medium"),
                "model_candidates_count": len(model_scores),
            },
        )

        return evidence

    def _generate_selection_reasoning(
        self, selected_model: str, model_scores: dict[str, dict[str, Any]], confidence: float
    ) -> str:
        """선택 근거 생성"""
        if not model_scores:
            return "점수 데이터 부족으로 기본 선택"

        selected_score = model_scores[selected_model]["weighted_score"]
        best_alternative = None
        best_alt_score = 0

        for model, scores in model_scores.items():
            if model != selected_model and scores["weighted_score"] > best_alt_score:
                best_alternative = model
                best_alt_score = scores["weighted_score"]

        margin = selected_score - best_alt_score if best_alternative else 0

        reasoning = f"Trinity Score {selected_score:.1f}점으로 선택"
        if best_alternative:
            reasoning += f" (차이: {margin:.1f}점, 대안: {best_alternative})"
        reasoning += f" - 신뢰도: {confidence:.2f}"

        return reasoning

    def _update_selection_stats(self, selected_model: str, confidence: float):
        """선택 통계 업데이트"""
        self.selection_stats["total_selections"] += 1

        # 모델 분포 업데이트
        if selected_model not in self.selection_stats["model_distribution"]:
            self.selection_stats["model_distribution"][selected_model] = 0
        self.selection_stats["model_distribution"][selected_model] += 1

        # 평균 신뢰도 업데이트
        current_avg = self.selection_stats["average_confidence"]
        total = self.selection_stats["total_selections"]
        self.selection_stats["average_confidence"] = (
            current_avg * (total - 1) + confidence
        ) / total

    async def _update_model_performance(self) -> None:
        """모델 성능 업데이트 (시뮬레이션)"""
        # 실제로는 실제 API 호출 결과를 바탕으로 업데이트
        # 현재는 시뮬레이션

        for candidate in self.model_candidates.values():
            # 가상의 성능 데이터 추가
            if len(candidate.performance_history) < 10:
                mock_score = 75.0 + (hash(candidate.model_id) % 20)  # 75-95 사이
                candidate.add_performance_record(
                    task_type="general",
                    trinity_score=mock_score,
                    response_time=1.0 + (hash(candidate.model_id) % 2),
                    cost=candidate.cost_per_token * 100,
                    quality_metrics={"accuracy": 0.9, "relevance": 0.85},
                )

    async def _optimize_rotation_policy(self) -> None:
        """로테이션 정책 최적화"""
        # 성공률 분석
        recent_selections = list(self.selection_history[-50:])  # 최근 50개

        if recent_selections:
            high_confidence_selections = [s for s in recent_selections if s.confidence_level > 0.8]
            success_rate = len(high_confidence_selections) / len(recent_selections)
            self.selection_stats["success_rate"] = success_rate

            # 성공률이 낮으면 보수적으로
            if success_rate < 0.7:
                self.confidence_threshold = min(0.9, self.confidence_threshold + 0.05)
            elif success_rate > 0.9:
                self.confidence_threshold = max(0.7, self.confidence_threshold - 0.02)

    async def _analyze_selection_history(self) -> None:
        """선택 히스토리 분석"""
        # 오래된 기록 정리 (1000개 이상이면)
        if len(self.selection_history) > 1000:
            # 최근 500개만 유지
            self.selection_history = self.selection_history[-500:]
            self.evidence_bundles = {
                k: v
                for k, v in self.evidence_bundles.items()
                if v.selection_timestamp > time.time() - (30 * 24 * 60 * 60)  # 30일 이내
            }

    async def get_metrics(self) -> dict[str, Any]:
        """Meritocracy Router 메트릭 반환"""
        return await self.get_meritocracy_report()

    async def get_meritocracy_report(self) -> dict[str, Any]:
        """능력주의 시스템 리포트"""
        total_selections = len(self.selection_history)
        recent_selections = list(self.selection_history[-100:])  # 최근 100개

        # 모델별 선택 통계
        model_stats = {}
        for selection in recent_selections:
            model = selection.selected_model
            if model not in model_stats:
                model_stats[model] = {"count": 0, "avg_confidence": 0, "total_confidence": 0}
            model_stats[model]["count"] += 1
            model_stats[model]["total_confidence"] += selection.confidence_level

        for model in model_stats:
            model_stats[model]["avg_confidence"] = (
                model_stats[model]["total_confidence"] / model_stats[model]["count"]
            )

        # Agent별 성능
        agent_performance = {}
        for agent_name in self.agent_roles.keys():
            agent_selections = [s for s in recent_selections if s.agent_name == agent_name]
            if agent_selections:
                avg_confidence = sum(s.confidence_level for s in agent_selections) / len(
                    agent_selections
                )
                agent_performance[agent_name] = {
                    "selections": len(agent_selections),
                    "avg_confidence": avg_confidence,
                    "success_rate": len([s for s in agent_selections if s.confidence_level > 0.8])
                    / len(agent_selections),
                }

        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": "active" if self.rotation_enabled else "disabled",
            "total_selections": total_selections,
            "recent_selections": len(recent_selections),
            "model_performance": model_stats,
            "agent_performance": agent_performance,
            "selection_stats": self.selection_stats,
            "philosophy": "세종대왕의 통치술 - 현명한 선택, 적재적소 배치",
            "evidence_bundle_count": len(self.evidence_bundles),
        }

    def get_selection_evidence(self, selection_id: str) -> SelectionEvidence | None:
        """선택 증거 조회"""
        return self.evidence_bundles.get(selection_id)

    def export_evidence_bundle(self, selection_id: str) -> str | None:
        """증거 번들 JSON导出"""
        evidence = self.get_selection_evidence(selection_id)
        if evidence:
            return json.dumps(evidence.to_dict(), indent=2, ensure_ascii=False)
        return None


# 글로벌 인스턴스
meritocracy_router = MeritocracyRouter()


# 유틸리티 함수들
async def select_best_model_for_agent(
    agent_name: str, task_context: dict[str, Any]
) -> tuple[str, SelectionEvidence]:
    """Agent 최적 모델 선택 유틸리티"""
    return await meritocracy_router.select_best_model(agent_name, task_context)


async def get_meritocracy_report() -> dict[str, Any]:
    """능력주의 리포트 유틸리티"""
    return await meritocracy_router.get_meritocracy_report()


async def get_selection_evidence(selection_id: str) -> SelectionEvidence | None:
    """선택 증거 조회 유틸리티"""
    return meritocracy_router.get_selection_evidence(selection_id)


__all__ = [
    # Models (re-export for convenience)
    "ModelProvider",
    "ModelCandidate",
    "AgentRole",
    "SelectionEvidence",
    # Router
    "MeritocracyRouter",
    "meritocracy_router",
    # Utility functions
    "select_best_model_for_agent",
    "get_meritocracy_report",
    "get_selection_evidence",
]
