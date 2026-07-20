"""Hyo restoration (philosophy V6) contract tests.

Covers the v3.3.0 rename path: ``hyo`` supersedes the one-sided ``loyalty``
(kept as a deprecated keyword alias until 4.0.0), the frozen legacy trinity
path, and doc/code pillar alignment.
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


def test_loyalty_deprecation_warns_and_maps():
    # loyalty 키워드는 DeprecationWarning을 내고 hyo와 동일 결과로 매핑된다
    with pytest.warns(DeprecationWarning, match="loyalty"):
        legacy = calculate_hygook_v5_score(
            benevolence=0.7, truth=0.7, goodness=0.7, beauty=0.7, loyalty=0.5
        )
    modern = calculate_hygook_v5_score(
        benevolence=0.7, truth=0.7, goodness=0.7, hyo=0.5, beauty=0.7
    )
    assert legacy == modern


def test_hyo_loyalty_conflict_raises():
    # 두 인자 동시 전달은 TypeError로 즉시 차단된다
    with pytest.raises(TypeError):
        calculate_hygook_v5_score(benevolence=1, truth=1, goodness=1, hyo=1, beauty=1, loyalty=1)


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
    # 레거시 trinity 경로는 동결 — 기존 결과 재현 + 경고 없음
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
    # API 위치 인자 집합 = 5기둥 집합 (문서-코드 정합의 코드 쪽 앵커)
    sig = inspect.signature(calculate_hygook_v5_score)
    positional = [
        name
        for name, p in sig.parameters.items()
        if p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]
    assert positional == ["benevolence", "truth", "goodness", "hyo", "beauty"]
    assert sig.parameters["loyalty"].kind is inspect.Parameter.KEYWORD_ONLY


def test_philosophy_doc_alignment():
    # PHILOSOPHY.md 기둥 표가 Hyo를 쓰고 Loyalty 행이 없어야 한다 (정합 붕괴 재발 방지)
    text = (REPO_ROOT / "PHILOSOPHY.md").read_text(encoding="utf-8")
    assert "| Hyo |" in text
    assert "| Loyalty |" not in text


def test_score_floor_is_six():
    # 0→1 클램프 때문에 F 하한은 6.0, S 하한은 1.0 — "한 축 0이면 전체 0"은 성립하지 않는다
    f_score, s_eternity = calculate_hygook_v5_score(0, 0, 0, 0, 0)
    assert f_score == pytest.approx(6.0)
    assert s_eternity == pytest.approx(1.0)
