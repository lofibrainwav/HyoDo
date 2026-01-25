import pytest
from pydantic import ValidationError
from services.trinity_calculator import trinity_calculator

from AFO.domain.metrics.trinity import TrinityInputs, TrinityMetrics


class TestTrinityEngine:
    """Test suite for Trinity Engine (Pydantic Upgrade)"""

    def test_trinity_inputs_auto_clamping(self) -> None:
        """Verify that TrinityInputs auto-clamps out-of-bounds values (Goodness/Serenity)"""
        # Over-bounds
        inputs = TrinityInputs(truth=1.5, goodness=2.0, beauty=100.0, filial_serenity=5.0)
        assert inputs.truth == 1.0
        assert inputs.goodness == 1.0
        assert inputs.beauty == 1.0
        assert inputs.filial_serenity == 1.0

        # Under-bounds
        inputs_neg = TrinityInputs(truth=-1.0, goodness=-0.5, beauty=-0.0, filial_serenity=-10.0)
        assert inputs_neg.truth == 0.0
        assert inputs_neg.goodness == 0.0
        assert inputs_neg.beauty == 0.0
        assert inputs_neg.filial_serenity == 0.0

        # Mixed types (should convert)
        inputs_str = TrinityInputs(truth="0.9", goodness=0.8, beauty="1.0", filial_serenity=0)
        assert inputs_str.truth == 0.9
        assert inputs_str.beauty == 1.0

    def test_trinity_calculator_integration(self) -> None:
        """Verify TrinityCalculator uses TrinityInputs for validation"""
        # Mock data that would produce >1.0 without validation if logic was naive
        # But here we just check if it returns valid 0-1 range.

        # Test valid case
        scores = trinity_calculator.calculate_raw_scores({"valid_structure": True})
        assert len(scores) == 5
        assert all(0.0 <= s <= 1.0 for s in scores)

        # Test invalid case (Truth=0)
        scores_bad = trinity_calculator.calculate_raw_scores({"valid_structure": False})
        assert scores_bad[0] == 0.0

    def test_trinity_metrics_calculation(self) -> None:
        """Verify TrinityMetrics calculation logic"""
        inputs = TrinityInputs(truth=1.0, goodness=1.0, beauty=1.0, filial_serenity=1.0)
        metrics = TrinityMetrics.from_inputs(inputs, eternity=1.0)

        assert metrics.trinity_score == pytest.approx(1.0)
        assert metrics.balance_status == "balanced"

        metrics_100 = metrics.to_100_scale()
        assert metrics_100.trinity_score == pytest.approx(100.0)
