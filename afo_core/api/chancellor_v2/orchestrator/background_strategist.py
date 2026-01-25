# Trinity Score: 94.0 (孝 - Seamless Background Execution)
"""Background Strategist for Async Task Execution.

Strategist 평가를 백그라운드에서 비동기 실행하고 상태를 추적합니다.

AFO 철학:
- 孝 (Serenity): 사용자 대기 시간 최소화
- 善 (Goodness): 태스크 누수 방지, 안전한 취소
- 眞 (Truth): 정확한 상태 추적
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Coroutine
from uuid import uuid4

if TYPE_CHECKING:
    from .strategist_context import StrategistContext

logger = logging.getLogger(__name__)


class TaskState(str, Enum):
    """백그라운드 태스크 상태."""

    PENDING = "pending"  # 대기 중
    RUNNING = "running"  # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    CANCELLED = "cancelled"  # 취소됨


# 콜백 타입 정의
ProgressCallback = Callable[[str, TaskState, float], Coroutine[Any, Any, None]]
ResultCallback = Callable[
    [str, "StrategistContext | None", Exception | None], Coroutine[Any, Any, None]
]


@dataclass
class BackgroundTask:
    """백그라운드 태스크 정보."""

    task_id: str = field(default_factory=lambda: uuid4().hex[:12])
    pillar: str = ""
    state: TaskState = TaskState.PENDING
    progress: float = 0.0  # 0.0 ~ 1.0

    # 실행 정보
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0

    # 결과
    context: StrategistContext | None = None
    error: Exception | None = None

    # asyncio 태스크 참조
    _asyncio_task: asyncio.Task[Any] | None = field(default=None, repr=False)

    @property
    def duration_ms(self) -> float:
        """실행 시간 (밀리초)."""
        if self.completed_at > 0 and self.started_at > 0:
            return (self.completed_at - self.started_at) * 1000
        if self.started_at > 0:
            return (time.time() - self.started_at) * 1000
        return 0.0

    @property
    def is_done(self) -> bool:
        """완료 여부 (성공/실패/취소 포함)."""
        return self.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "task_id": self.task_id,
            "pillar": self.pillar,
            "state": self.state.value,
            "progress": self.progress,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "has_error": self.error is not None,
            "error_message": str(self.error) if self.error else None,
        }


@dataclass
class BackgroundStrategist:
    """백그라운드 Strategist 실행 관리자.

    Strategist 평가를 백그라운드에서 실행하고 상태를 추적합니다.
    태스크 누수를 방지하고 안전한 취소를 지원합니다.

    Usage:
        bg = BackgroundStrategist()

        # 백그라운드 실행
        task_id = await bg.submit(pillar="truth", coro=strategist.evaluate(ctx))

        # 상태 확인
        task = bg.get_task(task_id)
        print(f"State: {task.state}, Progress: {task.progress}")

        # 완료 대기
        result = await bg.wait_for(task_id)

        # 취소
        await bg.cancel(task_id)

        # 모든 태스크 정리
        await bg.cleanup()
    """

    # 설정
    max_concurrent_tasks: int = 5  # 최대 동시 실행 태스크
    max_history: int = 50  # 완료된 태스크 히스토리 최대 개수
    default_timeout_seconds: float = 60.0  # 기본 타임아웃

    # 상태
    _tasks: dict[str, BackgroundTask] = field(default_factory=dict)
    _history: list[BackgroundTask] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _semaphore: asyncio.Semaphore | None = field(default=None, repr=False)

    # 콜백
    _progress_callback: ProgressCallback | None = None
    _result_callback: ResultCallback | None = None

    def __post_init__(self) -> None:
        """초기화 후 처리."""
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

    def set_progress_callback(self, callback: ProgressCallback) -> None:
        """진행 상황 콜백 설정."""
        self._progress_callback = callback

    def set_result_callback(self, callback: ResultCallback) -> None:
        """결과 콜백 설정."""
        self._result_callback = callback

    async def submit(
        self,
        pillar: str,
        coro: Coroutine[Any, Any, StrategistContext],
        timeout: float | None = None,
    ) -> str:
        """백그라운드 태스크 제출.

        Args:
            pillar: Strategist pillar (truth/goodness/beauty)
            coro: 실행할 코루틴
            timeout: 타임아웃 (None이면 기본값)

        Returns:
            태스크 ID

        Raises:
            RuntimeError: 최대 동시 태스크 초과 시
        """
        async with self._lock:
            # 실행 중인 태스크 수 확인
            running_count = sum(1 for t in self._tasks.values() if t.state == TaskState.RUNNING)
            if running_count >= self.max_concurrent_tasks:
                raise RuntimeError(
                    f"Maximum concurrent tasks ({self.max_concurrent_tasks}) reached"
                )

            # 태스크 생성
            task = BackgroundTask(pillar=pillar)
            self._tasks[task.task_id] = task

            logger.info(f"[BackgroundStrategist] Submitted task {task.task_id} for {pillar}")

        # 백그라운드 실행 시작
        asyncio_task = asyncio.create_task(
            self._run_task(task.task_id, coro, timeout or self.default_timeout_seconds)
        )

        async with self._lock:
            task._asyncio_task = asyncio_task

        return task.task_id

    async def _run_task(
        self,
        task_id: str,
        coro: Coroutine[Any, Any, StrategistContext],
        timeout: float,
    ) -> None:
        """태스크 실행 (내부)."""
        task = self._tasks.get(task_id)
        if not task:
            return

        assert self._semaphore is not None

        try:
            async with self._semaphore:
                # 상태 업데이트: RUNNING
                async with self._lock:
                    task.state = TaskState.RUNNING
                    task.started_at = time.time()

                await self._notify_progress(task_id, TaskState.RUNNING, 0.1)

                # 실행
                try:
                    result = await asyncio.wait_for(coro, timeout=timeout)

                    # 상태 업데이트: COMPLETED
                    async with self._lock:
                        task.state = TaskState.COMPLETED
                        task.completed_at = time.time()
                        task.context = result
                        task.progress = 1.0

                    await self._notify_progress(task_id, TaskState.COMPLETED, 1.0)
                    await self._notify_result(task_id, result, None)

                    logger.info(
                        f"[BackgroundStrategist] Task {task_id} completed "
                        f"(duration={task.duration_ms:.1f}ms)"
                    )

                except TimeoutError:
                    async with self._lock:
                        task.state = TaskState.FAILED
                        task.completed_at = time.time()
                        task.error = TimeoutError(f"Task timed out after {timeout}s")

                    await self._notify_progress(task_id, TaskState.FAILED, task.progress)
                    await self._notify_result(task_id, None, task.error)

                    logger.warning(f"[BackgroundStrategist] Task {task_id} timed out")

                except asyncio.CancelledError:
                    async with self._lock:
                        task.state = TaskState.CANCELLED
                        task.completed_at = time.time()

                    await self._notify_progress(task_id, TaskState.CANCELLED, task.progress)
                    logger.info(f"[BackgroundStrategist] Task {task_id} cancelled")
                    raise

                except Exception as e:
                    async with self._lock:
                        task.state = TaskState.FAILED
                        task.completed_at = time.time()
                        task.error = e

                    await self._notify_progress(task_id, TaskState.FAILED, task.progress)
                    await self._notify_result(task_id, None, e)

                    logger.error(f"[BackgroundStrategist] Task {task_id} failed: {e}")

        finally:
            # 완료된 태스크를 히스토리로 이동
            await self._move_to_history(task_id)

    async def _notify_progress(self, task_id: str, state: TaskState, progress: float) -> None:
        """진행 상황 콜백 호출."""
        if self._progress_callback:
            try:
                await self._progress_callback(task_id, state, progress)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    async def _notify_result(
        self,
        task_id: str,
        context: StrategistContext | None,
        error: Exception | None,
    ) -> None:
        """결과 콜백 호출."""
        if self._result_callback:
            try:
                await self._result_callback(task_id, context, error)
            except Exception as e:
                logger.warning(f"Result callback error: {e}")

    async def _move_to_history(self, task_id: str) -> None:
        """완료된 태스크를 히스토리로 이동."""
        async with self._lock:
            task = self._tasks.pop(task_id, None)
            if task and task.is_done:
                self._history.append(task)
                # 히스토리 크기 제한
                while len(self._history) > self.max_history:
                    self._history.pop(0)

    def get_task(self, task_id: str) -> BackgroundTask | None:
        """태스크 조회.

        Args:
            task_id: 태스크 ID

        Returns:
            태스크 정보 (없으면 None)
        """
        # 활성 태스크에서 먼저 찾기
        task = self._tasks.get(task_id)
        if task:
            return task

        # 히스토리에서 찾기
        for t in self._history:
            if t.task_id == task_id:
                return t

        return None

    async def wait_for(
        self, task_id: str, timeout: float | None = None
    ) -> StrategistContext | None:
        """태스크 완료 대기.

        Args:
            task_id: 태스크 ID
            timeout: 대기 타임아웃

        Returns:
            결과 컨텍스트 (실패/취소 시 None)

        Raises:
            asyncio.TimeoutError: 타임아웃 시
            KeyError: 태스크를 찾을 수 없을 때
        """
        task = self._tasks.get(task_id)
        if not task:
            # 히스토리에서 찾기
            for t in self._history:
                if t.task_id == task_id:
                    return t.context
            raise KeyError(f"Task not found: {task_id}")

        if task.is_done:
            return task.context

        if task._asyncio_task:
            try:
                await asyncio.wait_for(
                    asyncio.shield(task._asyncio_task),
                    timeout=timeout,
                )
            except asyncio.CancelledError:
                pass
            except TimeoutError:
                raise

        # 완료 후 결과 반환
        updated_task = self.get_task(task_id)
        return updated_task.context if updated_task else None

    async def wait_all(
        self, task_ids: list[str] | None = None, timeout: float | None = None
    ) -> dict[str, StrategistContext | None]:
        """여러 태스크 완료 대기.

        Args:
            task_ids: 대기할 태스크 ID 목록 (None이면 모든 활성 태스크)
            timeout: 전체 타임아웃

        Returns:
            task_id -> context 매핑
        """
        if task_ids is None:
            task_ids = list(self._tasks.keys())

        results: dict[str, StrategistContext | None] = {}

        async def wait_single(tid: str) -> tuple[str, StrategistContext | None]:
            try:
                ctx = await self.wait_for(tid, timeout=timeout)
                return tid, ctx
            except (TimeoutError, KeyError):
                return tid, None

        tasks = [wait_single(tid) for tid in task_ids]
        completed = await asyncio.gather(*tasks)

        for tid, ctx in completed:
            results[tid] = ctx

        return results

    async def cancel(self, task_id: str) -> bool:
        """태스크 취소.

        Args:
            task_id: 취소할 태스크 ID

        Returns:
            취소 성공 여부
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.is_done:
            return False

        if task._asyncio_task and not task._asyncio_task.done():
            task._asyncio_task.cancel()
            logger.info(f"[BackgroundStrategist] Cancelling task {task_id}")
            return True

        return False

    async def cancel_all(self) -> int:
        """모든 활성 태스크 취소.

        Returns:
            취소된 태스크 수
        """
        cancelled = 0
        for task_id in list(self._tasks.keys()):
            if await self.cancel(task_id):
                cancelled += 1
        return cancelled

    async def cleanup(self) -> None:
        """모든 태스크 정리 및 리소스 해제."""
        await self.cancel_all()

        # 모든 태스크 완료 대기 (짧은 타임아웃)
        for task in list(self._tasks.values()):
            if task._asyncio_task and not task._asyncio_task.done():
                try:
                    await asyncio.wait_for(task._asyncio_task, timeout=1.0)
                except (TimeoutError, asyncio.CancelledError):
                    pass

        async with self._lock:
            self._tasks.clear()

        logger.info("[BackgroundStrategist] Cleanup completed")

    def get_active_tasks(self) -> list[BackgroundTask]:
        """활성 태스크 목록."""
        return [t for t in self._tasks.values() if not t.is_done]

    def get_status(self) -> dict[str, Any]:
        """현재 상태 요약.

        Returns:
            상태 정보 딕셔너리
        """
        active = self.get_active_tasks()
        return {
            "active_count": len(active),
            "max_concurrent": self.max_concurrent_tasks,
            "history_count": len(self._history),
            "tasks": {
                "pending": sum(1 for t in active if t.state == TaskState.PENDING),
                "running": sum(1 for t in active if t.state == TaskState.RUNNING),
            },
            "active_pillars": [t.pillar for t in active],
        }


# 싱글톤 인스턴스
_background_strategist: BackgroundStrategist | None = None


def get_background_strategist() -> BackgroundStrategist:
    """BackgroundStrategist 싱글톤 반환."""
    global _background_strategist
    if _background_strategist is None:
        _background_strategist = BackgroundStrategist()
    return _background_strategist
