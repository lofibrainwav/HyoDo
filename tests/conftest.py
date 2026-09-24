"""Pytest/Hypothesis configuration for HyoDo.

CI determinism is separate from local exploration:
- CI disables the example database and uses deterministic generation so a
  given Hypothesis/Python/test version is repeatable on a fresh clone.
- Local runs keep Hypothesis defaults, including its local example database and
  normal exploration, so development does not become artificially narrow.
- Durable regression cases belong in explicit ``@example`` decorators; generated
  sequences are not promised to remain identical across dependency/test changes.
"""

from __future__ import annotations

import os

import pytest
from hypothesis import HealthCheck, settings

settings.register_profile(
    "hyodo_ci",
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
    print_blob=True,
    database=None,
)

if os.environ.get("CI"):
    settings.load_profile("hyodo_ci")


@pytest.fixture(autouse=True)
def _isolated_mcp_reader_registry(tmp_path_factory, monkeypatch):
    """In-process MCP readers must never register in the developer's real registry."""
    monkeypatch.setenv("HYODO_MCP_READER_DIR", str(tmp_path_factory.mktemp("mcp-readers")))


@pytest.fixture(autouse=True)
def _isolated_user_state(tmp_path_factory, monkeypatch):
    """Operator authority state must never touch the developer's real ~/.hyodo."""
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path_factory.mktemp("user-state")))
