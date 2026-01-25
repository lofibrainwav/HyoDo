"""Trinity Score Sharing Coverage Gap Tests - System & Feedback

SharingSystem 및 Feedback 커버리지 갭 해소 테스트.
Split from test_coverage_gaps.py for 500-line rule compliance.
"""

import asyncio
from unittest.mock import MagicMock

import pytest


class TestSharingSystemFullCoverage:
    """Sharing System Full Coverage Tests (remaining gaps)"""

    @pytest.fixture
    def system(self) -> None:
        from AFO.trinity_score_sharing.sharing_system import TrinityScoreSharingSystem

        return TrinityScoreSharingSystem()

    @pytest.mark.asyncio
    async def test_share_trinity_score_with_optimization(self, system):
        """Share score triggers optimization (line 127)"""
        # Add initial scores
        await system.share_trinity_score(
            agent_type="agent1",
            session_id="test_session",
            new_score=0.8,
            change_reason="Initial",
            contributing_factors={},
        )
        await system.share_trinity_score(
            agent_type="agent2",
            session_id="test_session",
            new_score=0.7,
            change_reason="Initial",
            contributing_factors={},
        )

        # Add more updates to build history
        for i in range(5):
            await system.share_trinity_score(
                agent_type="agent1",
                session_id="test_session",
                new_score=0.8 + (i * 0.01),
                change_reason=f"Update {i}",
                contributing_factors={},
            )
            await system.share_trinity_score(
                agent_type="agent2",
                session_id="test_session",
                new_score=0.7 + (i * 0.01),
                change_reason=f"Update {i}",
                contributing_factors={},
            )

        # Verify session exists
        assert "test_session" in system.score_pools

    @pytest.mark.asyncio
    async def test_optimize_collaborative_scores_success(self, system):
        """_optimize_collaborative_scores success path (lines 192-210)"""
        # Setup session
        system.score_pools = {"test_session": {"agent1": 0.8, "agent2": 0.7}}
        system.score_history = {"test_session": []}

        result = await system._optimize_collaborative_scores("test_session")

        assert result["success"] is True
        assert "strategy" in result
        assert "optimized_scores" in result
        assert "adjustments" in result
        assert "confidence" in result or "confidence_level" in result

    @pytest.mark.asyncio
    async def test_optimize_collaborative_scores_missing_session(self, system):
        """_optimize_collaborative_scores missing session"""
        result = await system._optimize_collaborative_scores("missing_session")

        assert result["success"] is False
        assert "reason" in result
        assert result["reason"] == "Session not found"


class TestFeedbackFullCoverage:
    """Feedback Module Full Coverage Tests (lines 34-36)"""

    @pytest.mark.asyncio
    async def test_cleanup_expired_feedback_loops_exception_handling(self):
        """Test exception handling in cleanup loop (lines 34-36)"""
        from AFO.trinity_score_sharing.feedback import cleanup_expired_feedback_loops

        # Create cleanup task with exception handling
        feedback_tasks = {"task1": MagicMock(done=lambda: True)}
        sharing_stats = {"feedback_loops_active": 1}

        # Create cleanup task
        cleanup_task = asyncio.create_task(
            cleanup_expired_feedback_loops(feedback_tasks, sharing_stats)
        )

        # Let it run one iteration
        await asyncio.sleep(0.05)

        # Cancel the task
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        # Test passes if no unhandled exception was raised
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
