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
    # hyo 키워드가 경고 없이 정상 F·S를 산출한다
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        f_score, s_eternity = calculate_hygook_v5_score(
            benevolence=0.8, truth=0.8, goodness=0.8, hyo=0.8, beauty=0.8
        )
    assert f_score > 6.0
    assert s_eternity > 1.0


def test_loyalty_keyword_removed():
    # 4.0.0에서 loyalty 키워드 alias는 완전 제거 — TypeError
    with pytest.raises(TypeError):
        calculate_hygook_v5_score(benevolence=1, truth=1, goodness=1, beauty=1, loyalty=1)


def test_positional_fourth_arg_no_warning():
    # 4번째 위치 인자는 hyo에 바인딩되어 기존 위치 호출이 무경고 호환된다
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        positional = calculate_hygook_v5_score(0.9, 0.9, 0.9, 0.6, 0.9)
    keyword = calculate_hygook_v5_score(
        benevolence=0.9, truth=0.9, goodness=0.9, hyo=0.6, beauty=0.9
    )
    assert positional == keyword


def test_trinity_legacy_frozen():
    # 레거시 trinity 경로는 동결 — 기존 결과 재현 + 경고 없음 (loyalty 파라미터 유지)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert calculate_trinity_score(1, 1, 1, benevolence=1, loyalty=1) == 100
        assert calculate_trinity_score(0, 0, 0, benevolence=0, loyalty=0) == 0
        legacy_weighted = calculate_trinity_score(1, 1, 1, serenity=1, eternity=1)
    assert legacy_weighted == 100


def test_philosophy_version_field():
    # 철학 버전 필드는 패키지 semver와 별도 네임스페이스로 노출된다
    assert hyodo.__philosophy_version__ == "V6"
    assert "__philosophy_version__" in hyodo.__all__


def test_signature_pillar_parity():
    # API 인자 집합 = 5기둥 집합, loyalty는 존재하지 않는다
    sig = inspect.signature(calculate_hygook_v5_score)
    assert list(sig.parameters) == ["benevolence", "truth", "goodness", "hyo", "beauty"]
    assert "loyalty" not in sig.parameters


def test_philosophy_doc_alignment():
    # PHILOSOPHY.md 기둥 표가 Hyo를 쓰고 Loyalty 행이 없어야 한다 (정합 붕괴 재발 방지)
    text = (REPO_ROOT / "PHILOSOPHY.md").read_text(encoding="utf-8")
    assert "| Hyo |" in text
    assert "| Loyalty |" not in text


def test_should_auto_approve_removed():
    # 4.0.0 제거 예고를 이행 — deprecated alias 완전 소멸
    assert not hasattr(hyodo, "should_auto_approve")
    assert "should_auto_approve" not in hyodo.__all__


def test_score_floor_is_six():
    # 0→1 클램프 때문에 F 하한은 6.0, S 하한은 1.0 — "한 축 0이면 전체 0"은 성립하지 않는다
    f_score, s_eternity = calculate_hygook_v5_score(0, 0, 0, 0, 0)
    assert f_score == pytest.approx(6.0)
    assert s_eternity == pytest.approx(1.0)
