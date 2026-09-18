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
    philosophical_scope: str
    measurable_proxy: str
    admissible_evidence: str
    measurement_status: str
    coverage_limitation: str
    authority_boundary: str
    score_role: str
    graph_representation: str


VIRTUE_CONTRACT: tuple[VirtueContract, ...] = (
    VirtueContract(
        "truth",
        "Truth",
        "진",
        "眞",
        "technical correctness",
        "Truthful technical claims and correct representation of system behavior",
        "Tests, typing, and static checks",
        "tests, typing, and static checks",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "Checks cover selected implementation properties, not truth in every context",
        "Review signal only; never execution authority",
        "independent measured axis",
        "pillar column",
    ),
    VirtueContract(
        "goodness",
        "Goodness",
        "선",
        "善",
        "safety and stability",
        "Reduce preventable harm while preserving necessary safeguards",
        "Safety findings and coverage",
        "safety findings and coverage",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "Safety checks do not measure all downstream harm or risk",
        "Review signal only; never execution authority",
        "independent measured axis",
        "pillar column",
    ),
    VirtueContract(
        "beauty",
        "Beauty",
        "미",
        "美",
        "clarity and maintainability",
        "Coherence, clarity, and form that make work easier to understand and maintain",
        "Lint, format, and clarity evidence",
        "lint, format, and clarity evidence",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "Style and clarity signals do not establish usability for every audience",
        "Review signal only; never execution authority",
        "independent measured axis",
        "pillar column",
    ),
    VirtueContract(
        "benevolence",
        "Benevolence",
        "인",
        "仁",
        "public and developer usability",
        "Other-awareness, relationship awareness, and sensitivity to participant, role, and context",
        "Public usability, API/onboarding clarity, and user-facing failure visibility",
        "public-surface and onboarding evidence",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "These human-facing signals do not fully measure relationships, other-awareness, or participant experience",
        "Review signal only; never execution authority",
        "independent measured axis",
        "pillar column",
    ),
    VirtueContract(
        "hyo",
        "Hyo",
        "효",
        "孝",
        "consent, context alignment, and data protection",
        "Technology carries its share of the burden; respect choice, consent, context, and protective friction",
        "Consent, context alignment, privacy/data protection, and observed friction or intervention signals",
        "policy, host-binding, and access-ledger evidence",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "Current proxies do not measure total human cost; no calibrated friction score is defined",
        "Review signal only; never execution authority",
        "independent measured axis",
        "pillar column",
    ),
    VirtueContract(
        "eternity",
        "Eternity",
        "영",
        "永",
        "continuity, persistence, and longitudinal evidence",
        "Preserve continuity and learn responsibly across time",
        "Append-only history and continuity evidence",
        "append-only history and continuity evidence",
        "OBSERVED/PARTIAL/UNOBSERVED",
        "History and continuity records do not prove long-term value by themselves",
        "Review signal only; never execution authority",
        "independent measured axis",
        "continuity indicator",
    ),
)

CANONICAL_VIRTUE_KEYS: tuple[str, ...] = tuple(v.key for v in VIRTUE_CONTRACT)
CANONICAL_VIRTUE_NAMES: tuple[str, ...] = tuple(v.name for v in VIRTUE_CONTRACT)
# Philosophy-to-engineering document labels. Machine keys and historical names
# remain stable so existing receipts and consumers are not silently renamed.
DOCUMENT_VIRTUE_NAMES: Mapping[str, str] = {
    "truth": "Truth",
    "goodness": "Good",
    "beauty": "Beauty",
    "benevolence": "Humanity",
    "hyo": "Hyo",
    "eternity": "Longevity",
}
# Reserved non-virtue namespace only. HyoDo defines and emits no canonical
# aggregate over the six axes; the current score CLI remains the separate V5
# compatibility path under its historical S_eternity label.
HARMONY_AGGREGATE_KEY = "harmony_aggregate"
LEGACY_V5_AGGREGATE_KEY = "s_eternity"


def virtue_by_key() -> Mapping[str, VirtueContract]:
    """Return the canonical virtue contract indexed by machine key."""
    return {v.key: v for v in VIRTUE_CONTRACT}
