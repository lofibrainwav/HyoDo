import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from AFO.trinity_score_sharing.collaboration_analysis import (
    analyze_score_distribution,
    calculate_variance,
)
from AFO.trinity_score_sharing.models import CollaborationMetrics
from AFO.trinity_score_sharing.sharing_system import TrinityScoreSharingSystem


class TestTrinityScoreSharingSystem:
    """Test TrinityScoreSharingSystem class methods."""

    @pytest.fixture
    def system(self) -> None:
        """Create a fresh system for each test."""
        return TrinityScoreSharingSystem()

    def test_initialization(self, system) -> None:
        """System should initialize with empty state."""
        assert system.score_pools == {}
        assert system.score_history == {}
        assert system.collaboration_metrics == {}
        # feedback_tasks moved to feedback_manager
        assert system.feedback_manager.feedback_tasks == {}
        assert system.sharing_stats["total_updates"] == 0
        assert system.sharing_stats["active_pools"] == 0

    def test_get_sharing_stats(self, system) -> None:
        """Should return sharing statistics."""
        stats = system.get_sharing_stats()
        assert "total_updates" in stats
        assert "active_pools" in stats
        assert "active_sessions" in stats
        assert "total_agents" in stats
        assert "total_history_entries" in stats

    def test_calculate_collaboration_impact_single_agent(self, system) -> None:
        """Single agent should have 0 impact."""
        system.score_pools = {"session1": {"agent1": 0.9}}
        impact = system._calculate_collaboration_impact("session1", "agent1", 0.9)
        assert impact == 0.0

    def test_calculate_collaboration_impact_no_session(self, system) -> None:
        """Missing session should return 0.0."""
        impact = system._calculate_collaboration_impact("missing", "agent1", 0.9)
        assert impact == 0.0

    def test_calculate_collaboration_impact_high_alignment(self, system) -> None:
        """High alignment with average should give high impact."""
        system.score_pools = {"session1": {"agent1": 0.8, "agent2": 0.8}}
        impact = system._calculate_collaboration_impact("session1", "agent1", 0.8)
        # avg = 0.8, deviation = 0, impact = 1.0
        assert impact == 1.0

    def test_calculate_collaboration_impact_low_alignment(self, system) -> None:
        """Low alignment with average should give low impact."""
        system.score_pools = {"session1": {"agent1": 0.5, "agent2": 0.9}}
        impact = system._calculate_collaboration_impact("session1", "agent1", 0.5)
        # avg = 0.7, deviation = 0.2, impact = 0.8
        assert impact == 0.8

    def test_analyze_score_distribution_empty(self, system) -> None:
        """Empty scores should return zeros."""
        # Moved to collaboration_analysis.py as standalone function
        result = analyze_score_distribution({})
        assert result["mean"] == 0.0
        assert result["variance"] == 0.0
        assert result["min"] == 0.0
        assert result["max"] == 0.0

    def test_analyze_score_distribution_with_data(self, system) -> None:
        """Should calculate correct distribution."""
        # Moved to collaboration_analysis.py as standalone function
        result = analyze_score_distribution({"a": 0.5, "b": 0.7, "c": 0.9})
        assert abs(result["mean"] - 0.7) < 0.001
        assert result["agent_count"] == 3
        assert result["min"] == 0.5
        assert result["max"] == 0.9

    def test_calculate_variance_empty(self, system) -> None:
        """Empty list should return 0.0."""
        # Moved to collaboration_analysis.py as standalone function
        result = calculate_variance([])
        assert result == 0.0

    def test_calculate_variance_with_values(self, system) -> None:
        """Should calculate correct variance."""
        # Moved to collaboration_analysis.py as standalone function
        result = calculate_variance([1.0, 2.0, 3.0])
        # mean = 2.0, variance = ((-1)^2 + 0 + 1^2)/3 = 2/3
        assert abs(result - 0.667) < 0.01

    def test_calculate_collaboration_intensity_single_agent(self, system) -> None:
        """Single agent should return 0.0."""
        result = system._calculate_collaboration_intensity({"agent1": 0.9})
        assert result == 0.0

    def test_calculate_collaboration_intensity_multiple_agents(self, system) -> None:
        """Multiple agents should calculate based on variance."""
        result = system._calculate_collaboration_intensity(
            {
                "agent1": 0.8,
                "agent2": 0.8,
            }
        )
        # variance = 0, intensity = 1.0
        assert result == 1.0

    def test_calculate_collaborative_adjustment_high_collab(self, system) -> None:
        """High collaboration should give positive adjustment."""
        context = {"collaboration_intensity": 0.9, "diversity_index": 0.1}
        result = system._calculate_collaborative_adjustment(0.8, context, {})
        assert result > 0

    def test_calculate_collaborative_adjustment_low_collab(self, system) -> None:
        """Low collaboration should give negative adjustment."""
        context = {"collaboration_intensity": 0.1, "diversity_index": 0.9}
        result = system._calculate_collaborative_adjustment(0.8, context, {})
        assert result < 0

    def test_calculate_collaborative_adjustment_clamped(self, system) -> None:
        """Adjustment should be clamped to [-0.1, 0.1]."""
        # Very high positive
        context = {"collaboration_intensity": 1.0, "diversity_index": 0.0}
        result = system._calculate_collaborative_adjustment(0.8, context, {})
        assert result <= 0.1

        # Very high negative
        context = {"collaboration_intensity": 0.0, "diversity_index": 10.0}
        result = system._calculate_collaborative_adjustment(0.8, context, {})
        assert result >= -0.1

    def test_generate_adjustment_reason_strong_positive(self, system) -> None:
        """Should generate strong positive reason."""
        # adjustment = 0.9 - 0.8 = +0.1
        result = system._generate_adjustment_reason(0.8, 0.9, {})
        assert "Score increased" in result
        assert "0.100" in result

    def test_generate_adjustment_reason_moderate_positive(self, system) -> None:
        """Should generate moderate positive reason."""
        # adjustment = 0.83 - 0.8 = +0.03
        result = system._generate_adjustment_reason(0.8, 0.83, {})
        assert "Score increased" in result
        assert "0.030" in result

    def test_generate_adjustment_reason_strong_negative(self, system) -> None:
        """Should generate strong negative reason."""
        # adjustment = 0.7 - 0.8 = -0.1
        result = system._generate_adjustment_reason(0.8, 0.7, {})
        assert "Score decreased" in result
        assert "0.100" in result

    def test_generate_adjustment_reason_moderate_negative(self, system) -> None:
        """Should generate moderate negative reason."""
        # adjustment = 0.77 - 0.8 = -0.03
        result = system._generate_adjustment_reason(0.8, 0.77, {})
        assert "Score decreased" in result
        assert "0.030" in result

    def test_generate_adjustment_reason_neutral(self, system) -> None:
        """Should generate neutral reason."""
        # adjustment = 0.0
        result = system._generate_adjustment_reason(0.8, 0.8, {})
        assert "No significant collaboration adjustment needed" in result

    def test_should_optimize_scores_missing_session(self, system) -> None:
        """Missing session should return False."""
        result = system._should_optimize_scores("missing")
        assert result is False

    def test_should_optimize_scores_single_agent(self, system) -> None:
        """Single agent should return False."""
        system.score_pools = {"session1": {"agent1": 0.9}}
        result = system._should_optimize_scores("session1")
        assert result is False

    def test_should_optimize_scores_insufficient_history(self, system) -> None:
        """Insufficient history should return False."""
        system.score_pools = {"session1": {"agent1": 0.9, "agent2": 0.8}}
        system.score_history = {"session1": [MagicMock() for _ in range(4)]}
        result = system._should_optimize_scores("session1")
        assert result is False

    def test_should_optimize_scores_old_history(self, system) -> None:
        """Old history should return False."""
        system.score_pools = {"session1": {"agent1": 0.9, "agent2": 0.8}}
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        system.score_history = {"session1": [MagicMock(timestamp=old_time) for _ in range(5)]}
        result = system._should_optimize_scores("session1")
        assert result is False

    def test_should_optimize_scores_sufficient_recent(self, system) -> None:
        """Sufficient recent history should return True."""
        system.score_pools = {"session1": {"agent1": 0.9, "agent2": 0.8}}
        recent_time = datetime.now() - timedelta(minutes=30)
        system.score_history = {
            "session1": [MagicMock(timestamp=recent_time.isoformat()) for _ in range(5)]
        }
        result = system._should_optimize_scores("session1")
        assert result is True

    def test_get_session_stats_missing_session(self, system) -> None:
        """Missing session should return inactive stats."""
        result = system._get_session_stats("missing")
        assert result["active"] is False

    def test_get_session_stats_active_session(self, system) -> None:
        """Active session should return stats."""
        system.score_pools = {"session1": {"agent1": 0.9, "agent2": 0.7}}
        system.score_history = {"session1": [MagicMock() for _ in range(3)]}
        result = system._get_session_stats("session1")
        assert result["active"] is True
        assert result["agent_count"] == 2
        assert result["total_updates"] == 3
        assert "avg_score" in result
        assert "score_range" in result

    @pytest.mark.asyncio
    async def test_get_optimized_score_missing_session(self, system):
        """Missing session should return 0.0."""
        result = await system._get_optimized_score("missing", "agent1")
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_get_optimized_score_missing_agent(self, system):
        """Missing agent should return 0.0."""
        system.score_pools = {"session1": {"other_agent": 0.9}}
        result = await system._get_optimized_score("session1", "agent1")
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_get_optimized_score_with_adjustment(self, system):
        """Should apply collaborative adjustment."""
        system.score_pools = {"session1": {"agent1": 0.8, "agent2": 0.8}}
        result = await system._get_optimized_score("session1", "agent1")
        # High collaboration = positive adjustment, result should be >= base score
        assert result >= 0.8

    def test_analyze_collaboration_context_empty_factors(self, system) -> None:
        """Should handle empty factors."""
        scores = {"agent1": 0.8}
        result = system._analyze_collaboration_context(scores, "agent1", {})
        assert result["total_agents"] == 1
        assert result["collaboration_intensity"] == 0.0

    def test_analyze_collaboration_context_single_agent(self, system) -> None:
        """Single agent should return single stats."""
        scores = {"agent1": 0.8}
        result = system._analyze_collaboration_context(scores, "agent1", {})
        assert result["total_agents"] == 1
        assert "score_distribution" in result

    def test_analyze_collaboration_context_multiple_agents(self, system) -> None:
        """Multiple agents should calculate stats."""
        scores = {"agent1": 0.5, "agent2": 0.9}
        result = system._analyze_collaboration_context(scores, "agent1", {})
        assert result["total_agents"] == 2
        assert "score_distribution" in result
        assert result["collaboration_intensity"] > 0

    @pytest.mark.asyncio
    async def test_update_collaboration_metrics_missing_session(self, system):
        """Missing session should do nothing."""
        await system._update_collaboration_metrics("missing")
        assert "missing" not in system.collaboration_metrics

    @pytest.mark.asyncio
    async def test_update_collaboration_metrics_creates_metrics(self, system):
        """Should create collaboration metrics."""
        system.score_pools = {"session1": {"agent1": 0.8, "agent2": 0.8}}
        system.score_history = {
            "session1": [
                MagicMock(agent_type="agent1", collaboration_impact=0.9),
                MagicMock(agent_type="agent2", collaboration_impact=0.9),
            ]
        }
        print(f"DEBUG: score_pools keys: {system.score_pools.keys()}")
        await system._update_collaboration_metrics("session1")
        print(f"DEBUG: collaboration_metrics keys: {system.collaboration_metrics.keys()}")
        assert "session1" in system.collaboration_metrics

        metrics = system.collaboration_metrics["session1"]
        assert isinstance(metrics, CollaborationMetrics)
        assert metrics.session_id == "session1"

    def test_get_session_trinity_metrics_missing_session(self, system) -> None:
        """Missing session should return error."""
        result = system.get_session_trinity_metrics("missing")
        assert "error" in result

    def test_get_session_trinity_metrics_active_session(self, system) -> None:
        """Active session should return metrics."""
        system.score_pools = {"session1": {"agent1": 0.8}}
        system.score_history = {
            "session1": [
                MagicMock(
                    agent_type="agent1",
                    new_score=0.8,
                    previous_score=0.7,
                    collaboration_impact=0.9,
                    timestamp=datetime.now().isoformat(),
                )
            ]
        }
        result = system.get_session_trinity_metrics("session1")
        assert result["session_id"] == "session1"
        assert "current_scores" in result
        assert "recent_updates" in result
        assert "collaboration_metrics" in result
        assert "optimization_stats" in result

    @pytest.mark.asyncio
    async def test_start_sharing_system(self, system):
        """Should start feedback cleanup task."""
        await system.start_sharing_system()
        assert "cleanup" in system.feedback_manager.feedback_tasks
        assert not system.feedback_manager.feedback_tasks["cleanup"].done()

    @pytest.mark.asyncio
    async def test_stop_sharing_system(self, system):
        """Should cancel all feedback tasks."""
        await system.start_sharing_system()
        # Capture task reference before stop (stop_all clears the dict)
        cleanup_task = system.feedback_manager.feedback_tasks["cleanup"]
        await system.stop_sharing_system()
        # Task should be cancelled and dict should be cleared
        assert cleanup_task.done()
        assert len(system.feedback_manager.feedback_tasks) == 0

    @pytest.mark.asyncio
    async def test_share_trinity_score_new_session(self, system):
        """Should create new session when sharing."""
        result = await system.share_trinity_score(
            agent_type="agent1",
            session_id="new_session",
            new_score=0.85,
            change_reason="Test update",
            contributing_factors={"truth": 0.9, "goodness": 0.8},
        )
        assert result["success"] is True
        assert result["update_event"] is not None
        assert "new_session" in system.score_pools
        assert "new_session" in system.score_history

    @pytest.mark.asyncio
    async def test_share_trinity_score_existing_session(self, system):
        """Should update existing session."""
        # First share
        await system.share_trinity_score(
            agent_type="agent1",
            session_id="session1",
            new_score=0.8,
            change_reason="First",
            contributing_factors={},
        )
        # Second share
        result = await system.share_trinity_score(
            agent_type="agent1",
            session_id="session1",
            new_score=0.9,
            change_reason="Update",
            contributing_factors={},
        )
        assert result["success"] is True
        assert system.score_pools["session1"]["agent1"] == 0.9
        assert len(system.score_history["session1"]) == 2

    @pytest.mark.asyncio
    async def test_get_collaborative_trinity_score_missing_session(self, system):
        """Missing session should return error."""
        result = await system.get_collaborative_trinity_score(
            session_id="missing",
            agent_type="agent1",
        )
        assert result["score"] == 0.0
        assert "Session not found" in result["reason"]

    @pytest.mark.asyncio
    async def test_get_collaborative_trinity_score_missing_agent(self, system):
        """Missing agent should return error."""
        system.score_pools = {"session1": {"other": 0.9}}
        result = await system.get_collaborative_trinity_score(
            session_id="session1",
            agent_type="agent1",
        )
        assert result["score"] == 0.0
        assert "Agent not found" in result["reason"]

    @pytest.mark.asyncio
    async def test_get_collaborative_trinity_score_base_only(self, system):
        """Should return base score when optimization disabled."""
        system.score_pools = {"session1": {"agent1": 0.85}}
        result = await system.get_collaborative_trinity_score(
            session_id="session1",
            agent_type="agent1",
            include_optimization=False,
        )
        assert result["score"] == 0.85
        assert result["reason"] == "Base score only"

    @pytest.mark.asyncio
    async def test_get_collaborative_trinity_score_with_optimization(self, system):
        """Should apply optimization when enabled."""
        system.score_pools = {"session1": {"agent1": 0.8, "agent2": 0.8}}
        result = await system.get_collaborative_trinity_score(
            session_id="session1",
            agent_type="agent1",
            include_optimization=True,
        )
        assert result["score"] == 0.8  # Base score
        assert "optimization_delta" in result
        assert (
            "due to" in result["reason"] or result["reason"] == "Collaborative optimization applied"
        )

    @pytest.mark.asyncio
    async def test_synchronize_session_scores_missing_session(self, system):
        """Missing session should return error."""
        result = await system.synchronize_session_scores("missing")
        assert result["success"] is False
        assert "Session not found" in result["reason"]

    @pytest.mark.asyncio
    async def test_synchronize_session_scores_success(self, system):
        """Should synchronize session scores."""
        system.score_pools = {"session1": {"agent1": 0.8}}
        result = await system.synchronize_session_scores("session1")
        assert result["success"] is True
        assert result["session_id"] == "session1"
        assert "sync_analysis" in result
        assert "collaboration_metrics" in result

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="_cleanup_expired_feedback_loops moved to FeedbackLoopManager (test_feedback.py)"
    )
    async def test_cleanup_feedback_tasks_deletes_completed(self, system):
        """Should delete completed tasks (line 462)."""
        system.cleanup_interval = 0.01
        # Create a completed task
        completed_task = asyncio.create_task(asyncio.sleep(0))
        await asyncio.sleep(0.01)  # Ensure task completes

        system.feedback_tasks = {"completed": completed_task}
        system.sharing_stats = {"feedback_loops_active": 1}

        # Run cleanup once and cancel
        cleanup_task = asyncio.create_task(system._cleanup_expired_feedback_loops())
        await asyncio.sleep(0.05)
        cleanup_task.cancel()

        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        # The completed task should be deleted
        assert "completed" not in system.feedback_tasks

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="_cleanup_expired_feedback_loops moved to FeedbackLoopManager (test_feedback.py)"
    )
    async def test_cleanup_feedback_tasks_exception_path(self, system):
        """Should handle exceptions gracefully (lines 472-474).

        This test triggers the exception path in _cleanup_expired_feedback_loops
        by having a task that raises when .done() is called.
        """

        # Create a task that raises exception when .done() is called
        class ExceptionRaisingTask:
            def done(self) -> None:
                raise RuntimeError("Simulated task error in sharing system")

            def cancel(self) -> None:
                pass

        system.feedback_tasks = {"bad_task": ExceptionRaisingTask()}
        system.sharing_stats = {"feedback_loops_active": 1}

        # Run the actual cleanup method
        cleanup_task = asyncio.create_task(system._cleanup_expired_feedback_loops())
        # Let it run one iteration and hit the exception
        await asyncio.sleep(0.15)
        cleanup_task.cancel()

        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        # Should handle exception gracefully without crashing
        assert True
