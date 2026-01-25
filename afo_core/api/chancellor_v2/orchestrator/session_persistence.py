# Trinity Score: 95.0 (永 - Eternal Session Recovery)
"""Session Persistence for Chancellor Orchestrator.

Redis 기반 세션 영속화로 장애 복구 및 컨텍스트 유지를 지원합니다.

AFO 철학:
- 永 (Eternity): 세션 영속성
- 孝 (Serenity): 투명한 복구 (사용자 인지 불필요)
- 善 (Goodness): 안전한 상태 관리
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# Redis 키 프리픽스
SESSION_PREFIX = "afo:chancellor:session:"
CONTEXT_PREFIX = "afo:chancellor:context:"


@dataclass
class SessionData:
    """세션 데이터 구조."""

    session_id: str
    thread_id: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: float = 0.0  # 0이면 만료 없음

    # 세션 상태
    status: str = "active"  # active, paused, completed, error
    current_pillar: str | None = None
    completed_pillars: list[str] = field(default_factory=list)

    # 입력/출력 캐시
    input_cache: dict[str, Any] = field(default_factory=dict)
    plan_cache: dict[str, Any] = field(default_factory=dict)

    # 메타데이터
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "session_id": self.session_id,
            "thread_id": self.thread_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "status": self.status,
            "current_pillar": self.current_pillar,
            "completed_pillars": self.completed_pillars,
            "input_cache": self.input_cache,
            "plan_cache": self.plan_cache,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionData:
        """딕셔너리에서 생성."""
        return cls(
            session_id=data.get("session_id", ""),
            thread_id=data.get("thread_id", ""),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            expires_at=data.get("expires_at", 0.0),
            status=data.get("status", "active"),
            current_pillar=data.get("current_pillar"),
            completed_pillars=data.get("completed_pillars", []),
            input_cache=data.get("input_cache", {}),
            plan_cache=data.get("plan_cache", {}),
            metadata=data.get("metadata", {}),
        )

    def is_expired(self) -> bool:
        """만료 여부 확인."""
        if self.expires_at == 0.0:
            return False
        return time.time() > self.expires_at


@dataclass
class ContextSnapshot:
    """Strategist 컨텍스트 스냅샷."""

    pillar: str
    score: float
    reasoning: str
    recommendations: list[str]
    warnings: list[str]
    errors: list[str]
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "pillar": self.pillar,
            "score": self.score,
            "reasoning": self.reasoning,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "errors": self.errors,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextSnapshot:
        """딕셔너리에서 생성."""
        return cls(
            pillar=data.get("pillar", ""),
            score=data.get("score", 0.0),
            reasoning=data.get("reasoning", ""),
            recommendations=data.get("recommendations", []),
            warnings=data.get("warnings", []),
            errors=data.get("errors", []),
            duration_ms=data.get("duration_ms", 0.0),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionPersistence:
    """Redis 기반 세션 영속화 관리자.

    세션 상태를 Redis에 저장하여 장애 복구 및 세션 이어가기를 지원합니다.

    Usage:
        persistence = SessionPersistence(redis_client)

        # 세션 생성/저장
        session = SessionData(session_id="abc", thread_id="thread-1")
        await persistence.save_session(session)

        # 세션 복구
        session = await persistence.load_session("abc")

        # 컨텍스트 스냅샷 저장
        snapshot = ContextSnapshot(pillar="truth", score=0.95, ...)
        await persistence.save_context_snapshot("abc", snapshot)

        # 세션 복구 가능 여부 확인
        can_resume = await persistence.can_resume("abc")
    """

    redis_client: Any = None  # redis.asyncio.Redis
    default_ttl_seconds: int = 3600  # 1시간
    _in_memory_fallback: dict[str, Any] = field(default_factory=dict)

    def _get_session_key(self, session_id: str) -> str:
        """세션 Redis 키 생성."""
        return f"{SESSION_PREFIX}{session_id}"

    def _get_context_key(self, session_id: str, pillar: str) -> str:
        """컨텍스트 Redis 키 생성."""
        return f"{CONTEXT_PREFIX}{session_id}:{pillar}"

    async def save_session(self, session: SessionData, ttl_seconds: int | None = None) -> bool:
        """세션 저장.

        Args:
            session: 세션 데이터
            ttl_seconds: TTL (None이면 기본값 사용)

        Returns:
            저장 성공 여부
        """
        session.updated_at = time.time()
        ttl = ttl_seconds or self.default_ttl_seconds

        if session.expires_at == 0.0:
            session.expires_at = time.time() + ttl

        key = self._get_session_key(session.session_id)
        data = json.dumps(session.to_dict())

        try:
            if self.redis_client:
                await self.redis_client.setex(key, ttl, data)
            else:
                # In-memory 폴백
                self._in_memory_fallback[key] = {
                    "data": data,
                    "expires_at": time.time() + ttl,
                }

            logger.debug(f"[SessionPersistence] Saved session: {session.session_id}")
            return True

        except Exception as e:
            logger.error(f"[SessionPersistence] Failed to save session: {e}")
            return False

    async def load_session(self, session_id: str) -> SessionData | None:
        """세션 로드.

        Args:
            session_id: 세션 ID

        Returns:
            세션 데이터 (없거나 만료되면 None)
        """
        key = self._get_session_key(session_id)

        try:
            if self.redis_client:
                data = await self.redis_client.get(key)
            else:
                # In-memory 폴백
                entry = self._in_memory_fallback.get(key)
                data = entry["data"] if entry and entry["expires_at"] > time.time() else None

            if not data:
                return None

            if isinstance(data, bytes):
                data = data.decode("utf-8")

            session = SessionData.from_dict(json.loads(data))

            if session.is_expired():
                logger.debug(f"[SessionPersistence] Session expired: {session_id}")
                await self.delete_session(session_id)
                return None

            logger.debug(f"[SessionPersistence] Loaded session: {session_id}")
            return session

        except Exception as e:
            logger.error(f"[SessionPersistence] Failed to load session: {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """세션 삭제.

        Args:
            session_id: 세션 ID

        Returns:
            삭제 성공 여부
        """
        key = self._get_session_key(session_id)

        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                self._in_memory_fallback.pop(key, None)

            # 컨텍스트 스냅샷도 삭제
            for pillar in ["truth", "goodness", "beauty"]:
                ctx_key = self._get_context_key(session_id, pillar)
                if self.redis_client:
                    await self.redis_client.delete(ctx_key)
                else:
                    self._in_memory_fallback.pop(ctx_key, None)

            logger.debug(f"[SessionPersistence] Deleted session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"[SessionPersistence] Failed to delete session: {e}")
            return False

    async def save_context_snapshot(self, session_id: str, snapshot: ContextSnapshot) -> bool:
        """컨텍스트 스냅샷 저장.

        Args:
            session_id: 세션 ID
            snapshot: 컨텍스트 스냅샷

        Returns:
            저장 성공 여부
        """
        key = self._get_context_key(session_id, snapshot.pillar)
        data = json.dumps(snapshot.to_dict())

        try:
            if self.redis_client:
                await self.redis_client.setex(key, self.default_ttl_seconds, data)
            else:
                self._in_memory_fallback[key] = {
                    "data": data,
                    "expires_at": time.time() + self.default_ttl_seconds,
                }

            logger.debug(
                f"[SessionPersistence] Saved context snapshot: {session_id}/{snapshot.pillar}"
            )
            return True

        except Exception as e:
            logger.error(f"[SessionPersistence] Failed to save context snapshot: {e}")
            return False

    async def load_context_snapshot(self, session_id: str, pillar: str) -> ContextSnapshot | None:
        """컨텍스트 스냅샷 로드.

        Args:
            session_id: 세션 ID
            pillar: 기둥 이름

        Returns:
            컨텍스트 스냅샷 (없으면 None)
        """
        key = self._get_context_key(session_id, pillar)

        try:
            if self.redis_client:
                data = await self.redis_client.get(key)
            else:
                entry = self._in_memory_fallback.get(key)
                data = entry["data"] if entry and entry["expires_at"] > time.time() else None

            if not data:
                return None

            if isinstance(data, bytes):
                data = data.decode("utf-8")

            return ContextSnapshot.from_dict(json.loads(data))

        except Exception as e:
            logger.error(f"[SessionPersistence] Failed to load context snapshot: {e}")
            return None

    async def load_all_context_snapshots(self, session_id: str) -> dict[str, ContextSnapshot]:
        """세션의 모든 컨텍스트 스냅샷 로드.

        Args:
            session_id: 세션 ID

        Returns:
            pillar -> ContextSnapshot 매핑
        """
        snapshots = {}
        for pillar in ["truth", "goodness", "beauty"]:
            snapshot = await self.load_context_snapshot(session_id, pillar)
            if snapshot:
                snapshots[pillar] = snapshot
        return snapshots

    async def can_resume(self, session_id: str) -> bool:
        """세션 재개 가능 여부 확인.

        Args:
            session_id: 세션 ID

        Returns:
            재개 가능 여부
        """
        session = await self.load_session(session_id)
        if not session:
            return False

        # 완료되지 않은 세션만 재개 가능
        return session.status in ("active", "paused")

    async def get_resumable_sessions(
        self, thread_id: str | None = None, limit: int = 10
    ) -> list[SessionData]:
        """재개 가능한 세션 목록 조회.

        Args:
            thread_id: 스레드 ID로 필터 (None이면 전체)
            limit: 최대 개수

        Returns:
            재개 가능한 세션 목록
        """
        # In-memory 폴백에서만 구현 (Redis는 SCAN 필요)
        sessions = []

        for key, entry in self._in_memory_fallback.items():
            if not key.startswith(SESSION_PREFIX):
                continue

            if entry["expires_at"] <= time.time():
                continue

            try:
                data = json.loads(entry["data"])
                session = SessionData.from_dict(data)

                if session.status not in ("active", "paused"):
                    continue

                if thread_id and session.thread_id != thread_id:
                    continue

                sessions.append(session)

                if len(sessions) >= limit:
                    break

            except (json.JSONDecodeError, KeyError):
                continue

        # 최신순 정렬
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions[:limit]

    async def update_session_status(
        self, session_id: str, status: str, current_pillar: str | None = None
    ) -> bool:
        """세션 상태 업데이트.

        Args:
            session_id: 세션 ID
            status: 새 상태
            current_pillar: 현재 진행 중인 pillar

        Returns:
            업데이트 성공 여부
        """
        session = await self.load_session(session_id)
        if not session:
            return False

        session.status = status
        if current_pillar:
            session.current_pillar = current_pillar

        return await self.save_session(session)

    async def mark_pillar_completed(self, session_id: str, pillar: str) -> bool:
        """Pillar 완료 표시.

        Args:
            session_id: 세션 ID
            pillar: 완료된 pillar

        Returns:
            업데이트 성공 여부
        """
        session = await self.load_session(session_id)
        if not session:
            return False

        if pillar not in session.completed_pillars:
            session.completed_pillars.append(pillar)

        # 모든 pillar 완료 확인
        if set(session.completed_pillars) >= {"truth", "goodness", "beauty"}:
            session.status = "completed"
            session.current_pillar = None
        else:
            session.current_pillar = None

        return await self.save_session(session)


# 싱글톤 인스턴스
_persistence: SessionPersistence | None = None


def get_session_persistence(redis_client: Any = None) -> SessionPersistence:
    """SessionPersistence 싱글톤 반환.

    Args:
        redis_client: Redis 클라이언트 (최초 호출 시에만 사용)

    Returns:
        SessionPersistence 인스턴스
    """
    global _persistence
    if _persistence is None:
        _persistence = SessionPersistence(redis_client=redis_client)
    return _persistence
