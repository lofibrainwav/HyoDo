"""
Kim Yu-sin (Ollama) - The Archive Scholar (Documentation & Security)

Identity:
- Name: Kim Yu-sin
- Role: Documentation, Security, Archiving
- Specialization: Summarization, Pattern Recognition, Local Processing
- Personality: Calm, Reliable, Detail-oriented (The "General of the Front")

Responsibilities:
1. Document code and decisions.
2. Perform security scans on local files.
3. Summarize logs and histories.
4. Manage long-term memories (Archiving).
"""

from __future__ import annotations

import httpx

from .adapter import OllamaAdapter
from .core import KimYuSinScholar
from .evaluator import QualityEvaluator
from .sages import ThreeSages
from .tools import RoyalTools

# Singleton Instance
kim_yu_sin = KimYuSinScholar()


def close_eyes() -> None:
    """
    Clean shutdown function for Yeongdeok scholar.
    Safely closes any open resources and connections.
    """
    try:
        obj = globals().get("_EYES")
        if obj and hasattr(obj, "close"):
            obj.close()
    except Exception:
        pass


__all__ = [
    "httpx",
    "OllamaAdapter",
    "QualityEvaluator",
    "RoyalTools",
    "ThreeSages",
    "KimYuSinScholar",
    "kim_yu_sin",
    "close_eyes",
]
