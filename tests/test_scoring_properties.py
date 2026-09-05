"""Property-based tests for the scoring math — invariants derived from philosophy.

Philosophy version V6 defines the HYOGOOK F-score:
  F = Σ(five pillars on 1-10 scale) + ⁵√(Π of those five)
  S = ⁵√(Π)

Three invariants flow directly from the philosophy document (PHILOSOPHY.md):

1. **Monotonicity (Benevolence):** Raising any pillar must never lower F or S.
   If an agent reports a higher score, the review signal must not weaken.

2. **Symmetry (Beauty):** Pillar order must not affect the result.
   Permuting inputs must produce the same F and S — no pillar is privileged
   by position.

3. **Boundedness (Eternity):** F ∈ [6, 60], S ∈ [1, 10].
   The to_10_scale maps raw 0 → 1, so S never collapses to 0 (fail-closed
   through floor, not zero). The bounds are exact at the extremes.

These are *properties*, not examples. Hypothesis generates examples via
random sampling, targeted edge-case exploration, and automatic shrinking;
failures reveal real boundary assumptions, not unlucky examples.
"""

from __future__ import annotations

from itertools import permutations

import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from hyodo import calculate_hygook_v5_score

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

unit_value = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


# ---------------------------------------------------------------------------
# 1. Monotonicity — raising any pillar never lowers F or S
# ---------------------------------------------------------------------------


@given(
    base_values=st.lists(unit_value, min_size=5, max_size=5),
    index=st.integers(min_value=0, max_value=4),
    increment=st.floats(min_value=0.001, max_value=0.1, allow_nan=False, allow_infinity=False),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_score_monotonicity_raising_one_pillar_never_lowers_score(
    base_values: list[float],
    index: int,
    increment: float,
) -> None:
    """Raising one pillar by a small amount must not decrease F or S.

    This is the mathematical expression of Benevolence: a better signal
    must never produce a weaker review.
    """
    values = list(base_values)
    # Clamp the raised value to [0, 1]
    values[index] = min(1.0, values[index] + increment)

    f_before, s_before = calculate_hygook_v5_score(*base_values)
    f_after, s_after = calculate_hygook_v5_score(*values)

    # Floating-point tolerance: differences smaller than this are noise.
    assert f_after >= f_before - 1e-9, f"Raising pillar {index} lowered F: {f_before} -> {f_after}"
    assert s_after >= s_before - 1e-9, f"Raising pillar {index} lowered S: {s_before} -> {s_after}"


# ---------------------------------------------------------------------------
# 2. Symmetry — permuting pillars produces the same F and S
# ---------------------------------------------------------------------------


@given(st.lists(unit_value, min_size=5, max_size=5))
@settings(deadline=None)
def test_score_symmetry_permutation_invariant(values: list[float]) -> None:
    """All 120 permutations of five pillar scores must yield identical F, S.

    This is the mathematical expression of Beauty: no pillar is privileged
    by position — the formula treats them symmetrically.
    """
    f_ref, s_ref = calculate_hygook_v5_score(*values)

    for perm in permutations(values):
        f_perm, s_perm = calculate_hygook_v5_score(*perm)
        assert f_perm == pytest.approx(f_ref, rel=1e-9, abs=1e-9), (
            f"F not invariant under permutation: {f_ref} vs {f_perm}"
        )
        assert s_perm == pytest.approx(s_ref, rel=1e-9, abs=1e-9), (
            f"S not invariant under permutation: {s_ref} vs {s_perm}"
        )


# ---------------------------------------------------------------------------
# 3. Boundedness — F ∈ [6, 60], S ∈ [1, 10]
# ---------------------------------------------------------------------------


@example(values=[0.0, 0.0, 0.0, 0.0, 0.0])
@example(values=[1.0, 1.0, 1.0, 1.0, 1.0])
@given(st.lists(unit_value, min_size=5, max_size=5))
@settings(deadline=None)
def test_score_bounded_f_and_s_ranges(values: list[float]) -> None:
    """F must lie in [6, 60] and S in [1, 10] for all unit-interval inputs.

    This is the mathematical expression of Eternity: the review signal is
    always a finite, well-bounded number. The to_10_scale maps raw 0 → 1,
    so S never collapses to 0. F minimum is 5*1 + 1 = 6 (all pillars at
    floor); F maximum is 5*10 + 10 = 60 (all pillars at ceiling).
    S is a geometric mean of values in [1,10], so ∈ [1,10].
    """
    f, s = calculate_hygook_v5_score(*values)

    # Floating-point tolerance: the geometric mean of five 10.0s can produce
    # 10.000000000000002 due to rounding in the fifth root.  Use a small epsilon.
    assert 6.0 - 1e-9 <= f <= 60.0 + 1e-9, f"F out of bounds: {f}"
    assert 1.0 - 1e-9 <= s <= 10.0 + 1e-9, f"S out of bounds: {s}"
