"""Dashboard cards show each built-in gate under the lens the canonical
contract and the evidence envelope attribute it to."""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from hyodo.cli.main import GateResult, GateStatus, collect_dashboard_evidence
from hyodo.dashboard import render_dashboard_html
from hyodo.gates import GATES_TRUST_ENV_VAR

# Canonical machine key -> dashboard card id.
CARD_FOR_LENS = {"truth": "jin", "goodness": "seon", "beauty": "mi"}
# Built-in gate -> the metric label its card shows.
GATE_LABEL = {"typecheck": "Type check", "tests": "Tests", "lint_format": "Lint and format"}


@pytest.fixture
def html(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict, str]:
    monkeypatch.setenv(GATES_TRUST_ENV_VAR, "1")
    ok = GateResult(GateStatus.PASS, "ok")
    safety = {"risk_score": 0, "source": "git diff HEAD", "findings": []}
    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=ok),
        patch("hyodo.cli.main.run_ruff_check", return_value=ok),
        patch("hyodo.cli.main.run_pytest_check", return_value=ok),
        patch("hyodo.cli.main.run_sbom_check", return_value=ok),
        patch("hyodo.cli.main.run_safety_scan", return_value=safety),
    ):
        evidence = collect_dashboard_evidence(tmp_path)
    return evidence, render_dashboard_html(evidence)


def _card_labels(page: str, card: str) -> list[str]:
    section = re.search(
        rf'<section class="card [^"]*" aria-labelledby="{card}">(.*?)</section>', page, re.S
    )
    assert section is not None, card
    return re.findall(r'<span class="metric-label">(.*?)</span>', section.group(1))


def test_each_builtin_gate_sits_in_the_card_of_its_attributed_lens(html) -> None:
    evidence, page = html
    for gate, label in GATE_LABEL.items():
        card = CARD_FOR_LENS[evidence["gates"][gate]["pillar"]]
        assert label in _card_labels(page, card), (gate, card)
        others = set(CARD_FOR_LENS.values()) - {card}
        assert all(label not in _card_labels(page, other) for other in others), gate


def test_tests_are_truth_and_safety_is_goodness(html) -> None:
    _evidence, page = html
    assert "Tests" in _card_labels(page, "jin")
    assert "Tests" not in _card_labels(page, "seon")
    assert "High-risk findings" in _card_labels(page, "seon")
    assert "Safety scan scope" in _card_labels(page, "seon")
