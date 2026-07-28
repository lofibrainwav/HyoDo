"""Hyo restoration (philosophy V6) contract tests.

Covers the v4.0.0 completion: ``hyo`` is the canonical fourth pillar, the
``loyalty`` keyword alias is fully removed, the legacy trinity path stays
frozen, and doc/code pillar naming stays aligned.
"""

from __future__ import annotations

import inspect
import warnings
from pathlib import Path

import pytest

import hyodo
from hyodo import calculate_hygook_v5_score, calculate_trinity_score

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_hyo_keyword_works():
    # The hyo keyword produces F and S scores without emitting a warning.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        f_score, s_eternity = calculate_hygook_v5_score(
            benevolence=0.8, truth=0.8, goodness=0.8, hyo=0.8, beauty=0.8
        )
    assert f_score > 6.0
    assert s_eternity > 1.0


def test_loyalty_keyword_removed():
    # The loyalty keyword alias was fully removed in 4.0.0 - it must raise TypeError.
    with pytest.raises(TypeError):
        calculate_hygook_v5_score(benevolence=1, truth=1, goodness=1, beauty=1, loyalty=1)


def test_positional_fourth_arg_no_warning():
    # The 4th positional argument binds to hyo, so existing positional
    # callers keep working without a warning.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        positional = calculate_hygook_v5_score(0.9, 0.9, 0.9, 0.6, 0.9)
    keyword = calculate_hygook_v5_score(
        benevolence=0.9, truth=0.9, goodness=0.9, hyo=0.6, beauty=0.9
    )
    assert positional == keyword


def test_trinity_legacy_frozen():
    # The legacy trinity path is frozen: same results, no warning, loyalty kept.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert calculate_trinity_score(1, 1, 1, benevolence=1, loyalty=1) == 100
        assert calculate_trinity_score(0, 0, 0, benevolence=0, loyalty=0) == 0
        legacy_weighted = calculate_trinity_score(1, 1, 1, serenity=1, eternity=1)
    assert legacy_weighted == 100


def test_philosophy_version_field():
    # The philosophy version is its own namespace, separate from the package semver.
    assert hyodo.__philosophy_version__ == "V6"
    assert "__philosophy_version__" in hyodo.__all__


def test_signature_pillar_parity():
    # The API argument set is exactly the five pillars - loyalty does not exist.
    sig = inspect.signature(calculate_hygook_v5_score)
    assert list(sig.parameters) == ["benevolence", "truth", "goodness", "hyo", "beauty"]
    assert "loyalty" not in sig.parameters


def test_philosophy_doc_alignment():
    # The PHILOSOPHY.md pillar table must say Hyo and carry no Loyalty row,
    # so doc and code cannot drift apart again.
    text = (REPO_ROOT / "PHILOSOPHY.md").read_text(encoding="utf-8")
    assert "| Hyo |" in text
    assert "| Loyalty |" not in text


def test_should_auto_approve_removed():
    # The 4.0.0 removal notice was honoured: the deprecated alias is gone.
    assert not hasattr(hyodo, "should_auto_approve")
    assert "should_auto_approve" not in hyodo.__all__


def test_score_floor_is_six():
    # The 0->1 clamp puts the F floor at 6.0 and the S floor at 1.0, so
    # "one axis at zero zeroes the whole score" does not hold here.
    f_score, s_eternity = calculate_hygook_v5_score(0, 0, 0, 0, 0)
    assert f_score == pytest.approx(6.0)
    assert s_eternity == pytest.approx(1.0)
