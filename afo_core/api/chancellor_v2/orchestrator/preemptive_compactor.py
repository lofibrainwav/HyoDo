# Trinity Score: 93.0 (永 - Context Preservation & Compression)
"""Preemptive Compactor for Context Window Management.

컨텍스트 윈도우 사용량을 모니터링하고 임계값 도달 시 자동 압축합니다.

AFO 철학:
- 永 (Eternity): 중요 컨텍스트 보존
- 孝 (Serenity): 사용자 경험 연속성
- 善 (Goodness): 압축 전 스냅샷으로 안전망 제공
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CompressionStrategy(str, Enum):
    """압축 전략."""

    TRIM_OLD = "trim_old"  # 오래된 메시지 제거
    SUMMARIZE = "summarize"  # 요약 (LLM 필요)
    DEDUPLICATE = "deduplicate"  # 중복 제거
    PRIORITY_FILTER = "priority_filter"  # 우선순위 기반 필터링
    HYBRID = "hybrid"  # 복합 전략


class CompressionLevel(str, Enum):
    """압축 수준."""

    LIGHT = "light"  # 10-20% 압축
    MODERATE = "moderate"  # 30-50% 압축
    AGGRESSIVE = "aggressive"  # 50-70% 압축


@dataclass
class ContextMetrics:
    """컨텍스트 메트릭."""

    total_tokens: int = 0
    max_tokens: int = 128000  # Claude 기본값
    message_count: int = 0
    oldest_message_age_seconds: float = 0.0
    duplicate_ratio: float = 0.0  # 중복 비율

    @property
    def usage_ratio(self) -> float:
        """사용률 (0.0 ~ 1.0)."""
        if self.max_tokens == 0:
            return 0.0
        return min(1.0, self.total_tokens / self.max_tokens)

    @property
    def usage_percent(self) -> float:
        """사용률 (%)."""
        return self.usage_ratio * 100

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "total_tokens": self.total_tokens,
            "max_tokens": self.max_tokens,
            "usage_ratio": round(self.usage_ratio, 3),
            "usage_percent": round(self.usage_percent, 1),
            "message_count": self.message_count,
            "oldest_message_age_seconds": self.oldest_message_age_seconds,
            "duplicate_ratio": round(self.duplicate_ratio, 3),
        }


@dataclass
class CompressionResult:
    """압축 결과."""

    success: bool = False
    strategy_used: CompressionStrategy = CompressionStrategy.TRIM_OLD
    level: CompressionLevel = CompressionLevel.LIGHT

    # 압축 전후 메트릭
    before_tokens: int = 0
    after_tokens: int = 0
    tokens_removed: int = 0
    messages_removed: int = 0

    # 백업 정보
    snapshot_id: str | None = None

    # 실행 정보
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    error: str | None = None

    @property
    def compression_ratio(self) -> float:
        """압축률 (0.0 ~ 1.0)."""
        if self.before_tokens == 0:
            return 0.0
        return 1.0 - (self.after_tokens / self.before_tokens)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "success": self.success,
            "strategy": self.strategy_used.value,
            "level": self.level.value,
            "before_tokens": self.before_tokens,
            "after_tokens": self.after_tokens,
            "tokens_removed": self.tokens_removed,
            "messages_removed": self.messages_removed,
            "compression_ratio": round(self.compression_ratio, 3),
            "snapshot_id": self.snapshot_id,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
        }


@dataclass
class MessageItem:
    """컨텍스트 메시지 아이템."""

    role: str  # system, user, assistant
    content: str
    timestamp: float = field(default_factory=time.time)
    token_count: int = 0
    priority: int = 5  # 1(최고) ~ 10(최저)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        """콘텐츠 해시 (중복 감지용)."""
        return hashlib.md5(self.content.encode()).hexdigest()[:8]

    @property
    def age_seconds(self) -> float:
        """메시지 나이 (초)."""
        return time.time() - self.timestamp


@dataclass
class PreemptiveCompactor:
    """컨텍스트 윈도우 압축 관리자.

    컨텍스트 사용량을 모니터링하고 임계값 도달 시 자동 압축합니다.
    압축 전 스냅샷을 저장하여 데이터 손실을 방지합니다.

    Usage:
        compactor = PreemptiveCompactor()

        # 메시지 추가
        compactor.add_message(MessageItem(role="user", content="Hello"))

        # 메트릭 확인
        metrics = compactor.get_metrics()
        if metrics.usage_ratio > 0.8:
            result = await compactor.compress()

        # 자동 압축 활성화
        compactor.auto_compress = True
    """

    # 설정
    max_tokens: int = 128000
    warning_threshold: float = 0.7  # 70%에서 경고
    compression_threshold: float = 0.8  # 80%에서 자동 압축
    auto_compress: bool = False  # 자동 압축 활성화
    default_strategy: CompressionStrategy = CompressionStrategy.HYBRID
    default_level: CompressionLevel = CompressionLevel.MODERATE

    # 상태
    _messages: list[MessageItem] = field(default_factory=list)
    _compression_history: list[CompressionResult] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    # 우선순위 설정 (role별 기본 우선순위)
    _role_priorities: dict[str, int] = field(
        default_factory=lambda: {
            "system": 1,  # 시스템 메시지 최우선
            "user": 3,  # 사용자 메시지 높음
            "assistant": 5,  # 어시스턴트 보통
        }
    )

    def __post_init__(self) -> None:
        """초기화 후 처리."""
        self._lock = asyncio.Lock()

    def add_message(
        self,
        message: MessageItem | None = None,
        *,
        role: str = "",
        content: str = "",
        priority: int | None = None,
    ) -> None:
        """메시지 추가.

        Args:
            message: MessageItem 또는 개별 파라미터
            role: 메시지 역할
            content: 메시지 내용
            priority: 우선순위 (None이면 역할 기반)
        """
        if message is None:
            if not role or not content:
                return

            msg_priority = priority or self._role_priorities.get(role, 5)
            token_count = self._estimate_tokens(content)

            message = MessageItem(
                role=role,
                content=content,
                priority=msg_priority,
                token_count=token_count,
            )

        if message.token_count == 0:
            message.token_count = self._estimate_tokens(message.content)

        self._messages.append(message)

        # 자동 압축 체크
        if self.auto_compress:
            metrics = self.get_metrics()
            if metrics.usage_ratio >= self.compression_threshold:
                asyncio.create_task(self._auto_compress())

    def _estimate_tokens(self, text: str) -> int:
        """토큰 수 추정 (간단한 휴리스틱)."""
        # 영어: ~4자당 1토큰, 한글: ~2자당 1토큰
        # 혼합 텍스트 평균으로 ~3자당 1토큰
        return max(1, len(text) // 3)

    def get_metrics(self) -> ContextMetrics:
        """현재 컨텍스트 메트릭."""
        if not self._messages:
            return ContextMetrics(max_tokens=self.max_tokens)

        total_tokens = sum(m.token_count for m in self._messages)
        oldest_age = max(m.age_seconds for m in self._messages) if self._messages else 0

        # 중복 비율 계산
        hashes = [m.content_hash for m in self._messages]
        unique_hashes = set(hashes)
        duplicate_ratio = 1 - (len(unique_hashes) / len(hashes)) if hashes else 0

        return ContextMetrics(
            total_tokens=total_tokens,
            max_tokens=self.max_tokens,
            message_count=len(self._messages),
            oldest_message_age_seconds=oldest_age,
            duplicate_ratio=duplicate_ratio,
        )

    async def compress(
        self,
        strategy: CompressionStrategy | None = None,
        level: CompressionLevel | None = None,
        save_snapshot: bool = True,
    ) -> CompressionResult:
        """컨텍스트 압축 실행.

        Args:
            strategy: 압축 전략 (None이면 기본값)
            level: 압축 수준 (None이면 기본값)
            save_snapshot: 압축 전 스냅샷 저장 여부

        Returns:
            압축 결과
        """
        start_time = time.perf_counter()
        strategy = strategy or self.default_strategy
        level = level or self.default_level

        async with self._lock:
            before_metrics = self.get_metrics()

            result = CompressionResult(
                strategy_used=strategy,
                level=level,
                before_tokens=before_metrics.total_tokens,
            )

            # 스냅샷 저장
            if save_snapshot:
                result.snapshot_id = await self._save_snapshot()

            try:
                # 압축 실행
                if strategy == CompressionStrategy.TRIM_OLD:
                    removed = self._compress_trim_old(level)
                elif strategy == CompressionStrategy.DEDUPLICATE:
                    removed = self._compress_deduplicate()
                elif strategy == CompressionStrategy.PRIORITY_FILTER:
                    removed = self._compress_priority_filter(level)
                elif strategy == CompressionStrategy.HYBRID:
                    removed = self._compress_hybrid(level)
                else:
                    # SUMMARIZE는 LLM 필요 - 여기서는 HYBRID로 대체
                    removed = self._compress_hybrid(level)

                after_metrics = self.get_metrics()

                result.success = True
                result.after_tokens = after_metrics.total_tokens
                result.tokens_removed = result.before_tokens - result.after_tokens
                result.messages_removed = removed

                logger.info(
                    f"[Compactor] Compression complete: {result.tokens_removed} tokens "
                    f"({result.compression_ratio:.1%}), {removed} messages removed"
                )

            except Exception as e:
                result.success = False
                result.error = str(e)
                logger.error(f"[Compactor] Compression failed: {e}")

            result.duration_ms = (time.perf_counter() - start_time) * 1000
            self._compression_history.append(result)

            return result

    def _compress_trim_old(self, level: CompressionLevel) -> int:
        """오래된 메시지 제거."""
        if not self._messages:
            return 0

        # 제거할 비율 결정
        trim_ratio = {
            CompressionLevel.LIGHT: 0.2,
            CompressionLevel.MODERATE: 0.4,
            CompressionLevel.AGGRESSIVE: 0.6,
        }[level]

        # 시스템 메시지 제외하고 정렬
        non_system = [m for m in self._messages if m.role != "system"]
        system_msgs = [m for m in self._messages if m.role == "system"]

        # 오래된 순으로 정렬
        non_system.sort(key=lambda m: m.timestamp)

        # 제거할 개수
        remove_count = int(len(non_system) * trim_ratio)
        if remove_count == 0:
            return 0

        # 오래된 메시지 제거
        to_remove = {id(m) for m in non_system[:remove_count]}
        self._messages = system_msgs + [m for m in non_system if id(m) not in to_remove]

        return remove_count

    def _compress_deduplicate(self) -> int:
        """중복 메시지 제거."""
        seen_hashes: set[str] = set()
        unique_messages: list[MessageItem] = []
        removed = 0

        for msg in self._messages:
            # 시스템 메시지는 항상 유지
            if msg.role == "system":
                unique_messages.append(msg)
                continue

            if msg.content_hash not in seen_hashes:
                seen_hashes.add(msg.content_hash)
                unique_messages.append(msg)
            else:
                removed += 1

        self._messages = unique_messages
        return removed

    def _compress_priority_filter(self, level: CompressionLevel) -> int:
        """우선순위 기반 필터링."""
        if not self._messages:
            return 0

        # 레벨별 우선순위 임계값
        priority_threshold = {
            CompressionLevel.LIGHT: 8,
            CompressionLevel.MODERATE: 6,
            CompressionLevel.AGGRESSIVE: 4,
        }[level]

        original_count = len(self._messages)

        # 우선순위가 임계값 이하인 메시지만 유지
        self._messages = [
            m for m in self._messages if m.role == "system" or m.priority <= priority_threshold
        ]

        return original_count - len(self._messages)

    def _compress_hybrid(self, level: CompressionLevel) -> int:
        """복합 압축 전략."""
        total_removed = 0

        # 1단계: 중복 제거
        total_removed += self._compress_deduplicate()

        # 2단계: 오래된 메시지 제거 (50% 비율로)
        if level in (CompressionLevel.MODERATE, CompressionLevel.AGGRESSIVE):
            lighter_level = (
                CompressionLevel.LIGHT
                if level == CompressionLevel.MODERATE
                else CompressionLevel.MODERATE
            )
            total_removed += self._compress_trim_old(lighter_level)

        # 3단계: 우선순위 필터 (aggressive에서만)
        if level == CompressionLevel.AGGRESSIVE:
            total_removed += self._compress_priority_filter(CompressionLevel.LIGHT)

        return total_removed

    async def _save_snapshot(self) -> str | None:
        """압축 전 스냅샷 저장."""
        try:
            from .session_persistence import get_session_persistence

            persistence = get_session_persistence()

            # 스냅샷 ID 생성
            snapshot_id = f"compactor-{int(time.time())}"

            # 메시지 직렬화
            messages_data = [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "token_count": m.token_count,
                    "priority": m.priority,
                }
                for m in self._messages
            ]

            # SessionPersistence의 in-memory 폴백 사용
            key = f"compactor:snapshot:{snapshot_id}"
            import json

            persistence._in_memory_fallback[key] = {
                "data": json.dumps(messages_data),
                "expires_at": time.time() + 3600,  # 1시간 유지
            }

            logger.debug(f"[Compactor] Saved snapshot: {snapshot_id}")
            return snapshot_id

        except Exception as e:
            logger.warning(f"[Compactor] Failed to save snapshot: {e}")
            return None

    async def restore_from_snapshot(self, snapshot_id: str) -> bool:
        """스냅샷에서 복원.

        Args:
            snapshot_id: 스냅샷 ID

        Returns:
            복원 성공 여부
        """
        try:
            from .session_persistence import get_session_persistence

            persistence = get_session_persistence()

            key = f"compactor:snapshot:{snapshot_id}"
            entry = persistence._in_memory_fallback.get(key)

            if not entry or entry["expires_at"] <= time.time():
                logger.warning(f"[Compactor] Snapshot not found or expired: {snapshot_id}")
                return False

            import json

            messages_data = json.loads(entry["data"])

            async with self._lock:
                self._messages = [
                    MessageItem(
                        role=m["role"],
                        content=m["content"],
                        timestamp=m["timestamp"],
                        token_count=m["token_count"],
                        priority=m["priority"],
                    )
                    for m in messages_data
                ]

            logger.info(f"[Compactor] Restored from snapshot: {snapshot_id}")
            return True

        except Exception as e:
            logger.error(f"[Compactor] Failed to restore from snapshot: {e}")
            return False

    async def _auto_compress(self) -> None:
        """자동 압축 실행."""
        metrics = self.get_metrics()
        if metrics.usage_ratio < self.compression_threshold:
            return

        logger.info(f"[Compactor] Auto-compress triggered at {metrics.usage_percent:.1f}%")
        await self.compress()

    def clear(self) -> None:
        """모든 메시지 제거."""
        self._messages.clear()

    def get_messages(self, include_system: bool = True) -> list[MessageItem]:
        """메시지 목록 조회.

        Args:
            include_system: 시스템 메시지 포함 여부

        Returns:
            메시지 목록
        """
        if include_system:
            return list(self._messages)
        return [m for m in self._messages if m.role != "system"]

    def get_compression_history(self, limit: int = 10) -> list[CompressionResult]:
        """압축 히스토리 조회.

        Args:
            limit: 최대 개수

        Returns:
            최근 압축 결과 목록
        """
        return list(reversed(self._compression_history[-limit:]))

    def should_compress(self) -> bool:
        """압축 필요 여부."""
        return self.get_metrics().usage_ratio >= self.compression_threshold

    def should_warn(self) -> bool:
        """경고 필요 여부."""
        return self.get_metrics().usage_ratio >= self.warning_threshold

    def get_status(self) -> dict[str, Any]:
        """현재 상태 요약."""
        metrics = self.get_metrics()
        return {
            "metrics": metrics.to_dict(),
            "should_warn": self.should_warn(),
            "should_compress": self.should_compress(),
            "auto_compress": self.auto_compress,
            "compression_count": len(self._compression_history),
            "last_compression": (
                self._compression_history[-1].to_dict() if self._compression_history else None
            ),
        }


# 싱글톤 인스턴스
_compactor: PreemptiveCompactor | None = None


def get_preemptive_compactor() -> PreemptiveCompactor:
    """PreemptiveCompactor 싱글톤 반환."""
    global _compactor
    if _compactor is None:
        _compactor = PreemptiveCompactor()
    return _compactor
