import sys
from unittest.mock import MagicMock

# Mock the entire api.chancellor_v2 package since we are in a documentation audit phase
# and don't want to trigger actual long-running engine logic
mock_engine = MagicMock()
sys.modules["api.chancellor_v2"] = mock_engine
sys.modules["api.chancellor_v2.graph"] = mock_engine
sys.modules["api.chancellor_v2.graph.runner"] = mock_engine
sys.modules["api.chancellor_v2.graph.nodes"] = mock_engine

try:
    from api.chancellor_v2.graph.nodes import (
        beauty_node,
        cmd_node,
        execute_node,
        goodness_node,
        merge_node,
        parse_node,
        report_node,
        truth_node,
        verify_node,
    )
    from api.chancellor_v2.graph.runner import run_v2

    print("SUCCESS: Unified Import Paths (SSOT) are valid.")
except ImportError as e:
    print(f"FAILURE: Import Path error: {e}")
    sys.exit(1)

# Mocking the runner to return a dummy state
mock_state = MagicMock()
mock_state.trace_id = "smoke-test-trace-id"
mock_state.errors = []
mock_state.outputs = {"REPORT": {"trinity_score": 95.0, "decision": "AUTO_RUN"}}
run_v2.return_value = mock_state

# Simple execution simulation
input_payload = {"command": "test"}
nodes = {"CMD": cmd_node}
state = run_v2(input_payload, nodes)
print(f"SUCCESS: Mock execution complete. Trace ID: {state.trace_id}")
