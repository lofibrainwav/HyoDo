# Trinity Score: 94.0 (孝 - Lifecycle Harmony)
"""Chancellor Hooks for Lifecycle Management.

Orchestrator 라이프사이클 이벤트에 훅을 등록하여 확장성을 제공합니다.

AFO 철학:
- 孝 (Serenity): 부드러운 라이프사이클 전환
- 善 (Goodness): 안전한 훅 실행 (실패 격리)
- 永 (Eternity): 이벤트 기록 및 추적
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class HookEvent(str, Enum):
    """훅 이벤트 타입."""

    SESSION_START = "session_start"  # 세션 시작
    BEFORE_ORCHESTRATE = "before_orchestrate"  # 오케스트레이션 전
    AFTER_STRATEGIST = "after_strategist"  # 개별 Strategist 완료 후
    AFTER_ORCHESTRATE = "after_orchestrate"  # 오케스트레이션 완료 후
    ON_ERROR = "on_error"  # 에러 발생 시
    SESSION_END = "session_end"  # 세션 종료


# 훅 함수 타입 정의
HookFunc = Callable[..., Coroutine[Any, Any, None]]


@dataclass
class HookResult:
    """훅 실행 결과."""

    event: HookEvent
    hook_name: str
    success: bool
    duration_ms: float
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HookRegistration:
    """훅 등록 정보."""

    event: HookEvent
    name: str
    func: HookFunc
    priority: int = 0  # 높을수록 먼저 실행
    enabled: bool = True
    timeout_seconds: float = 5.0  # 훅 타임아웃


@dataclass
class ChancellorHooks:
    """Chancellor 라이프사이클 훅 관리자.

    Orchestrator 실행 과정에서 다양한 이벤트에 훅을 등록하고 실행합니다.
    훅 실패는 격리되어 메인 로직에 영향을 주지 않습니다.

    Usage:
        hooks = ChancellorHooks()

        @hooks.on(HookEvent.BEFORE_ORCHESTRATE)
        async def log_start(state, **kwargs):
            logger.info(f"Starting orchestration for: {state.input}")

        @hooks.on(HookEvent.AFTER_STRATEGIST)
        async def record_result(pillar, context, **kwargs):
            logger.info(f"{pillar} scored: {context.score}")

        # Orchestrator에서 사용
        await hooks.emit(HookEvent.BEFORE_ORCHESTRATE, state=state)
    """

    _hooks: dict[HookEvent, list[HookRegistration]] = field(default_factory=dict)
    _history: list[HookResult] = field(default_factory=list)
    max_history: int = 100
    fail_silent: bool = True  # True면 훅 실패해도 예외 발생 안함

    def __post_init__(self) -> None:
        """초기화 후 이벤트별 빈 리스트 생성."""
        for event in HookEvent:
            if event not in self._hooks:
                self._hooks[event] = []

    def on(
        self,
        event: HookEvent,
        *,
        name: str | None = None,
        priority: int = 0,
        timeout: float = 5.0,
    ) -> Callable[[HookFunc], HookFunc]:
        """훅 등록 데코레이터.

        Args:
            event: 훅 이벤트 타입
            name: 훅 이름 (None이면 함수명 사용)
            priority: 우선순위 (높을수록 먼저 실행)
            timeout: 타임아웃 (초)

        Returns:
            데코레이터 함수

        Example:
            @hooks.on(HookEvent.BEFORE_ORCHESTRATE, priority=10)
            async def my_hook(state, **kwargs):
                ...
        """

        def decorator(func: HookFunc) -> HookFunc:
            hook_name = name or func.__name__
            registration = HookRegistration(
                event=event,
                name=hook_name,
                func=func,
                priority=priority,
                timeout_seconds=timeout,
            )
            self.register(registration)
            return func

        return decorator

    def register(self, registration: HookRegistration) -> None:
        """훅 직접 등록.

        Args:
            registration: 훅 등록 정보
        """
        self._hooks[registration.event].append(registration)
        # 우선순위 정렬 (높은 것 먼저)
        self._hooks[registration.event].sort(key=lambda h: -h.priority)
        logger.debug(
            f"[Hooks] Registered '{registration.name}' for {registration.event.value} "
            f"(priority={registration.priority})"
        )

    def unregister(self, event: HookEvent, name: str) -> bool:
        """훅 등록 해제.

        Args:
            event: 훅 이벤트
            name: 훅 이름

        Returns:
            해제 성공 여부
        """
        hooks = self._hooks.get(event, [])
        for i, hook in enumerate(hooks):
            if hook.name == name:
                hooks.pop(i)
                logger.debug(f"[Hooks] Unregistered '{name}' from {event.value}")
                return True
        return False

    async def emit(self, event: HookEvent, **kwargs: Any) -> list[HookResult]:
        """훅 이벤트 발생.

        등록된 모든 훅을 우선순위 순으로 실행합니다.
        훅 실패는 격리되어 다른 훅 실행에 영향을 주지 않습니다.

        Args:
            event: 발생시킬 이벤트
            **kwargs: 훅에 전달할 인자

        Returns:
            훅 실행 결과 목록
        """
        hooks = self._hooks.get(event, [])
        results: list[HookResult] = []

        for hook in hooks:
            if not hook.enabled:
                continue

            result = await self._execute_hook(hook, kwargs)
            results.append(result)
            self._add_to_history(result)

        if results:
            success_count = sum(1 for r in results if r.success)
            logger.debug(f"[Hooks] {event.value}: {success_count}/{len(results)} hooks succeeded")

        return results

    async def _execute_hook(self, hook: HookRegistration, kwargs: dict[str, Any]) -> HookResult:
        """단일 훅 안전 실행.

        Args:
            hook: 훅 등록 정보
            kwargs: 훅 인자

        Returns:
            실행 결과
        """
        start_time = time.perf_counter()

        try:
            await asyncio.wait_for(hook.func(**kwargs), timeout=hook.timeout_seconds)
            duration_ms = (time.perf_counter() - start_time) * 1000

            return HookResult(
                event=hook.event,
                hook_name=hook.name,
                success=True,
                duration_ms=duration_ms,
            )

        except TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Hook '{hook.name}' timed out after {hook.timeout_seconds}s"
            logger.warning(f"[Hooks] {error_msg}")

            if not self.fail_silent:
                raise

            return HookResult(
                event=hook.event,
                hook_name=hook.name,
                success=False,
                duration_ms=duration_ms,
                error=error_msg,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_msg = f"Hook '{hook.name}' failed: {e}"
            logger.warning(f"[Hooks] {error_msg}")

            if not self.fail_silent:
                raise

            return HookResult(
                event=hook.event,
                hook_name=hook.name,
                success=False,
                duration_ms=duration_ms,
                error=str(e),
            )

    def _add_to_history(self, result: HookResult) -> None:
        """결과를 히스토리에 추가."""
        self._history.append(result)
        if len(self._history) > self.max_history:
            self._history.pop(0)

    def get_history(self, event: HookEvent | None = None, limit: int = 20) -> list[HookResult]:
        """훅 실행 히스토리 조회.

        Args:
            event: 필터할 이벤트 (None이면 전체)
            limit: 최대 개수

        Returns:
            실행 결과 목록 (최신순)
        """
        history = self._history
        if event:
            history = [r for r in history if r.event == event]
        return list(reversed(history[-limit:]))

    def get_registered_hooks(self, event: HookEvent | None = None) -> dict[str, Any]:
        """등록된 훅 정보 조회.

        Args:
            event: 필터할 이벤트 (None이면 전체)

        Returns:
            훅 정보
        """
        if event:
            return {
                event.value: [
                    {"name": h.name, "priority": h.priority, "enabled": h.enabled}
                    for h in self._hooks.get(event, [])
                ]
            }

        return {
            e.value: [{"name": h.name, "priority": h.priority, "enabled": h.enabled} for h in hooks]
            for e, hooks in self._hooks.items()
            if hooks
        }

    def clear(self, event: HookEvent | None = None) -> None:
        """훅 등록 해제.

        Args:
            event: 해제할 이벤트 (None이면 전체)
        """
        if event:
            self._hooks[event] = []
        else:
            for e in HookEvent:
                self._hooks[e] = []
        logger.debug(f"[Hooks] Cleared hooks for {event.value if event else 'all events'}")


# 싱글톤 인스턴스
_hooks: ChancellorHooks | None = None


def get_chancellor_hooks() -> ChancellorHooks:
    """ChancellorHooks 싱글톤 반환."""
    global _hooks
    if _hooks is None:
        _hooks = ChancellorHooks()
    return _hooks
