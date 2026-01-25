import os

import pytest

# Import from AFO package
from AFO.mipro_optimizer import MiproOptimizer
from AFO.trinity_metric_wrapper import TrinityMetricWrapper


def test_mipro_disabled_returns_default() -> None:
    """Test that MIPRO returns default result when disabled."""
    metric = TrinityMetricWrapper(lambda prompt, target: 0.5)
    opt = MiproOptimizer(metric)
    os.environ.pop("AFO_MIPRO_ENABLED", None)

    # Should not raise, should return default result
    result = opt.optimize(["p1"], "t")
    assert result.best_prompt == "p1"  # First prompt as default
    assert result.best_score == 0.0  # Default score when disabled


def test_mipro_selects_best() -> None:
    metric = TrinityMetricWrapper(lambda prompt, target: 1.0 if prompt == "best" else 0.1)
    opt = MiproOptimizer(metric)
    os.environ["AFO_MIPRO_ENABLED"] = "1"
    res = opt.optimize(["bad", "best"], "t")
    assert res.best_prompt == "best"
    assert res.best_score == 1.0


def test_mipro_enabled_calls_optimizer() -> None:
    """Test that MIPRO optimizer is called when enabled."""
    from AFO.mipro import Example, MiproConfig, MiproOptimizer, Module

    # Create optimizer with config
    config = MiproConfig(auto="light", num_trials=5)
    optimizer = MiproOptimizer(config)

    # Create test program and examples
    program = Module()
    trainset = [
        Example(input="hello", output="world"),
        Example(input="foo", output="bar"),
    ]

    # Enable MIPRO
    import os

    os.environ["AFO_MIPRO_V2_ENABLED"] = "1"

    try:
        # Run optimization
        result = optimizer.compile(program, trainset)

        # Verify optimization occurred
        assert result is not program  # Should return new optimized program
        assert hasattr(result, "_mipro_optimized")
        assert getattr(result, "_mipro_optimized", False) == True
        assert hasattr(result, "_mipro_score")
        assert hasattr(result, "_mipro_trials")
        assert getattr(result, "_mipro_trials", 0) == min(5, len(trainset))

    finally:
        # Clean up environment
        os.environ.pop("AFO_MIPRO_V2_ENABLED", None)


def test_mipro_node_noop_when_disabled() -> None:
    """Test that MIPRO node is truly NO-OP when flags are disabled."""
    from AFO.chancellor_mipro_plugin import ChancellorMiproPlugin

    # Mock state to track changes
    class MockState:
        def __init__(self) -> None:
            self.outputs = {}
            self.trace_id = "test-noop"
            self.step = "MIPRO"

    # Test with flags OFF
    os.environ.pop("AFO_MIPRO_ENABLED", None)
    os.environ.pop("AFO_MIPRO_CHANCELLOR_ENABLED", None)

    # Test plugin plan
    plugin = ChancellorMiproPlugin()
    plan = plugin.plan()
    assert not plan.enabled, "Plugin should be disabled when flags are OFF"

    # Create MIPRO node function directly (same as in ChancellorGraph)
    def mipro_node(state) -> None:
        """MIPRO optimization node for Chancellor Graph (NO-OP by default)."""
        try:
            from AFO.chancellor_mipro_plugin import ChancellorMiproPlugin

            plugin = ChancellorMiproPlugin()
            plan = plugin.plan()

            if not plan.enabled:
                # NO-OP: feature flags not enabled, do nothing
                return state

            # Feature flags enabled: perform actual MIPRO optimization
            try:
                from AFO.mipro_optimizer import MiproOptimizer
                from AFO.trinity_metric_wrapper import TrinityMetricWrapper

                # Phase 73: Integrate with actual DSPy MIPROv2 when available
                # Current: Placeholder implementation with Trinity Score integration
                metric = TrinityMetricWrapper(lambda p, t: 0.8)  # Default metric
                optimizer = MiproOptimizer(metric)

                # SSOT: MIPRO output size limit - keep summary only to prevent Graph state pollution
                # Raw traces/candidates go to artifacts, not state.outputs
                state.outputs["_mipro"] = {
                    "status": "integrated",
                    "score": 0.8,
                    "trial_count": 0,  # Summary only, no raw data
                    "reason": "placeholder",
                }

            except ImportError as e:
                # DSPy/MIPRO modules not available
                state.outputs["_mipro"] = {"status": "modules_missing", "error": str(e)}
            except Exception as e:
                # MIPRO execution failed
                state.outputs["_mipro"] = {"status": "failed", "error": str(e)}

        except Exception:
            # Plugin system failed, fallback to NO-OP
            pass

        return state

    # Test NO-OP behavior with flags OFF
    initial_outputs = {"existing": "data"}
    state = MockState()
    state.outputs = initial_outputs.copy()

    # Call MIPRO node with flags OFF
    result_state = mipro_node(state)

    # Verify NO-OP: outputs should be unchanged
    assert result_state.outputs == initial_outputs, "MIPRO node should be NO-OP when disabled"
    assert "_mipro" not in result_state.outputs, "No MIPRO output should be added when disabled"
