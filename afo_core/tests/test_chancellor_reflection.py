"""Smoke test for Chancellor Graph REFLECT node (PH30B)."""

from unittest.mock import AsyncMock, patch

import pytest

from AFO.api.chancellor_v2.graph.nodes.reflect_node import reflect_node
from AFO.api.chancellor_v2.graph.state import GraphState


@pytest.mark.asyncio
async def test_reflect_node_success():
    """Verify that reflect_node correctly audits strategist outputs."""
    # 1. Setup State with strategist outputs
    state = GraphState(
        trace_id="test-trace",
        request_id="test-req",
        input={"command": "Test Command"},
        plan={"action": "test_action"},
    )
    state.outputs["TRUTH"] = {"score": 0.9, "reasoning": "Solid tech"}
    state.outputs["GOODNESS"] = {"score": 0.8, "reasoning": "Safe"}
    state.outputs["BEAUTY"] = {"score": 0.95, "reasoning": "Elegant"}

    # 2. Mock LLM Router
    mock_response = {
        "success": True,
        "response": '{"consistency_score": 0.95, "audit_status": "passed", "findings": ["Audit passed"], "metacognition": "Logic is sound."}',
    }

    with patch(
        "infrastructure.llm.ssot_compliant_router.SSOTCompliantLLMRouter.call_scholar_via_wallet",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.return_value = mock_response

        # 3. Execute Node
        new_state = await reflect_node(state)

        # 4. Assertions
        assert "REFLECT" in new_state.outputs
        reflect_out = new_state.outputs["REFLECT"]
        assert reflect_out["score"] == 0.95
        assert reflect_out["status"] == "passed"
        assert "Deep Reflection" in reflect_out["metadata"]["assessment_mode"]

        # Verify call
        mock_execute.assert_called()


@pytest.mark.asyncio
async def test_reflect_node_fallback_on_error():
    """Verify that reflect_node handles LLM failure gracefully."""
    state = GraphState(
        trace_id="test-trace-fail",
        request_id="test-req-fail",
        input={"command": "Fail Command"},
        plan={},
    )

    with patch(
        "infrastructure.llm.ssot_compliant_router.SSOTCompliantLLMRouter.call_scholar_via_wallet",
        new_callable=AsyncMock,
    ) as mock_execute:
        mock_execute.side_effect = Exception("Yeongdeok is offline")

        new_state = await reflect_node(state)

        assert "REFLECT" in new_state.outputs
        assert new_state.outputs["REFLECT"]["status"] == "passed"  # Default fallback
        assert any("Yeongdeok (REFLECT) audit failed" in err for err in new_state.errors)
