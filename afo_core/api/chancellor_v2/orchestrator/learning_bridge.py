# Trinity Score: 92.0 (永 - Continuous Learning)
"""Learning Engine Bridge for Strategist Integration.

Learning Engine과 Strategist를 연결하는 브릿지.
Strategist 평가 결과를 학습하고, 과거 패턴을 기반으로 최적화합니다.

AFO 철학:
- 永 (Eternity): 지속적인 학습과 개선
- 眞 (Truth): 데이터 기반 최적화
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .strategist_context import StrategistContext

logger = logging.getLogger(__name__)


@dataclass
class StrategistDecisionRecord:
    """Strategist 결정 기록."""

    # Identity
    record_id: str = ""
    pillar: str = ""
    context_id: str = ""

    # Input
    skill_id: str = ""
    command_hash: str = ""  # 명령어 해시 (패턴 매칭용)

    # Output
    score: float = 0.0
    reasoning: str = ""
    issues: list[str] = field(default_factory=list)

    # Meta
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    mode: str = ""  # "Heuristic" or "LLM"

    # Outcome (나중에 피드백으로 업데이트)
    outcome_success: bool | None = None
    outcome_feedback: str = ""
    outcome_timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "record_id": self.record_id,
            "pillar": self.pillar,
            "context_id": self.context_id,
            "skill_id": self.skill_id,
            "command_hash": self.command_hash,
            "score": self.score,
            "reasoning": self.reasoning,
            "issues": self.issues,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "mode": self.mode,
            "outcome_success": self.outcome_success,
            "outcome_feedback": self.outcome_feedback,
        }


@dataclass
class PatternInsight:
    """학습된 패턴 인사이트."""

    pattern_hash: str
    pillar: str
    skill_id: str

    # 통계
    total_count: int = 0
    success_count: int = 0
    avg_score: float = 0.0
    score_variance: float = 0.0

    # 권장사항
    recommended_score_adjustment: float = 0.0
    confidence: float = 0.0

    # 발견된 공통 이슈
    common_issues: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """성공률."""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count


class LearningBridge:
    """Learning Engine ↔ Strategist 브릿지.

    Usage:
        bridge = LearningBridge()

        # 결정 기록
        await bridge.record_decision(ctx, outcome=True)

        # 패턴 기반 점수 조정
        adjusted_score = await bridge.get_score_adjustment(ctx)

        # 인사이트 조회
        insights = bridge.get_insights_for_pillar("truth")
    """

    def __init__(self, max_records: int = 10000) -> None:
        """브릿지 초기화."""
        self._records: list[StrategistDecisionRecord] = []
        self._patterns: dict[str, PatternInsight] = {}
        self._max_records = max_records
        self._lock = asyncio.Lock()

        # Learning Engine 연결 시도
        self._learning_engine: Any = None
        self._connect_learning_engine()

    def _connect_learning_engine(self) -> None:
        """Learning Engine 연결."""
        try:
            from AFO.chancellor.learning_engine import LearningEngine

            self._learning_engine = LearningEngine()
            logger.info("Learning Engine connected to bridge")
        except ImportError:
            logger.warning("Learning Engine not available, using local storage only")

    def _compute_pattern_hash(self, ctx: StrategistContext) -> str:
        """컨텍스트 기반 패턴 해시 계산.

        비슷한 명령어/스킬 조합을 같은 패턴으로 그룹화합니다.
        """
        # 명령어에서 변수 부분 제거 (일반화)
        normalized_command = ctx.command.lower()
        for var in ["uuid", "id", "key", "token", "path"]:
            import re

            normalized_command = re.sub(rf"\b{var}[_\-]?\w+\b", f"${var}$", normalized_command)

        pattern_input = f"{ctx.pillar}:{ctx.skill_id}:{normalized_command[:100]}"
        return hashlib.md5(pattern_input.encode()).hexdigest()[:12]

    async def record_decision(
        self,
        ctx: StrategistContext,
        outcome: bool | None = None,
        feedback: str = "",
    ) -> StrategistDecisionRecord:
        """Strategist 결정 기록.

        Args:
            ctx: 실행 컨텍스트
            outcome: 결과 성공 여부 (나중에 업데이트 가능)
            feedback: 피드백 메시지

        Returns:
            생성된 기록
        """
        record = StrategistDecisionRecord(
            record_id=f"{ctx.context_id}_{ctx.pillar}",
            pillar=ctx.pillar,
            context_id=ctx.context_id,
            skill_id=ctx.skill_id,
            command_hash=self._compute_pattern_hash(ctx),
            score=ctx.score,
            reasoning=ctx.reasoning,
            issues=ctx.issues.copy(),
            timestamp=time.time(),
            duration_ms=ctx.duration_ms,
            mode=ctx.metadata.get("mode", "Unknown"),
            outcome_success=outcome,
            outcome_feedback=feedback,
        )

        async with self._lock:
            self._records.append(record)

            # 최대 개수 초과 시 오래된 기록 제거
            if len(self._records) > self._max_records:
                self._records = self._records[-self._max_records :]

            # 패턴 업데이트
            await self._update_pattern(record)

        # Learning Engine에도 기록
        if self._learning_engine and outcome is not None:
            try:
                self._learning_engine.learn_from_decision(
                    decision_id=record.record_id,
                    outcome="success" if outcome else "failure",
                    context={"pillar": ctx.pillar, "skill": ctx.skill_id},
                )
            except Exception as e:
                logger.debug(f"Learning Engine recording failed: {e}")

        return record

    async def _update_pattern(self, record: StrategistDecisionRecord) -> None:
        """패턴 통계 업데이트."""
        pattern_key = f"{record.pillar}:{record.command_hash}"

        if pattern_key not in self._patterns:
            self._patterns[pattern_key] = PatternInsight(
                pattern_hash=record.command_hash,
                pillar=record.pillar,
                skill_id=record.skill_id,
            )

        pattern = self._patterns[pattern_key]
        pattern.total_count += 1

        if record.outcome_success:
            pattern.success_count += 1

        # 평균 점수 업데이트 (이동 평균)
        alpha = 0.1  # 최근 데이터에 더 많은 가중치
        pattern.avg_score = (1 - alpha) * pattern.avg_score + alpha * record.score

        # 공통 이슈 수집
        for issue in record.issues:
            if issue not in pattern.common_issues:
                pattern.common_issues.append(issue)
                if len(pattern.common_issues) > 5:
                    pattern.common_issues = pattern.common_issues[-5:]

        # 권장 점수 조정 계산
        if pattern.total_count >= 5:
            pattern.confidence = min(1.0, pattern.total_count / 50)
            if pattern.success_rate > 0.8:
                pattern.recommended_score_adjustment = 0.05 * pattern.confidence
            elif pattern.success_rate < 0.3:
                pattern.recommended_score_adjustment = -0.1 * pattern.confidence

    async def get_score_adjustment(self, ctx: StrategistContext) -> float:
        """패턴 기반 점수 조정값 조회.

        Args:
            ctx: 실행 컨텍스트

        Returns:
            권장 점수 조정값 (-0.1 ~ 0.1)
        """
        pattern_hash = self._compute_pattern_hash(ctx)
        pattern_key = f"{ctx.pillar}:{pattern_hash}"

        pattern = self._patterns.get(pattern_key)
        if pattern and pattern.confidence > 0.3:
            logger.debug(
                f"Pattern found for {ctx.pillar}: "
                f"adj={pattern.recommended_score_adjustment:.3f}, "
                f"conf={pattern.confidence:.2f}"
            )
            return pattern.recommended_score_adjustment

        return 0.0

    async def update_outcome(
        self,
        context_id: str,
        pillar: str,
        success: bool,
        feedback: str = "",
    ) -> bool:
        """기존 기록에 결과 업데이트.

        Args:
            context_id: 컨텍스트 ID
            pillar: Pillar 이름
            success: 성공 여부
            feedback: 피드백

        Returns:
            업데이트 성공 여부
        """
        record_id = f"{context_id}_{pillar}"

        async with self._lock:
            for record in reversed(self._records):
                if record.record_id == record_id:
                    record.outcome_success = success
                    record.outcome_feedback = feedback
                    record.outcome_timestamp = time.time()
                    await self._update_pattern(record)
                    return True

        return False

    def get_insights_for_pillar(self, pillar: str) -> list[PatternInsight]:
        """Pillar별 학습된 인사이트 조회.

        Args:
            pillar: Pillar 이름

        Returns:
            관련 패턴 인사이트 목록
        """
        return [
            p
            for p in self._patterns.values()
            if p.pillar.lower() == pillar.lower() and p.total_count >= 3
        ]

    def get_recent_records(
        self,
        pillar: str | None = None,
        limit: int = 20,
    ) -> list[StrategistDecisionRecord]:
        """최근 기록 조회.

        Args:
            pillar: 필터할 Pillar (None이면 전체)
            limit: 최대 반환 개수

        Returns:
            최근 기록 목록
        """
        records = self._records
        if pillar:
            records = [r for r in records if r.pillar.lower() == pillar.lower()]
        return records[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """전체 통계 조회."""
        pillar_stats = {}
        for pillar in ["truth", "goodness", "beauty"]:
            records = [r for r in self._records if r.pillar.lower() == pillar]
            if records:
                scores = [r.score for r in records]
                success_records = [r for r in records if r.outcome_success is True]
                pillar_stats[pillar] = {
                    "total_records": len(records),
                    "avg_score": sum(scores) / len(scores),
                    "success_rate": len(success_records) / len(records) if records else 0,
                    "patterns_learned": len(
                        [p for p in self._patterns.values() if p.pillar.lower() == pillar]
                    ),
                }

        return {
            "total_records": len(self._records),
            "total_patterns": len(self._patterns),
            "pillar_stats": pillar_stats,
            "learning_engine_connected": self._learning_engine is not None,
        }


# 싱글톤 인스턴스
_default_bridge: LearningBridge | None = None


def get_learning_bridge() -> LearningBridge:
    """기본 Learning Bridge 조회."""
    global _default_bridge
    if _default_bridge is None:
        _default_bridge = LearningBridge()
    return _default_bridge
