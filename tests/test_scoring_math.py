"""Property-based tests for the HYOGOOK V5 scoring math.

Targets ``hyodo/__init__.py``: ``calculate_geometric_mean``,
``calculate_hygook_v5_score``, and the V5-mode branch of
``calculate_trinity_score`` (taken when both ``benevolence`` and ``loyalty``
are supplied).

Every property asserts what the *current implementation* actually does,
verified empirically first. In particular the geometric mean is computed as
``product ** (1 / 5)``, which is not exact in floating point (e.g. five 10.0
values yield 10.000000000000002), so bounds use tolerances rather than exact
equality.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hyodo import (
    calculate_geometric_mean,
    calculate_hygook_v5_score,
    calculate_trinity_score,
)

# A single strictly-positive pillar value. Bounds stay away from subnormals and
# from overflow so the five-way product and its fifth root remain well-behaved.
positive_value = st.floats(min_value=1e-3, max_value=1e3, allow_nan=False, allow_infinity=False)

# A raw pillar input on the documented 0-1 scale, widened past both bounds so
# the clamp inside ``to_10_scale`` is actually exercised.
raw_pillar = st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False)

# An in-range pillar input on the documented 0-1 scale.
unit_pillar = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


def _clamp01(value: float) -> float:
    """Mirror ``to_10_scale``'s clamp: fold any input into [0, 1]."""
    return max(0.0, min(1.0, value))


# --------------------------------------------------------------------------- #
# calculate_geometric_mean
# --------------------------------------------------------------------------- #


@given(st.lists(positive_value, min_size=5, max_size=5))
def test_geometric_mean_within_bounds(values: list[float]) -> None:
    """For 5 positive inputs the result lies within [min, max] (+/- fp slack)."""
    result = calculate_geometric_mean(values)
    lo, hi = min(values), max(values)
    tol = 1e-9 * max(hi, 1.0)
    assert math.isfinite(result)
    assert lo - tol <= result <= hi + tol


@given(positive_value)
def test_geometric_mean_of_equal_values(value: float) -> None:
    """Geometric mean of five identical positive values is that value."""
    result = calculate_geometric_mean([value] * 5)
    assert result == pytest.approx(value, rel=1e-9, abs=1e-9)


@given(
    st.lists(positive_value, min_size=4, max_size=4),
    st.integers(min_value=0, max_value=4),
)
def test_geometric_mean_zero_when_any_input_is_zero(rest: list[float], index: int) -> None:
    """A single 0.0 anywhere in a length-5 list forces the result to 0.0."""
    values = list(rest)
    values.insert(index, 0.0)
    assert calculate_geometric_mean(values) == 0.0


@given(
    st.lists(positive_value, min_size=4, max_size=4),
    st.integers(min_value=0, max_value=4),
    st.floats(min_value=-1e3, max_value=-1e-3, allow_nan=False, allow_infinity=False),
)
def test_geometric_mean_zero_when_any_input_is_negative(
    rest: list[float], index: int, negative: float
) -> None:
    """Any non-positive element (v <= 0) short-circuits the result to 0.0."""
    values = list(rest)
    values.insert(index, negative)
    assert calculate_geometric_mean(values) == 0.0


@given(st.lists(positive_value, min_size=0, max_size=12).filter(lambda xs: len(xs) != 5))
def test_geometric_mean_wrong_length_returns_one(values: list[float]) -> None:
    """The documented length is 5; any other length returns the 1.0 sentinel."""
    assert calculate_geometric_mean(values) == 1.0


def test_geometric_mean_empty_list_returns_one() -> None:
    """The empty-list guard also returns the 1.0 sentinel."""
    assert calculate_geometric_mean([]) == 1.0


# --------------------------------------------------------------------------- #
# calculate_hygook_v5_score
# --------------------------------------------------------------------------- #


@given(unit_pillar, unit_pillar, unit_pillar, unit_pillar, unit_pillar)
def test_hygook_v5_score_in_documented_range(
    benevolence: float,
    truth: float,
    goodness: float,
    loyalty: float,
    beauty: float,
) -> None:
    """With five in-range pillars, F in [6, 60], S in [1, 10], both finite.

    F = sum(five values on the 1-10 scale) + S, so F - S (the five-way sum)
    must fall within [5, 50].
    """
    f_score, s_eternity = calculate_hygook_v5_score(benevolence, truth, goodness, loyalty, beauty)
    assert math.isfinite(f_score)
    assert math.isfinite(s_eternity)
    assert 6.0 - 1e-9 <= f_score <= 60.0 + 1e-9
    assert 1.0 - 1e-9 <= s_eternity <= 10.0 + 1e-9
    assert 5.0 - 1e-9 <= f_score - s_eternity <= 50.0 + 1e-9


