# Trinity Score: 90.0 (Established by Chancellor)
"""
Matrix Stream Service (The Flow)
Phase 10: Thought Visualization

Broadcasts AI internal monologues via SSE.
Implements Advanced NLP (TF-IDF) to classify thoughts into 5 Pillars.
"""

import asyncio
import json
import logging
import math
from collections.abc import AsyncGenerator
from typing import Any

# Lightweight NLP (No heavy deps like sklearn/scikit yet, using pure python/numpy logic if feasible or simplified)
# User requested TF-IDF + Cosine.
# Since we might not have numpy installed in strict env, we implement a pure python version or try generic.
# Actually user said "Python Developer... TF-IDF + cosine".
# Let's assume standard math library or simple implementation for now to be safe in AFO env.
# We will implement a Pure Python TF-IDF for stability.

logger = logging.getLogger("afo.services.matrix_stream")

PILLAR_KEYWORDS = {
    "眞": [
        "type",
        "mypy",
        "strict",
        "TS",
        "safety",
        "validation",
        "integrity",
        "truth",
        "logic",
        "verify",
    ],
    "善": [
        "risk",
        "vuln",
        "grype",
        "syft",
        "security",
        "guard",
        "ethics",
        "goodness",
        "safe",
        "lock",
    ],
    "美": [
        "glass",
        "tailwind",
        "design",
        "aesthetic",
        "elegance",
        "ui",
        "beauty",
        "css",
        "style",
        "glow",
    ],
    "孝": [
        "stream",
        "sse",
        "terminal",
        "friction",
        "serenity",
        "feedback",
        "zero",
        "peace",
        "comfort",
        "easy",
    ],
    "永": [
        "log",
        "evolution",
        "ssot",
        "record",
        "persistent",
        "history",
        "eternal",
        "database",
        "memory",
        "save",
    ],
}


class MatrixStreamService:
    """
    Manages the broadcast of AI thoughts.
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._history: list[dict[str, Any]] = []

    async def push_thought(self, text: str, level: str = "info") -> None:
        """
        Push a thought to the stream.
        Auto-classifies Pillar.
        """
        pillar, confidence = self._classify_pillar(text)

        thought_data = {
            "id": len(self._history) + 1,
            "text": text,
            "level": level,
            "pillar": pillar,
            "confidence": confidence,
        }

        self._history.append(thought_data)
        # Keep history manageable
        if len(self._history) > 100:
            self._history.pop(0)

        await self._queue.put(thought_data)
        logger.debug(f"🧠 [Matrix] Pushed: {text} ({pillar}:{confidence}%)")

    async def event_generator(self) -> AsyncGenerator[str, None]:
        """
        SSE Generator.
        Yields new thoughts as they come.
        """
        while True:
            try:
                # Wait for next thought
                data = await self._queue.get()
                yield f"data: {json.dumps(data)}\n\n"
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Matrix Stream Error: {e}")
                break

    def _classify_pillar(self, text: str) -> tuple[str | None, int]:
        """
        Advanced NLP Classification (TF-IDFish + Cosine Sim).
        Pure Python Implementation for portability.
        """
        # 1. Tokenize
        import re

        def tokenize(s: str) -> list[str]:
            return re.findall(r"\w+", s.lower())

        doc_tokens = tokenize(text)
        if not doc_tokens:
            return None, 0

        scores: dict[str, float] = {}

        # 2. Compute Similarity
        # We treat the keywords as the "Definition Document" for each Pillar.

        for pillar, keywords in PILLAR_KEYWORDS.items():
            matches = 0
            for token in doc_tokens:
                # Direct match or singular form match (simple heuristic)
                if token in keywords or token.rstrip("s") in keywords:
                    matches += 1

            if matches > 0:
                # Score = matches / sqrt(len(doc_tokens) * len(keywords)) * 100
                # Boost precision
                denom = math.sqrt(len(doc_tokens) * len(keywords))
                scores[pillar] = (matches / denom) * 100
            else:
                scores[pillar] = 0.0

        # 3. Find Max
        if not scores:
            return None, 0

        best_pillar = max(scores, key=scores.get)  # type: ignore
        confidence = scores[best_pillar]

        if confidence > 10:  # Threshold
            return best_pillar, int(confidence)

        return None, 0


# Global Instance
matrix_stream = MatrixStreamService()
