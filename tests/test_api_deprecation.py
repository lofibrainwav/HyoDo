"""Public API: review-signal naming and legacy score normalization."""

import hyodo
from hyodo import (
    LEGACY_TRINITY_WEIGHTS,
    TRINITY_WEIGHTS,
    calculate_trinity_score,
    is_strong_review_signal,
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
    assert is_strong_review_signal(90, 10.0) is True


def test_is_strong_review_signal_rejects_non_numeric_risk():
    import pytest

    with pytest.raises(TypeError, match="risk_score"):
        is_strong_review_signal(90, "low")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="trinity_score"):
        is_strong_review_signal("90", 0)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        is_strong_review_signal(True, 0)  # type: ignore[arg-type]


def test_should_auto_approve_removed_in_400():
    # 3.2.x에서 예고한 4.0.0 제거 이행 확인
    assert not hasattr(hyodo, "should_auto_approve")
