"""HyoDo - AI Code Quality Automation

The Way of Devotion: Philosophy-driven code review for AI-assisted development.

Built with the Six Pillars (HYOGOOK F-score, philosophy V6):
- Benevolence: Developer experience and user serenity
- Truth: Technical accuracy
- Goodness: Security and stability
- Hyo: Reciprocal and voluntary continuity — SSOT discipline
  (supersedes one-sided Loyalty; the `loyalty=` alias was removed in 4.0.0)
- Beauty: Code clarity and UX
- Eternity: Geometric mean of harmony (calculated)

HYOGOOK F-score formula (SSOT; formula lineage label V5, philosophy V6):
  F = sum(five pillars on 1–10 scale) + geometric_mean
  S = geometric_mean
Review-emphasis percentages are philosophical labels only — not F weights.
"""

from __future__ import annotations

__version__ = "4.1.0"
__philosophy_version__ = "V6"
__author__ = "AFO Kingdom"
__license__ = "MIT"

# Legacy compatibility weights (WEIGHTED_V1 / calculate_trinity_score legacy path).
# Not used by the HYOGOOK F-score. Sum is normalized at use site.
# Key name "loyalty" is frozen for historical score reproducibility.
TRINITY_WEIGHTS = {
    "benevolence": 0.25,  # Developer/user experience (legacy)
    "truth": 0.22,  # Technical accuracy (legacy)
    "goodness": 0.18,  # Security/stability (legacy)
    "loyalty": 0.15,  # SSOT compliance (legacy; philosophy V6 uses Hyo)
    "beauty": 0.15,  # Code clarity/UX (legacy)
}
LEGACY_TRINITY_WEIGHTS = TRINITY_WEIGHTS


def calculate_geometric_mean(values: list[float]) -> float:
    """Calculate geometric mean for Eternity pillar.

    S = ⁵√(T × G × In × B × C)

    Args:
        values: List of 5 pillar scores (0-1 or 1-10 scale)

    Returns:
        Geometric mean using the same scale as the input values.
    """
    if not values or len(values) != 5:
        return 1.0

    product = 1.0
    for v in values:
        if v <= 0:
            return 0.0
        product *= v

    return product ** (1 / 5)


def calculate_hygook_v5_score(
    benevolence: float,
    truth: float,
    goodness: float,
    hyo: float,
    beauty: float,
) -> tuple[float, float]:
    """Calculate HYOGOOK V5 F score and S (Eternity) value.

    F = (T + G + In + B + C) + ⁵√(T × G × In × B × C)
    S = ⁵√(T × G × In × B × C)

    Args:
        benevolence: Benevolence score (0-1, will be scaled to 1-10)
        truth: Truth score (0-1, will be scaled to 1-10)
        goodness: Goodness score (0-1, will be scaled to 1-10)
        hyo: Hyo score (0-1, will be scaled to 1-10). Reciprocal and
            voluntary continuity; supersedes the one-sided ``loyalty``,
            whose keyword alias was removed in 4.0.0.
        beauty: Beauty score (0-1, will be scaled to 1-10)

    Returns:
        Tuple of (F_score, S_eternity)
    """

    def to_10_scale(v: float) -> float:
        """Scale a unit-interval pillar value to the inclusive 1-to-10 range."""
        bounded = max(0.0, min(1.0, v))
        return 1 + bounded * 9  # 0->1, 1->10

    values_10 = [to_10_scale(v) for v in [benevolence, truth, goodness, hyo, beauty]]
    s_eternity = calculate_geometric_mean(values_10)
    f_score = sum(values_10) + s_eternity
    return f_score, s_eternity


def calculate_trinity_score(
    truth: float,
    goodness: float,
    beauty: float,
    serenity: float = 1.0,
    eternity: float = 1.0,
    benevolence: float | None = None,
    loyalty: float | None = None,
) -> float:
    """Calculate Trinity Score from pillar values (HYOGOOK V5 compatible).

    Legacy mode: Uses weighted compatibility if benevolence/loyalty are not provided.
    V5 mode: Uses HYOGOOK V5 formula if all V5 pillars are provided.

    Args:
        truth: Technical accuracy score (0-1)
        goodness: Security/stability score (0-1)
        beauty: Code clarity score (0-1)
        serenity: UX score (0-1), default 1.0 (legacy, maps to benevolence)
        eternity: Maintainability score (0-1), default 1.0 (legacy, maps to loyalty)
        benevolence: Developer/user experience (0-1), optional for V5 mode
        loyalty: SSOT compliance (0-1), optional for V5 mode

    Returns:
        Trinity Score as percentage (0-100)
    """
    if benevolence is not None and loyalty is not None:
        f_score, _ = calculate_hygook_v5_score(benevolence, truth, goodness, loyalty, beauty)
        score = ((f_score - 6) / (60 - 6)) * 100
        return round(max(0, min(100, score)), 2)

    weights = LEGACY_TRINITY_WEIGHTS
    weight_sum = sum(weights.values())
    weighted = (
        weights["truth"] * truth
        + weights["goodness"] * goodness
        + weights["beauty"] * beauty
        + weights["benevolence"] * serenity
        + weights["loyalty"] * eternity
    )
    # Normalize so all-ones inputs yield 100 (legacy sum was 0.95 without this).
    score = weighted / weight_sum if weight_sum else 0.0
    return round(max(0, min(1, score)) * 100, 2)


def is_strong_review_signal(trinity_score: float, risk_score: float = 0) -> bool:
    """Return True when scores meet the strong *review signal* threshold.

    This is not automatic approval and never grants write/merge authority.
    Humans remain the final gate.

    Args:
        trinity_score: Trinity Score (0-100), numeric
        risk_score: Risk score (0-100), lower is better; must be numeric
            (level strings such as ``"low"`` / ``"high"`` are rejected)

    Returns:
        True if strong-review-signal eligible (Trinity >= 90, Risk <= 10)

    Raises:
        TypeError: if either argument is not an int or float (bool excluded)
    """
    if isinstance(trinity_score, bool) or not isinstance(trinity_score, (int, float)):
        raise TypeError(f"trinity_score must be a number 0-100, got {type(trinity_score).__name__}")
    if isinstance(risk_score, bool) or not isinstance(risk_score, (int, float)):
        raise TypeError(
            "risk_score must be a number 0-100 (not a level string), "
            f"got {type(risk_score).__name__}"
        )
    return float(trinity_score) >= 90 and float(risk_score) <= 10


__all__ = [
    "LEGACY_TRINITY_WEIGHTS",
    "TRINITY_WEIGHTS",
    "__author__",
    "__license__",
    "__philosophy_version__",
    "__version__",
    "calculate_geometric_mean",
    "calculate_hygook_v5_score",
    "calculate_trinity_score",
    "is_strong_review_signal",
]
