"""Tests for trinity_score_sharing/metrics module coverage gaps."""

import pytest

from AFO.trinity_score_sharing.metrics import (
    analyze_collaboration_context,
    analyze_score_distribution,
    calculate_collaboration_intensity,
    calculate_collaborative_adjustment,
    calculate_variance,
)


class TestCalculateVariance:
    """Test calculate_variance function."""

    def test_empty_list(self) -> None:
        """Empty list should return 0.0."""
        result = calculate_variance([])
        assert result == 0.0

    def test_single_value(self) -> None:
        """Single value should return 0.0 variance."""
        result = calculate_variance([5.0])
        assert result == 0.0

    def test_identical_values(self) -> None:
        """Identical values should return 0.0 variance."""
        result = calculate_variance([3.0, 3.0, 3.0])
        assert result == 0.0

    def test_mixed_values(self) -> None:
        """Mixed values should return correct variance."""
        # [1, 2, 3, 4, 5] has variance of 2.0
        result = calculate_variance([1.0, 2.0, 3.0, 4.0, 5.0])
        assert abs(result - 2.0) < 0.001

    def test_negative_values(self) -> None:
        """Should handle negative values correctly."""
        result = calculate_variance([-2.0, -1.0, 0.0, 1.0, 2.0])
        # Same distribution as [1,2,3,4,5] shifted by -3
        assert abs(result - 2.0) < 0.001

    def test_high_variance(self) -> None:
        """Should correctly identify high variance."""
        # Wide spread = high variance
        result = calculate_variance([0.0, 10.0])
        assert result == 25.0


class TestCalculateCollaborationIntensity:
    """Test calculate_collaboration_intensity function."""

    def test_empty_scores(self) -> None:
        """Empty dict should return 0.0."""
        result = calculate_collaboration_intensity({})
        assert result == 0.0

    def test_single_agent(self) -> None:
        """Single agent should return 0.0."""
        result = calculate_collaboration_intensity({"agent1": 0.9})
        assert result == 0.0

    def test_identical_scores(self) -> None:
        """Identical scores should return high intensity (1.0 - 0 = 1.0)."""
        result = calculate_collaboration_intensity(
            {
                "agent1": 0.8,
                "agent2": 0.8,
                "agent3": 0.8,
            }
        )
        assert result == 1.0

    def test_similar_scores(self) -> None:
        """Similar scores should return high intensity."""
        result = calculate_collaboration_intensity(
            {
                "agent1": 0.80,
                "agent2": 0.81,
                "agent3": 0.79,
            }
        )
        assert result > 0.9

    def test_different_scores(self) -> None:
        """Different scores should return lower intensity."""
        result = calculate_collaboration_intensity(
            {
                "agent1": 0.1,
                "agent2": 0.9,
            }
        )
        # Variance = 0.16, so intensity = 1 - 0.16 = 0.84
        assert result == 0.84

    def test_very_different_scores(self) -> None:
        """Very different scores should return low intensity."""
        result = calculate_collaboration_intensity(
            {
                "agent1": 0.0,
                "agent2": 1.0,
            }
        )
        # Variance = 0.25, so intensity = 1 - 0.25 = 0.75
        assert result == 0.75

    def test_intensity_clamped_to_zero(self) -> None:
        """Should not return negative intensity."""
        # Very high variance (max is 0.25 for [0,1])
        result = calculate_collaboration_intensity(
            {
                "agent1": 0.0,
                "agent2": 1.0,
            }
        )
        assert result >= 0.0


class TestAnalyzeScoreDistribution:
    """Test analyze_score_distribution function."""

    def test_empty_scores(self) -> None:
        """Empty dict should return zeros."""
        result = analyze_score_distribution({})
        assert result["mean"] == 0.0
        assert result["variance"] == 0.0
        assert result["min"] == 0.0
        assert result["max"] == 0.0

    def test_single_score(self) -> None:
        """Single score should return that score for mean/min/max."""
        result = analyze_score_distribution({"agent1": 0.75})
        assert result["mean"] == 0.75
        assert result["variance"] == 0.0
        assert result["min"] == 0.75
        assert result["max"] == 0.75
        assert result["range"] == 0.0
        assert result["agent_count"] == 1

    def test_multiple_scores(self) -> None:
        """Should calculate correct statistics."""
        result = analyze_score_distribution(
            {
                "agent1": 0.5,
                "agent2": 0.7,
                "agent3": 0.9,
            }
        )
        assert abs(result["mean"] - 0.7) < 0.001
        assert result["min"] == 0.5
        assert result["max"] == 0.9
        assert result["range"] == 0.4
        assert result["agent_count"] == 3

    def test_variance_calculation(self) -> None:
        """Should calculate correct variance."""
        # [0.5, 0.7, 0.9] has mean 0.7, variance = ((-0.2)^2 + 0^2 + 0.2^2)/3 = 0.0267
        result = analyze_score_distribution(
            {
                "agent1": 0.5,
                "agent2": 0.7,
                "agent3": 0.9,
            }
        )
        assert abs(result["variance"] - 0.0267) < 0.001


