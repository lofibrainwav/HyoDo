# Trinity Score: 95.0 (眞 - Test Coverage)
"""Tests for Chancellor V3 Phase 3 Components.

BackgroundStrategist와 PreemptiveCompactor의 핵심 기능을 검증합니다.
"""

import asyncio
import time

import pytest
from api.chancellor_v2.orchestrator.background_strategist import (
    BackgroundStrategist,
    BackgroundTask,
    TaskState,
    get_background_strategist,
)
from api.chancellor_v2.orchestrator.preemptive_compactor import (
    CompressionLevel,
    CompressionStrategy,
    ContextMetrics,
    MessageItem,
    PreemptiveCompactor,
    get_preemptive_compactor,
)
from api.chancellor_v2.orchestrator.strategist_context import StrategistContext


class TestBackgroundStrategist:
    """BackgroundStrategist 테스트."""

    @pytest.fixture
    def bg(self) -> BackgroundStrategist:
        """새 BackgroundStrategist 인스턴스."""
        return BackgroundStrategist()

    @pytest.mark.asyncio
    async def test_submit_and_wait(self, bg: BackgroundStrategist) -> None:
        """태스크 제출 및 대기."""

        async def mock_evaluate() -> StrategistContext:
            await asyncio.sleep(0.05)
            ctx = StrategistContext(pillar="TRUTH", score=0.95)
            ctx.mark_completed()
            return ctx

        task_id = await bg.submit(pillar="truth", coro=mock_evaluate())
        assert task_id is not None

        result = await bg.wait_for(task_id)
        assert result is not None
        assert result.score == 0.95

    @pytest.mark.asyncio
    async def test_task_states(self, bg: BackgroundStrategist) -> None:
        """태스크 상태 전환."""
        states_seen: list[TaskState] = []

        async def progress_cb(task_id: str, state: TaskState, progress: float) -> None:
            states_seen.append(state)

        bg.set_progress_callback(progress_cb)

        async def mock_evaluate() -> StrategistContext:
            await asyncio.sleep(0.05)
            return StrategistContext(pillar="TRUTH")

        task_id = await bg.submit(pillar="truth", coro=mock_evaluate())
        await bg.wait_for(task_id)

        assert TaskState.RUNNING in states_seen
        assert TaskState.COMPLETED in states_seen

    @pytest.mark.asyncio
    async def test_task_cancellation(self, bg: BackgroundStrategist) -> None:
        """태스크 취소."""

        async def slow_evaluate() -> StrategistContext:
            await asyncio.sleep(10.0)  # 긴 작업
            return StrategistContext(pillar="TRUTH")

        task_id = await bg.submit(pillar="truth", coro=slow_evaluate())

        # 약간 대기 후 취소
        await asyncio.sleep(0.05)
        cancelled = await bg.cancel(task_id)

        assert cancelled is True

        # 취소된 태스크 확인
        await asyncio.sleep(0.1)
        task = bg.get_task(task_id)
        assert task is not None
        assert task.state == TaskState.CANCELLED

    @pytest.mark.asyncio
    async def test_task_timeout(self, bg: BackgroundStrategist) -> None:
        """태스크 타임아웃."""

        async def slow_evaluate() -> StrategistContext:
            await asyncio.sleep(10.0)
            return StrategistContext(pillar="TRUTH")

        task_id = await bg.submit(pillar="truth", coro=slow_evaluate(), timeout=0.1)

        # 타임아웃 대기
        await asyncio.sleep(0.3)

        task = bg.get_task(task_id)
        assert task is not None
        assert task.state == TaskState.FAILED
        assert task.error is not None

    @pytest.mark.asyncio
    async def test_max_concurrent_tasks(self, bg: BackgroundStrategist) -> None:
        """최대 동시 태스크 제한."""
        bg.max_concurrent_tasks = 2

        async def slow_evaluate() -> StrategistContext:
            await asyncio.sleep(1.0)
            return StrategistContext(pillar="TRUTH")

        # 2개 제출 성공
        await bg.submit(pillar="truth", coro=slow_evaluate())
        await bg.submit(pillar="goodness", coro=slow_evaluate())

        # 태스크가 RUNNING 상태가 될 때까지 대기
        await asyncio.sleep(0.1)

        # 3번째는 실패해야 함
        with pytest.raises(RuntimeError, match="Maximum concurrent tasks"):
            await bg.submit(pillar="beauty", coro=slow_evaluate())

        await bg.cleanup()

    @pytest.mark.asyncio
    async def test_wait_all(self, bg: BackgroundStrategist) -> None:
        """여러 태스크 동시 대기."""

        async def mock_evaluate(pillar: str) -> StrategistContext:
            await asyncio.sleep(0.05)
            return StrategistContext(pillar=pillar, score=0.9)

        task_ids = []
        for pillar in ["truth", "goodness", "beauty"]:
            tid = await bg.submit(pillar=pillar, coro=mock_evaluate(pillar))
            task_ids.append(tid)

        results = await bg.wait_all(task_ids)

        assert len(results) == 3
        assert all(ctx is not None for ctx in results.values())

    @pytest.mark.asyncio
    async def test_result_callback(self, bg: BackgroundStrategist) -> None:
        """결과 콜백."""
        received_results: list[tuple[str, StrategistContext | None]] = []

        async def result_cb(
            task_id: str, context: StrategistContext | None, error: Exception | None
        ) -> None:
            received_results.append((task_id, context))

        bg.set_result_callback(result_cb)

        async def mock_evaluate() -> StrategistContext:
            return StrategistContext(pillar="TRUTH", score=0.88)

        task_id = await bg.submit(pillar="truth", coro=mock_evaluate())
        await bg.wait_for(task_id)

        assert len(received_results) == 1
        assert received_results[0][0] == task_id
        assert received_results[0][1] is not None

    def test_get_status(self, bg: BackgroundStrategist) -> None:
        """상태 조회."""
        status = bg.get_status()

        assert "active_count" in status
        assert "max_concurrent" in status
        assert status["max_concurrent"] == bg.max_concurrent_tasks

    @pytest.mark.asyncio
    async def test_cleanup(self, bg: BackgroundStrategist) -> None:
        """정리."""

        async def slow_evaluate() -> StrategistContext:
            await asyncio.sleep(10.0)
            return StrategistContext(pillar="TRUTH")

        await bg.submit(pillar="truth", coro=slow_evaluate())
        await bg.cleanup()

        assert len(bg.get_active_tasks()) == 0


