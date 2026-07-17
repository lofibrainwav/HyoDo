"""Public API: review-signal naming and legacy score normalization."""

import warnings

from hyodo import (
    LEGACY_TRINITY_WEIGHTS,
    TRINITY_WEIGHTS,
    calculate_trinity_score,
    is_strong_review_signal,
    should_auto_approve,
)


def test_legacy_weights_sum_not_one():
    # Document historical weight sum; normalization is required at use site.
    assert abs(sum(LEGACY_TRINITY_WEIGHTS.values()) - 0.95) < 1e-9
    assert TRINITY_WEIGHTS is LEGACY_TRINITY_WEIGHTS or TRINITY_WEIGHTS == LEGACY_TRINITY_WEIGHTS


def test_legacy_trinity_all_ones_is_100():
    score = calculate_trinity_score(1.0, 1.0, 1.0, serenity=1.0, eternity=1.0)
    assert score == 100.0


def test_is_strong_review_signal_threshold():
    assert is_strong_review_signal(90, 0) is True
    assert is_strong_review_signal(89, 0) is False
    assert is_strong_review_signal(95, 11) is False


def test_should_auto_approve_warns_and_delegates():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = should_auto_approve(95, 5)
    assert value is True
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert any("is_strong_review_signal" in str(w.message) for w in caught)
