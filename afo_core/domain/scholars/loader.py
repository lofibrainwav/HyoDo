from __future__ import annotations

from pathlib import Path

"""Scholars Pattern Loader - AFO Kingdom Integration Layer.

Loads domain-specific strategic patterns from Amp-Skills for Scholar assessment.
"""


BASE_DIR = Path(__file__).parent / "patterns"


def get_scholar_patterns(scholar_name: str) -> str:
    """Load patterns for a specific scholar.

    Args:
        scholar_name: Name of the scholar (zilong, lushun, simayi, etc.)

    Returns:
        The content of the pattern file or empty string if not found.
    """
    file_path = BASE_DIR / f"{scholar_name.lower()}_dev.md"
    if not file_path.exists():
        file_path = BASE_DIR / f"{scholar_name.lower()}_vibe.md"

    if not file_path.exists():
        return ""

    with open(file_path, encoding="utf-8") as f:
        return f.read()
