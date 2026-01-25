from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from AFO.domain.metrics.trinity import TrinityInputs, TrinityMetrics
from AFO.services.mcp_tool_trinity_evaluator import mcp_tool_trinity_evaluator
from afo_soul_engine.api.models.skills import (
    PhilosophyScores,
    SkillExecuteRequest,
    SkillExecutionResult,
)

if TYPE_CHECKING:
    from AFO.afo_skills_registry import SkillRegistry

logger = logging.getLogger(__name__)

# Trinity Score Evaluator (동적 점수 계산)
try:
    TRINITY_EVALUATOR_AVAILABLE = True
except ImportError:
    mcp_tool_trinity_evaluator = None
    TRINITY_EVALUATOR_AVAILABLE = False


class SkillExecutor:
    """Skill 실행 및 평가 담당"""

    def __init__(self, registry: SkillRegistry | None) -> None:
        self.registry = registry
        self.execution_stats: dict[str, dict[str, Any]] = {}

    async def execute_skill(self, request: SkillExecuteRequest) -> SkillExecutionResult:
        """스킬 실행"""
        start_time = time.time()

        try:
            if not self.registry:
                raise ValueError("Skill Registry not available")

            skill = self.registry.get(request.skill_id)
            if not skill:
                raise ValueError(f"Skill not found: {request.skill_id}")

            # 실제 스킬 실행 로직 (Mock)
            result = await self._execute_skill_logic(skill, request.parameters or {})

            execution_time = (time.time() - start_time) * 1000

            # 실행 통계 업데이트
            self._update_execution_stats(request.skill_id)

            # 동적 Trinity Score 계산
            final_philosophy_score = self._evaluate_trinity_score(
                skill, request.skill_id, result, execution_time
            )

            # 실행 결과 생성
            execution_result = SkillExecutionResult(
                skill_id=request.skill_id,
                success=True,
                status="success",
                result=result,
                execution_time_ms=execution_time,
                philosophy_score=final_philosophy_score,
                error=None,
            )

            # 통계 기록
            self._record_execution_stats(request.skill_id, execution_result)

            logger.info("✅ 스킬 실행 완료: %s (%.2fms)", request.skill_id, execution_time)

            return execution_result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            execution_result = SkillExecutionResult(
                skill_id=request.skill_id,
                success=False,
                status="error",
                result={},
                execution_time_ms=execution_time,
                error=error_msg,
                philosophy_score=None,
            )

            logger.error("❌ 스킬 실행 실패: %s - %s", request.skill_id, error_msg)
            return execution_result

    async def _execute_skill_logic(self, skill: Any, parameters: dict[str, Any]) -> dict[str, Any]:
        """실제 스킬 실행 로직 (Mock)"""
        await asyncio.sleep(0.1)  # 모의 실행 시간

        execution_mode_value = (
            skill.execution_mode.value
            if hasattr(skill.execution_mode, "value")
            else str(skill.execution_mode)
        )

        skill_type_messages = {
            "local_function": f"Executed local function for {skill.skill_id}",
            "n8n_workflow": f"Executed n8n workflow for {skill.skill_id}",
            "browser_script": f"Executed browser script for {skill.skill_id}",
            "api_call": f"Executed API call for {skill.skill_id}",
        }

        message = skill_type_messages.get(
            execution_mode_value, f"Executed skill {skill.skill_id} with mock result"
        )
        return {"message": message}

    def _update_execution_stats(self, skill_id: str) -> None:
        """레지스트리 실행 카운트 증가"""
        if self.registry and hasattr(self.registry, "increment_execution_count"):
            self.registry.increment_execution_count(skill_id)
        else:
            if skill_id not in self.execution_stats:
                self.execution_stats[skill_id] = {}
            self.execution_stats[skill_id]["execution_count"] = (
                self.execution_stats[skill_id].get("execution_count", 0) + 1
            )

    def _evaluate_trinity_score(
        self, skill: Any, skill_id: str, result: Any, execution_time: float
    ) -> PhilosophyScores | None:
        """Trinity Score 평가"""
        base_philosophy_scores = None
        if skill.philosophy_scores and hasattr(skill.philosophy_scores, "truth"):
            base_philosophy_scores = {
                "truth": getattr(skill.philosophy_scores, "truth", 85),
                "goodness": getattr(skill.philosophy_scores, "goodness", 80),
                "beauty": getattr(skill.philosophy_scores, "beauty", 75),
                "serenity": getattr(skill.philosophy_scores, "serenity", 90),
            }

        # 동적 평가 시도
        if TRINITY_EVALUATOR_AVAILABLE and mcp_tool_trinity_evaluator:
            try:
                result_str = json.dumps(result) if isinstance(result, dict) else str(result)
                trinity_eval = mcp_tool_trinity_evaluator.evaluate_execution_result(
                    tool_name=skill_id,
                    execution_result=result_str,
                    execution_time_ms=execution_time,
                    is_error=False,
                    base_philosophy_scores=base_philosophy_scores,
                )

                trinity_inputs = TrinityInputs(
                    truth=trinity_eval["trinity_scores"]["truth"],
                    goodness=trinity_eval["trinity_scores"]["goodness"],
                    beauty=trinity_eval["trinity_scores"]["beauty"],
                    filial_serenity=trinity_eval["trinity_scores"]["filial_serenity"],
                )
                trinity_metrics = TrinityMetrics.from_inputs(trinity_inputs)

                return PhilosophyScores(
                    truth=trinity_metrics.truth * 100,
                    goodness=trinity_metrics.goodness * 100,
                    beauty=trinity_metrics.beauty * 100,
                    serenity=trinity_metrics.filial_serenity * 100,
                )
            except Exception as e:
                logger.warning("SSOT Trinity Score 계산 실패, 정적 점수 사용: %s", e)

        # Fallback: 정적 점수
        if base_philosophy_scores:
            return PhilosophyScores(
                truth=base_philosophy_scores["truth"],
                goodness=base_philosophy_scores["goodness"],
                beauty=base_philosophy_scores["beauty"],
                serenity=base_philosophy_scores["serenity"],
            )
        return PhilosophyScores(truth=85.0, goodness=80.0, beauty=75.0, serenity=90.0)

    def _record_execution_stats(self, skill_id: str, result: SkillExecutionResult) -> None:
        """내부 실행 통계 기록"""
        if skill_id not in self.execution_stats:
            self.execution_stats[skill_id] = {}

        self.execution_stats[skill_id].update(
            {
                "last_execution": datetime.now(UTC),
                "success_rate": 1.0 if result.status == "success" else 0.0,
                "avg_execution_time": result.execution_time_ms,
            }
        )

    def get_execution_stats(self) -> dict[str, dict[str, Any]]:
        return self.execution_stats