class TestPreemptiveCompactor:
    """PreemptiveCompactor 테스트."""

    @pytest.fixture
    def compactor(self) -> PreemptiveCompactor:
        """새 PreemptiveCompactor 인스턴스."""
        return PreemptiveCompactor(max_tokens=1000)

    def test_add_message(self, compactor: PreemptiveCompactor) -> None:
        """메시지 추가."""
        compactor.add_message(role="user", content="Hello, world!")

        metrics = compactor.get_metrics()
        assert metrics.message_count == 1
        assert metrics.total_tokens > 0

    def test_add_message_item(self, compactor: PreemptiveCompactor) -> None:
        """MessageItem으로 추가."""
        msg = MessageItem(role="assistant", content="Hi there!", priority=3)
        compactor.add_message(msg)

        metrics = compactor.get_metrics()
        assert metrics.message_count == 1

    def test_metrics_calculation(self, compactor: PreemptiveCompactor) -> None:
        """메트릭 계산."""
        # 충분한 양의 메시지 추가
        for i in range(10):
            compactor.add_message(role="user", content=f"Message {i}" * 10)

        metrics = compactor.get_metrics()

        assert metrics.total_tokens > 0
        assert 0 <= metrics.usage_ratio <= 1
        assert metrics.message_count == 10

    @pytest.mark.asyncio
    async def test_compress_trim_old(self, compactor: PreemptiveCompactor) -> None:
        """오래된 메시지 제거 압축."""
        # 메시지 추가
        for i in range(10):
            compactor.add_message(role="user", content=f"Message {i}")

        before_count = compactor.get_metrics().message_count

        result = await compactor.compress(
            strategy=CompressionStrategy.TRIM_OLD,
            level=CompressionLevel.MODERATE,
            save_snapshot=False,
        )

        assert result.success is True
        assert result.messages_removed > 0
        assert compactor.get_metrics().message_count < before_count

    @pytest.mark.asyncio
    async def test_compress_deduplicate(self, compactor: PreemptiveCompactor) -> None:
        """중복 제거 압축."""
        # 중복 메시지 추가
        for _ in range(5):
            compactor.add_message(role="user", content="Same message")
            compactor.add_message(role="user", content="Different message")

        result = await compactor.compress(
            strategy=CompressionStrategy.DEDUPLICATE,
            save_snapshot=False,
        )

        assert result.success is True
        assert result.messages_removed >= 4  # 최소 4개 중복 제거

    @pytest.mark.asyncio
    async def test_compress_hybrid(self, compactor: PreemptiveCompactor) -> None:
        """복합 압축."""
        for i in range(20):
            compactor.add_message(role="user", content=f"Message {i % 5}")  # 일부 중복

        result = await compactor.compress(
            strategy=CompressionStrategy.HYBRID,
            level=CompressionLevel.AGGRESSIVE,
            save_snapshot=False,
        )

        assert result.success is True
        assert result.compression_ratio > 0

    @pytest.mark.asyncio
    async def test_compress_with_snapshot(self, compactor: PreemptiveCompactor) -> None:
        """스냅샷 저장과 함께 압축."""
        for i in range(10):
            compactor.add_message(role="user", content=f"Message {i}")

        result = await compactor.compress(save_snapshot=True)

        assert result.success is True
        assert result.snapshot_id is not None

    @pytest.mark.asyncio
    async def test_restore_from_snapshot(self, compactor: PreemptiveCompactor) -> None:
        """스냅샷에서 복원."""
        # 메시지 추가
        for i in range(5):
            compactor.add_message(role="user", content=f"Original {i}")

        # 압축 (스냅샷 저장)
        result = await compactor.compress(level=CompressionLevel.AGGRESSIVE, save_snapshot=True)
        assert result.snapshot_id is not None

        # 복원
        restored = await compactor.restore_from_snapshot(result.snapshot_id)
        assert restored is True

        # 원본 메시지 수 확인
        assert compactor.get_metrics().message_count == 5

    def test_should_compress(self, compactor: PreemptiveCompactor) -> None:
        """압축 필요 여부."""
        compactor.compression_threshold = 0.5  # 50%로 낮춤
        # max_tokens=1000, 50% = 500 tokens 필요
        # 각 메시지당 약 100 토큰 (300자 / 3)

        # 500+ 토큰 채우기
        for _ in range(10):
            compactor.add_message(role="user", content="X" * 150)  # ~50 tokens each

        assert compactor.should_compress() is True

    def test_should_warn(self, compactor: PreemptiveCompactor) -> None:
        """경고 필요 여부."""
        compactor.warning_threshold = 0.3  # 30%로 낮춤
        # max_tokens=1000, 30% = 300 tokens 필요

        # 300+ 토큰 채우기
        for _ in range(6):
            compactor.add_message(role="user", content="X" * 150)  # ~50 tokens each

        assert compactor.should_warn() is True

    def test_priority_preserved_on_system_messages(self, compactor: PreemptiveCompactor) -> None:
        """시스템 메시지 우선순위 보존."""
        compactor.add_message(role="system", content="System prompt")
        compactor.add_message(role="user", content="User message")

        msgs = compactor.get_messages()
        system_msg = next(m for m in msgs if m.role == "system")

        assert system_msg.priority == 1  # 최우선

    def test_get_compression_history(self, compactor: PreemptiveCompactor) -> None:
        """압축 히스토리."""
        # 초기 히스토리는 비어있음
        history = compactor.get_compression_history()
        assert len(history) == 0

    def test_clear(self, compactor: PreemptiveCompactor) -> None:
        """메시지 전체 삭제."""
        compactor.add_message(role="user", content="Test")
        compactor.clear()

        assert compactor.get_metrics().message_count == 0

    def test_get_status(self, compactor: PreemptiveCompactor) -> None:
        """상태 조회."""
        status = compactor.get_status()

        assert "metrics" in status
        assert "should_warn" in status
        assert "should_compress" in status
        assert "auto_compress" in status


