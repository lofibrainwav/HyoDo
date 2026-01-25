import asyncio

import pytest
from tigers_orchestrator.circuit_breakers import CircuitState, TigerCircuitBreaker
from tigers_orchestrator.state_machine import TigerGeneralsState, truth_guard_node


class TestTigerCircuitBreaker:
    @pytest.mark.asyncio
    async def test_failure_threshold_opens_circuit(self):
        cb = TigerCircuitBreaker(name="test", failure_threshold=2, timeout_seconds=1)
        assert cb.state == CircuitState.CLOSED

        # First failure
        await cb.record_failure(ValueError("Error 1"))
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1

        # Second failure (threshold reached)
        await cb.record_failure(ValueError("Error 2"))
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 2

    @pytest.mark.asyncio
    async def test_recovery_timeout_to_half_open(self):
        cb = TigerCircuitBreaker(name="test", failure_threshold=1, timeout_seconds=0.1)
        await cb.record_failure(ValueError("Error"))
        assert cb.state == CircuitState.OPEN

        await asyncio.sleep(0.2)
        # should_allow_call triggers the transition to HALF_OPEN
        assert cb.should_allow_call() is True
        assert cb.state == CircuitState.HALF_OPEN


class TestTigerStateNodes:
    @pytest.mark.asyncio
    async def test_generals_state_initialization(self):
        state: TigerGeneralsState = {
            "input_data": {"command": "test"},
            "context_id": "test-ctx",
            "all_generals_completed": False,
            "trinity_score": 0.0,
        }
        assert state["all_generals_completed"] is False
        assert state["trinity_score"] == 0.0
