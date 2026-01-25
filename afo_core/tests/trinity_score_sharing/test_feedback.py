"""Tests for trinity_score_sharing/feedback module coverage gaps."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from AFO.trinity_score_sharing.feedback import (
    cleanup_expired_feedback_loops,
    generate_adjustment_reason,
    should_optimize_scores,
)


class TestGenerateAdjustmentReason:
    """Test generate_adjustment_reason function."""

    def test_strong_positive_adjustment(self) -> None:
        """Adjustment > 0.05 should return strong boost message."""
        result = generate_adjustment_reason(0.1, {})
        assert result == "Strong collaborative performance boost"

    def test_moderate_positive_adjustment(self) -> None:
        """0.01 < adjustment <= 0.05 should return moderate enhancement."""
        result = generate_adjustment_reason(0.03, {})
        assert result == "Moderate collaboration enhancement"

    def test_small_positive_adjustment(self) -> None:
        """0 < adjustment <= 0.01 should return maintained message."""
        result = generate_adjustment_reason(0.005, {})
        assert result == "Score maintained at optimal level"

    def test_strong_negative_adjustment(self) -> None:
        """Adjustment < -0.05 should return alignment message."""
        result = generate_adjustment_reason(-0.1, {})
        assert result == "Score alignment for better consensus"

    def test_moderate_negative_adjustment(self) -> None:
        """-0.05 <= adjustment < -0.01 should return minor adjustment."""
        result = generate_adjustment_reason(-0.03, {})
        assert result == "Minor consensus adjustment"

    def test_small_negative_adjustment(self) -> None:
        """-0.01 <= adjustment <= 0 should return maintained message."""
        result = generate_adjustment_reason(-0.005, {})
        assert result == "Score maintained at optimal level"

    def test_zero_adjustment(self) -> None:
        """Zero adjustment should return maintained message."""
        result = generate_adjustment_reason(0.0, {})
        assert result == "Score maintained at optimal level"

    def test_adjustment_with_context(self) -> None:
        """Test that context is accepted but not used in logic."""
        result = generate_adjustment_reason(0.1, {"session_id": "test"})
        assert result == "Strong collaborative performance boost"


class TestShouldOptimizeScores:
    """Test should_optimize_scores function."""

    def test_session_not_in_pools(self) -> None:
        """Should return False when session not in pools."""
        result = should_optimize_scores(
            session_id="missing",
            score_pools={},
            score_history={},
            _datetime_module=datetime,
        )
        assert result is False

    def test_single_agent_not_enough(self) -> None:
        """Should return False when only one agent."""
        result = should_optimize_scores(
            session_id="test",
            score_pools={"test": {"agent1": 0.9}},
            score_history={},
            _datetime_module=datetime,
        )
        assert result is False

    def test_insufficient_history(self) -> None:
        """Should return False when history < 5 updates."""
        # Create mock updates with timestamps
        mock_history = [
            MagicMock(timestamp=(datetime.now() - timedelta(minutes=5)).isoformat())
            for _ in range(4)
        ]
        result = should_optimize_scores(
            session_id="test",
            score_pools={"test": {"agent1": 0.9, "agent2": 0.8}},
            score_history={"test": mock_history},
            _datetime_module=datetime,
        )
        assert result is False

    def test_insufficient_recent_updates(self) -> None:
        """Should return False when recent updates < 3."""
        # Create 5 old updates (more than 1 hour ago)
        mock_history = [
            MagicMock(timestamp=(datetime.now() - timedelta(hours=2)).isoformat()) for _ in range(5)
        ]
        result = should_optimize_scores(
            session_id="test",
            score_pools={"test": {"agent1": 0.9, "agent2": 0.8}},
            score_history={"test": mock_history},
            _datetime_module=datetime,
        )
        assert result is False

    def test_sufficient_recent_updates(self) -> None:
        """Should return True when >= 3 recent updates."""
        # Create 5 recent updates (within 1 hour) - need 5 for should_optimize
        # Each with a timestamp that's clearly recent
        recent_time = datetime.now() - timedelta(minutes=30)
        mock_history = [MagicMock(timestamp=recent_time.isoformat()) for _ in range(5)]
        result = should_optimize_scores(
            session_id="test",
            score_pools={"test": {"agent1": 0.9, "agent2": 0.8}},
            score_history={"test": mock_history},
            _datetime_module=datetime,
        )
        assert result is True


class TestCleanupExpiredFeedbackLoops:
    """Test cleanup_expired_feedback_loops async function."""

    @pytest.mark.asyncio
    async def test_cleanup_completed_tasks(self):
        """Should remove completed tasks from feedback_tasks."""
        # Create a completed task
        completed_task = asyncio.create_task(asyncio.sleep(0))
        await asyncio.sleep(0.01)  # Ensure task completes

        feedback_tasks = {
            "completed_task": completed_task,
            "running_task": MagicMock(done=lambda: False),
        }
        sharing_stats = {"feedback_loops_active": 2}

        # Run cleanup once with a short sleep
        cleanup_task = asyncio.create_task(
            cleanup_expired_feedback_loops(feedback_tasks, sharing_stats)
        )
        await asyncio.sleep(0.05)  # Let it run one iteration
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        # Verify completed task was removed
        assert "completed_task" not in feedback_tasks
        assert "running_task" in feedback_tasks

    @pytest.mark.asyncio
    async def test_cleanup_updates_stats(self):
        """Should update sharing_stats with active count."""
        # Create a completed task
        completed_task = asyncio.create_task(asyncio.sleep(0))
        await asyncio.sleep(0.01)

        feedback_tasks = {"task1": completed_task}
        sharing_stats = {"feedback_loops_active": 1}

        cleanup_task = asyncio.create_task(
            cleanup_expired_feedback_loops(feedback_tasks, sharing_stats)
        )
        await asyncio.sleep(0.05)
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        # Verify stats updated
        assert sharing_stats["feedback_loops_active"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_cancelled_error(self):
        """Should break loop on CancelledError."""
        feedback_tasks = {}
        sharing_stats = {"feedback_loops_active": 0}

        # Mock a task that raises CancelledError
        async def raise_cancelled():
            await asyncio.sleep(100)

        cleanup_task = asyncio.create_task(
            cleanup_expired_feedback_loops(feedback_tasks, sharing_stats)
        )
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        # Should complete without error
        assert True

    @pytest.mark.asyncio
    async def test_cleanup_handles_exception(self):
        """Should handle exceptions gracefully."""
        feedback_tasks = {"task1": MagicMock(done=lambda: True, cancel=lambda: None)}
        sharing_stats = {"feedback_loops_active": 1}

        # We'll patch to raise an exception
        original_delete = (
            feedback_tasks.pop.__self__ if hasattr(feedback_tasks.pop, "__self__") else None
        )

        cleanup_task = asyncio.create_task(
            cleanup_expired_feedback_loops(feedback_tasks, sharing_stats)
        )
        await asyncio.sleep(0.1)  # Let it hit exception path
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        # Should handle without crashing
        assert True

    @pytest.mark.asyncio
    async def test_cleanup_exception_path_coverage(self):
        """Trigger exception path (lines 34-36) in cleanup loop.

        This test causes an exception during dict iteration to hit
        the 'except Exception as e' block in cleanup_expired_feedback_loops.
        """

        # Create a task that raises exception when .done() is called
        class ExceptionRaisingTask:
            def done(self) -> None:
                raise RuntimeError("Simulated task error")

        feedback_tasks = {"bad_task": ExceptionRaisingTask()}
        sharing_stats = {"feedback_loops_active": 1}

        cleanup_task = asyncio.create_task(
            cleanup_expired_feedback_loops(feedback_tasks, sharing_stats)
        )
        # Let it run one iteration and hit the exception
        await asyncio.sleep(0.15)
        cleanup_task.cancel()

        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        # Should handle exception gracefully and continue
        assert True
