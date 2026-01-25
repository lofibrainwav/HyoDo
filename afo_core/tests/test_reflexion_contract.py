from __future__ import annotations

from pathlib import Path

import pytest

from AFO.self_expansion.contracts import load_reflexion_contract


def test_contract_loads_default() -> None:
    """Verify the default contract loads correctly"""
    # Use absolute path relative to this test file (tests/../config/reflexion.yml)
    config_path = Path(__file__).parent.parent / "config" / "reflexion.yml"
    c = load_reflexion_contract(config_path)
    assert c.version >= 1
    assert 1 <= c.max_iters <= 20
    assert 1 <= c.time_budget_sec <= 300
    assert 0 <= c.risk_threshold <= 100
    assert isinstance(c.fingerprint, str) and len(c.fingerprint) == 16


def test_contract_rejects_bad_values(tmp_path: Path) -> None:
    """Verify that invalid contract values are caught during loading"""
    p = tmp_path / "bad.yml"
    p.write_text(
        "version: 1\nmax_iters: 999\ntime_budget_sec: 30\ndry_run_default: true\nrisk_threshold: 10\nstop_conditions: []\njudge: {rubric: [clarity], pass_score: 0.9}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="contract_invalid: max_iters"):
        load_reflexion_contract(p)