class TestAnalyzeCollaborationContext:
    """Test analyze_collaboration_context function."""

    def test_empty_scores(self) -> None:
        """Empty scores should return zeros."""
        result = analyze_collaboration_context({}, 10)
        assert result["collaboration_level"] == 0.0
        assert result["diversity_index"] == 0.0

    def test_short_history(self) -> None:
        """Short history should return low collaboration level."""
        result = analyze_collaboration_context(
            {"agent1": 0.8, "agent2": 0.7},
            5,  # Less than 20
        )
        # collaboration_level = 5/20 = 0.25
        assert abs(result["collaboration_level"] - 0.25) < 0.001
        assert result["update_count"] == 5

    def test_long_history(self) -> None:
        """Long history should return high collaboration level (capped at 1.0)."""
        result = analyze_collaboration_context(
            {"agent1": 0.8, "agent2": 0.7},
            30,  # More than 20
        )
        # collaboration_level = min(1.0, 30/20) = 1.0
        assert result["collaboration_level"] == 1.0

    def test_single_agent_diversity(self) -> None:
        """Single agent should return 0 diversity index."""
        result = analyze_collaboration_context({"agent1": 0.8}, 10)
        assert result["diversity_index"] == 0.0
        assert result["agent_count"] == 1

    def test_multiple_agents_diversity(self) -> None:
        """Multiple agents should return calculated diversity index."""
        result = analyze_collaboration_context(
            {"agent1": 0.5, "agent2": 0.9},
            10,
        )
        # mean = (0.5 + 0.9) / 2 = 0.7
        # variance = ((0.5-0.7)^2 + (0.9-0.7)^2) / 2 = (0.04 + 0.04) / 2 = 0.04
        # diversity_index = min(1.0, 0.04 * 10) = 0.4
        assert abs(result["diversity_index"] - 0.4) < 0.001

    def test_diversity_clamped_to_one(self) -> None:
        """Very high variance should clamp diversity to 1.0."""
        result = analyze_collaboration_context(
            {"agent1": 0.0, "agent2": 1.0},
            10,
        )
        # variance = 0.25, diversity = min(1.0, 0.25 * 10) = 1.0
        assert result["diversity_index"] == 1.0


class TestCalculateCollaborativeAdjustment:
    """Test calculate_collaborative_adjustment function."""

    def test_zero_context(self) -> None:
        """Zero context should return 0.0."""
        result = calculate_collaborative_adjustment(0.8, {})
        assert result == 0.0

    def test_high_collaboration_low_diversity(self) -> None:
        """High collaboration, low diversity should give positive adjustment."""
        context = {
            "collaboration_intensity": 0.9,
            "diversity_index": 0.1,
        }
        result = calculate_collaborative_adjustment(0.8, context)
        # (0.9 * 0.1) - (0.1 * 0.05) = 0.09 - 0.005 = 0.085
        assert result > 0

    def test_low_collaboration_high_diversity(self) -> None:
        """Low collaboration, high diversity should give negative adjustment."""
        context = {
            "collaboration_intensity": 0.1,
            "diversity_index": 0.9,
        }
        result = calculate_collaborative_adjustment(0.8, context)
        # (0.1 * 0.1) - (0.9 * 0.05) = 0.01 - 0.045 = -0.035
        assert result < 0

    def test_adjustment_clamped_positive(self) -> None:
        """Positive adjustment should be clamped to 0.1."""
        context = {
            "collaboration_intensity": 1.0,
            "diversity_index": 0.0,
        }
        result = calculate_collaborative_adjustment(0.8, context)
        # (1.0 * 0.1) - (0.0 * 0.05) = 0.1 (exactly at limit)
        assert abs(result - 0.1) < 0.001

    def test_adjustment_clamped_negative(self) -> None:
        """Negative adjustment should be clamped to -0.1."""
        context = {
            "collaboration_intensity": 0.0,
            "diversity_index": 1.0,
        }
        result = calculate_collaborative_adjustment(0.8, context)
        # (0.0 * 0.1) - (1.0 * 0.05) = -0.05 (not at limit)
        # Let's try more extreme
        context = {
            "collaboration_intensity": 0.0,
            "diversity_index": 5.0,  # Won't happen in practice
        }
        result = calculate_collaborative_adjustment(0.8, context)
        # Clamped to -0.1
        assert abs(result - (-0.1)) < 0.001

    def test_base_score_not_used(self) -> None:
        """Base score is not used in adjustment calculation."""
        context = {"collaboration_intensity": 0.5, "diversity_index": 0.5}
        result1 = calculate_collaborative_adjustment(0.1, context)
        result2 = calculate_collaborative_adjustment(0.9, context)
        # Should be the same
        assert result1 == result2