class TestBackgroundTask:
    """BackgroundTask 테스트."""

    def test_to_dict(self) -> None:
        """딕셔너리 변환."""
        task = BackgroundTask(pillar="truth", state=TaskState.RUNNING)
        data = task.to_dict()

        assert data["pillar"] == "truth"
        assert data["state"] == "running"
        assert "task_id" in data

    def test_is_done(self) -> None:
        """완료 여부."""
        task = BackgroundTask(state=TaskState.RUNNING)
        assert task.is_done is False

        task.state = TaskState.COMPLETED
        assert task.is_done is True

        task.state = TaskState.FAILED
        assert task.is_done is True


class TestContextMetrics:
    """ContextMetrics 테스트."""

    def test_usage_ratio(self) -> None:
        """사용률 계산."""
        metrics = ContextMetrics(total_tokens=50000, max_tokens=100000)
        assert metrics.usage_ratio == 0.5
        assert metrics.usage_percent == 50.0

    def test_to_dict(self) -> None:
        """딕셔너리 변환."""
        metrics = ContextMetrics(total_tokens=1000, max_tokens=10000)
        data = metrics.to_dict()

        assert data["total_tokens"] == 1000
        assert data["usage_ratio"] == 0.1


class TestMessageItem:
    """MessageItem 테스트."""

    def test_content_hash(self) -> None:
        """콘텐츠 해시."""
        msg1 = MessageItem(role="user", content="Hello")
        msg2 = MessageItem(role="user", content="Hello")
        msg3 = MessageItem(role="user", content="World")

        assert msg1.content_hash == msg2.content_hash
        assert msg1.content_hash != msg3.content_hash

    def test_age_seconds(self) -> None:
        """메시지 나이."""
        msg = MessageItem(role="user", content="Test", timestamp=time.time() - 10)
        assert msg.age_seconds >= 10


