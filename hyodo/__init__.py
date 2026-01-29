"""HyoDo (孝道) - AI Code Quality Automation

The Way of Devotion: Philosophy-driven code review for AI-assisted development.

Built with the Five Pillars:
- 眞 (Truth): Technical accuracy
- 善 (Goodness): Security and stability
- 美 (Beauty): Code clarity
- 孝 (Serenity): User experience
- 永 (Eternity): Long-term maintainability
"""

__version__ = "3.0.0"
__author__ = "AFO Kingdom"
__license__ = "MIT"

# Trinity Score weights
TRINITY_WEIGHTS = {
    "truth": 0.35,      # 眞
    "goodness": 0.35,   # 善
    "beauty": 0.20,     # 美
    "serenity": 0.08,   # 孝
    "eternity": 0.02,   # 永
}


def calculate_trinity_score(
    truth: float,
    goodness: float,
    beauty: float,
    serenity: float = 1.0,
    eternity: float = 1.0,
) -> float:
    """Calculate Trinity Score from pillar values.

    Args:
        truth: Technical accuracy score (0-1)
        goodness: Security/stability score (0-1)
        beauty: Code clarity score (0-1)
        serenity: UX score (0-1), default 1.0
        eternity: Maintainability score (0-1), default 1.0

    Returns:
        Trinity Score as percentage (0-100)
    """
    score = (
        TRINITY_WEIGHTS["truth"] * truth
        + TRINITY_WEIGHTS["goodness"] * goodness
        + TRINITY_WEIGHTS["beauty"] * beauty
        + TRINITY_WEIGHTS["serenity"] * serenity
        + TRINITY_WEIGHTS["eternity"] * eternity
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
