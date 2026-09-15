"""Tests that ontology and compatibility semantics cannot silently drift."""

from __future__ import annotations

from pathlib import Path

import pytest

from hyodo import calculate_hygook_v5_score
from hyodo.dashboard import PILLAR_SPECS
from hyodo.gates import VALID_PILLARS
from hyodo.skills import PILLARS
from hyodo.virtues import (
    CANONICAL_VIRTUE_KEYS,
    DOCUMENT_VIRTUE_NAMES,
    HARMONY_AGGREGATE_KEY,
    LEGACY_V5_AGGREGATE_KEY,
    VIRTUE_CONTRACT,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_canonical_contract_has_exactly_six_ordered_virtues() -> None:
    assert CANONICAL_VIRTUE_KEYS == (
        "truth",
        "goodness",
        "beauty",
        "benevolence",
        "hyo",
        "eternity",
    )
    assert tuple(v.key for v in VIRTUE_CONTRACT) == CANONICAL_VIRTUE_KEYS
    assert tuple(v.name for v in VIRTUE_CONTRACT) == (
        "Truth",
        "Goodness",
        "Beauty",
        "Benevolence",
        "Hyo",
        "Eternity",
    )
    assert PILLARS == CANONICAL_VIRTUE_KEYS
    assert set(CANONICAL_VIRTUE_KEYS) == VALID_PILLARS


def test_document_labels_follow_philosophy_definition_without_renaming_keys() -> None:
    assert tuple(DOCUMENT_VIRTUE_NAMES[key] for key in CANONICAL_VIRTUE_KEYS) == (
        "Truth",
        "Good",
        "Beauty",
        "Humanity",
        "Hyo",
        "Longevity",
    )
    assert tuple(DOCUMENT_VIRTUE_NAMES) == CANONICAL_VIRTUE_KEYS


def test_aggregate_namespace_is_not_the_eternity_virtue() -> None:
    assert HARMONY_AGGREGATE_KEY == "harmony_aggregate"
    assert LEGACY_V5_AGGREGATE_KEY == "s_eternity"
    assert HARMONY_AGGREGATE_KEY not in CANONICAL_VIRTUE_KEYS
    contract = (REPO_ROOT / "docs" / "VIRTUE_CONTRACT.md").read_text(encoding="utf-8")
    assert "does **not** define or emit a canonical aggregate across the six virtue" in contract
    assert "reserved namespace constant" in contract


def test_dashboard_has_six_cards_in_canonical_order() -> None:
    assert len(PILLAR_SPECS) == 6
    assert tuple(spec[3] for spec in PILLAR_SPECS) == (
        "Truth",
        "Good",
        "Beauty",
        "Humanity",
        "Hyo",
        "Longevity",
    )


def test_hygook_v5_keeps_its_historical_floor() -> None:
    # V5 compatibility remains 0 -> 1 on its 1-10 scale; it is not the
    # independent Eternity axis or a six-virtue aggregate.
    f_score, s_value = calculate_hygook_v5_score(0, 0, 0, 0, 0)
    assert f_score == pytest.approx(6.0)
    assert s_value == pytest.approx(1.0)


def test_current_facing_surfaces_use_published_version_and_boundary() -> None:
    current_surfaces = (
        REPO_ROOT / "docs" / "CURRENT_STATE.md",
        REPO_ROOT / "docs" / "capabilities.json",
        REPO_ROOT / "ROADMAP.md",
        REPO_ROOT / "site" / "src" / "pages" / "index.astro",
        REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "current-state.md",
        REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "roadmap.md",
    )
    for path in current_surfaces:
        text = path.read_text(encoding="utf-8")
        assert "publication is pending" not in text.lower(), path
    assert (
        "4.19.3"
        not in (REPO_ROOT / "ROADMAP.md")
        .read_text(encoding="utf-8")
        .split("Landed and released:", 1)[0]
    )
    assert "first organ of an open-source Agent OS" not in (
        REPO_ROOT / "site" / "src" / "content" / "docs" / "docs" / "roadmap.md"
    ).read_text(encoding="utf-8")