class TestSingletons:
    """싱글톤 테스트."""

    def test_background_strategist_singleton(self) -> None:
        """BackgroundStrategist 싱글톤."""
        bg1 = get_background_strategist()
        bg2 = get_background_strategist()
        assert bg1 is bg2

    def test_compactor_singleton(self) -> None:
        """PreemptiveCompactor 싱글톤."""
        c1 = get_preemptive_compactor()
        c2 = get_preemptive_compactor()
        assert c1 is c2


@pytest.mark.smoke
class TestPhase3Smoke:
    """스모크 테스트."""

    def test_background_strategist_instantiates(self) -> None:
        """BackgroundStrategist 인스턴스화."""
        bg = BackgroundStrategist()
        assert bg is not None

    def test_compactor_instantiates(self) -> None:
        """PreemptiveCompactor 인스턴스화."""
        compactor = PreemptiveCompactor()
        assert compactor is not None

    @pytest.mark.asyncio
    async def test_background_basic_flow(self) -> None:
        """BackgroundStrategist 기본 흐름."""
        bg = BackgroundStrategist()

        async def quick_task() -> StrategistContext:
            return StrategistContext(pillar="TRUTH")

        task_id = await bg.submit(pillar="truth", coro=quick_task())
        result = await bg.wait_for(task_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_compactor_basic_flow(self) -> None:
        """PreemptiveCompactor 기본 흐름."""
        compactor = PreemptiveCompactor()

        compactor.add_message(role="user", content="Test message")
        metrics = compactor.get_metrics()

        assert metrics.message_count == 1
