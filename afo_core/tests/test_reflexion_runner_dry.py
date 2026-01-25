from __future__ import annotations

from pathlib import Path

import pytest

from AFO.self_expansion.contracts import load_reflexion_contract
from AFO.self_expansion.reflexion_runner import run_reflexion


def test_runner_dry_run_outputs_final() -> None:
    """Verify that the dry-run runner produces the expected JSON structure"""
    # Use absolute path relative to this test file
    config_path = Path(__file__).parent.parent / "config" / "reflexion.yml"
    c = load_reflexion_contract(config_path)
    out = run_reflexion("smoke test", c, dry_run=True)
    assert out["dry_run"] is True
    assert out["input"] == "smoke test"
    assert 1 <= out["iters"] <= c.max_iters
    kinds = [s["kind"] for s in out["steps"]]
    assert "draft" in kinds
    assert "final" in kinds
    assert "content" in out["steps"][0]
