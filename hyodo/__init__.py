"""HyoDo (孝道) - AI Code Quality Automation

The Way of Devotion: Philosophy-driven code review for AI-assisted development.

Built with the Five Pillars (HYOGOOK V5):
- 仁 (Benevolence): Developer experience and user serenity
- 眞 (Truth): Technical accuracy
- 善 (Goodness): Security and stability
- 忠 (Loyalty): SSOT compliance and cultural continuity
- 美 (Beauty): Code clarity and UX
- 永 (Eternity): Geometric mean of harmony (calculated)
"""

__version__ = "3.1.0"
__author__ = "AFO Kingdom"
__license__ = "MIT"

# HYOGOOK V5 Weights (Phase 127+)
TRINITY_WEIGHTS = {
    "benevolence": 0.25,  # 仁 - Developer/user experience (new)
    "truth": 0.22,  # 眞 - Technical accuracy (was 0.18)
    "goodness": 0.18,  # 善 - Security/stability (unchanged)
    "loyalty": 0.15,  # 忠 - SSOT compliance (new)
    "beauty": 0.15,  # 美 - Code clarity/UX (was 0.12)
}


def calculate_geometric_mean(values: list[float]) -> float:
    """Calculate geometric mean for Eternity (永) pillar.

    S = ⁵√(T × G × In × B × C)

    Args:
        values: List of 5 pillar scores (0-1)

    Returns:
        Geometric mean (0-1)
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
    loyalty: float,
    beauty: float,
) -> tuple[float, float]:
    """Calculate HYOGOOK V5 F score and S (Eternity) value.

    F = (T + G + In + B + C) + ⁵√(T × G × In × B × C)
    S = ⁵√(T × G × In × B × C)

    Args:
        benevolence: 仁 score (0-1, will be scaled to 1-10)
        truth: 眞 score (0-1, will be scaled to 1-10)
        goodness: 善 score (0-1, will be scaled to 1-10)
        loyalty: 忠 score (0-1, will be scaled to 1-10)
        beauty: 美 score (0-1, will be scaled to 1-10)

    Returns:
        Tuple of (F_score, S_eternity)
    """

    # Convert 0-1 scale to 1-10 scale
    def to_10_scale(v: float) -> float:
        return 1 + v * 9  # 0->1, 1->10

    values_10 = [to_10_scale(v) for v in [benevolence, truth, goodness, loyalty, beauty]]
    S = calculate_geometric_mean(values_10)
    arithmetic_sum = sum(values_10)
    F = arithmetic_sum + S
    return F, S


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

    Legacy mode: Uses 5-pillar weighted sum if benevolence/loyalty not provided.
    V5 mode: Uses HYOGOOK V5 formula if all 5 V5 pillars provided.

    Args:
        truth: Technical accuracy score (0-1)
        goodness: Security/stability score (0-1)
        beauty: Code clarity score (0-1)
        serenity: UX score (0-1), default 1.0 (legacy, maps to benevolence)
        eternity: Maintainability score (0-1), default 1.0 (legacy, now calculated)
        benevolence: Developer/user experience (0-1), optional for V5 mode
        loyalty: SSOT compliance (0-1), optional for V5 mode

    Returns:
        Trinity Score as percentage (0-100)
    """
    # HYOGOOK V5 mode
    if benevolence is not None and loyalty is not None:
        F, S = calculate_hygook_v5_score(benevolence, truth, goodness, loyalty, beauty)
        # Convert F (range ~6-60) to percentage (0-100)
        # F=6 → 0%, F=60 → 100%
        score = ((F - 6) / (60 - 6)) * 100
        return round(max(0, min(100, score)), 2)

    # Legacy weighted mode (V1)
    score = (
        TRINITY_WEIGHTS["truth"] * truth
        + TRINITY_WEIGHTS["goodness"] * goodness
        + TRINITY_WEIGHTS["beauty"] * beauty
        + (TRINITY_WEIGHTS["benevolence"] * serenity)  # Map serenity to benevolence
        + (TRINITY_WEIGHTS["loyalty"] * eternity)  # Map eternity to loyalty
    )
    return round(score * 100, 2)


def should_auto_approve(trinity_score: float, risk_score: float = 0) -> bool:
    """Determine if changes can be auto-approved.

    Args:
        trinity_score: Trinity Score (0-100)
        risk_score: Risk score (0-100), lower is better

    Returns:
        True if auto-approve eligible (Trinity >= 90, Risk <= 10)
    """
    return trinity_score >= 90 and risk_score <= 10


__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "TRINITY_WEIGHTS",
    "calculate_trinity_score",
    "should_auto_approve",
]
