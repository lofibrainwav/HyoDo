"""Canonical HyoDo six-virtue ontology.

This module is the semantic source of truth.  Presentation surfaces may add
audience-specific wording, but they must preserve these keys, order, labels,
and measurement roles.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class VirtueContract:
    """One canonical virtue axis and its evidence/representation contract."""

    key: str
    name: str
    korean: str
    hanja: str
    technical_meaning: str
    admissible_evidence: str
    measurement_status: str
    score_role: str
    graph_representation: str


VIRTUE_CONTRACT: tuple[VirtueContract, ...] = (
    VirtueContract(
        "truth",
        "Truth",
        "진",
        "眞",
        "technical correctness",
        "tests, typing, and static checks",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "independent measured axis",
        "pillar column",
    ),
    VirtueContract(
        "goodness",
        "Goodness",
        "선",
        "善",
        "safety and stability",
        "safety findings and coverage",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "independent measured axis",
        "pillar column",
    ),
    VirtueContract(
        "beauty",
        "Beauty",
        "미",
        "美",
        "clarity and maintainability",
        "lint, format, and clarity evidence",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "independent measured axis",
        "pillar column",
    ),
    VirtueContract(
        "benevolence",
        "Benevolence",
        "인",
        "仁",
        "public and developer usability",
        "public-surface and onboarding evidence",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "independent measured axis",
        "pillar column",
    ),
    VirtueContract(
        "hyo",
        "Hyo",
        "효",
        "孝",
        "consent, context alignment, and data protection",
        "policy, host-binding, and access-ledger evidence",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "independent measured axis",
        "pillar column",
    ),
    VirtueContract(
        "eternity",
        "Eternity",
        "영",
        "永",
        "continuity, persistence, and longitudinal evidence",
        "append-only history and continuity evidence",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "independent measured axis",
        "continuity indicator",
    ),
)

CANONICAL_VIRTUE_KEYS: tuple[str, ...] = tuple(v.key for v in VIRTUE_CONTRACT)
CANONICAL_VIRTUE_NAMES: tuple[str, ...] = tuple(v.name for v in VIRTUE_CONTRACT)
HARMONY_AGGREGATE_KEY = "harmony_aggregate"
LEGACY_V5_AGGREGATE_KEY = "s_eternity"


def virtue_by_key() -> Mapping[str, VirtueContract]:
    """Return the canonical virtue contract indexed by machine key."""
    return {v.key: v for v in VIRTUE_CONTRACT}