@given(raw_pillar, raw_pillar, raw_pillar, raw_pillar, raw_pillar)
def test_hygook_v5_score_clamps_out_of_range_inputs(
    benevolence: float,
    truth: float,
    goodness: float,
    loyalty: float,
    beauty: float,
) -> None:
    """Out-of-range inputs are folded into [0, 1] before scaling to [1, 10].

    Calling with raw inputs must equal calling with each input pre-clamped to
    [0, 1], and the wild inputs still yield an F/S pair inside the documented
    range.
    """
    raw = calculate_hygook_v5_score(benevolence, truth, goodness, loyalty, beauty)
    clamped = calculate_hygook_v5_score(
        _clamp01(benevolence),
        _clamp01(truth),
        _clamp01(goodness),
        _clamp01(loyalty),
        _clamp01(beauty),
    )
    assert raw == clamped

    f_score, s_eternity = raw
    assert 6.0 - 1e-9 <= f_score <= 60.0 + 1e-9
    assert 1.0 - 1e-9 <= s_eternity <= 10.0 + 1e-9


def test_hygook_v5_score_lower_clamp_boundary() -> None:
    """Inputs <= 0 clamp to 0, mapping to 1.0 on the 1-10 scale (F=6, S=1)."""
    assert calculate_hygook_v5_score(-5, -5, -5, -5, -5) == (6.0, 1.0)
    assert calculate_hygook_v5_score(0, 0, 0, 0, 0) == (6.0, 1.0)


def test_hygook_v5_score_upper_clamp_boundary() -> None:
    """Inputs >= 1 clamp to 1, mapping to 10.0 on the 1-10 scale (F=60, S=10)."""
    f_score, s_eternity = calculate_hygook_v5_score(5, 5, 5, 5, 5)
    assert f_score == pytest.approx(60.0, abs=1e-9)
    assert s_eternity == pytest.approx(10.0, abs=1e-9)


# --------------------------------------------------------------------------- #
# calculate_trinity_score - V5 branch (benevolence AND loyalty provided)
# --------------------------------------------------------------------------- #


@given(unit_pillar, unit_pillar, unit_pillar, unit_pillar, unit_pillar)
def test_trinity_v5_branch_percentage_range(
    truth: float,
    goodness: float,
    beauty: float,
    benevolence: float,
    loyalty: float,
) -> None:
    """V5 branch returns a finite percentage in [0, 100]."""
    score = calculate_trinity_score(
        truth, goodness, beauty, benevolence=benevolence, loyalty=loyalty
    )
    assert math.isfinite(score)
    assert 0.0 <= score <= 100.0


@given(unit_pillar, unit_pillar, unit_pillar, unit_pillar, unit_pillar)
def test_trinity_v5_branch_matches_hygook_formula(
    truth: float,
    goodness: float,
    beauty: float,
    benevolence: float,
    loyalty: float,
) -> None:
    """V5 branch is exactly the documented rescale of the HYOGOOK F score.

    score = round(clamp(((F - 6) / 54) * 100, 0, 100), 2).
    """
    score = calculate_trinity_score(
        truth, goodness, beauty, benevolence=benevolence, loyalty=loyalty
    )
    f_score, _ = calculate_hygook_v5_score(benevolence, truth, goodness, loyalty, beauty)
    expected = round(max(0, min(100, ((f_score - 6) / (60 - 6)) * 100)), 2)
    assert score == expected


@given(raw_pillar, raw_pillar, raw_pillar, raw_pillar, raw_pillar)
def test_trinity_v5_branch_range_with_out_of_range_inputs(
    truth: float,
    goodness: float,
    beauty: float,
    benevolence: float,
    loyalty: float,
) -> None:
    """Even wild inputs stay in [0, 100] thanks to input + output clamping."""
    score = calculate_trinity_score(
        truth, goodness, beauty, benevolence=benevolence, loyalty=loyalty
    )
    assert math.isfinite(score)
    assert 0.0 <= score <= 100.0


def test_trinity_v5_branch_extremes() -> None:
    """The V5 branch spans the full percentage range at the pillar extremes."""
    assert calculate_trinity_score(0, 0, 0, benevolence=0, loyalty=0) == 0
    assert calculate_trinity_score(1, 1, 1, benevolence=1, loyalty=1) == 100
