# Trinity Score: 90.0 (Established by Chancellor)
"""
Sejong Research Institute (Phase 14)
Active Research & Adoption System (King Sejong's Spirit)
"널리 구하고(Research), 시시비비를 가려(Validate), 우리 것으로 만든다(Adopt)"
"""

import json
import logging
from datetime import datetime
from typing import Any

from AFO.services.trinity_calculator import trinity_calculator
from AFO.utils.trinity_type_validator import validate_with_trinity

logger = logging.getLogger("AFO.Sejong")

KNOWLEDGE_BASE_PATH = "knowledge_base.jsonl"


class SejongResearcher:
    """
    Sejong Researcher: The Kingdom's Chief Scholar.
    Responsibility: Continuous accumulation of validated knowledge.
    """

    def __init__(self) -> None:
        pass

    @validate_with_trinity
    def research_topic(self, topic: str) -> dict[str, Any]:
        """
        Step 1: Research (널리 구한다)
        Simulates active research using search tools (or mocks if offline).
        """
        logger.info(f"🔭 [Sejong] Researching topic: {topic}")

        # Mocking search results for now (Integration point for Brave Search)
        # In a real scenario, this would call a search API.
        findings = {
            "topic": topic,
            "summary": f"Latest insights on {topic}",
            "source": "Royal Library & Web Archives",
            "content": f"Advanced techniques for {topic} include strict type checking and modular architecture.",
            "timestamp": datetime.now().isoformat(),
        }
        return findings

    @validate_with_trinity
    def sisi_bibi_validation(self, data: dict[str, Any]) -> float:
        """
        Step 2: Sisi-Bibi (시시비비를 가린다)
        Validate using Trinity Score (Truth=Fact, Goodness=Risk).
        """
        logger.info(f"⚖️ [Sejong] Validating knowledge: {data.get('topic')}")

        # Construct Trinity Context
        # Truth: Is the source reliable? (Mocked as 1.0)
        # Goodness: Is it safe? (Risk check)

        # Mocking generic validation logic
        risk_level = 0.0
        if "exploit" in data.get("content", "").lower():
            risk_level = 1.0

        valid_structure = True

        raw_scores = trinity_calculator.calculate_raw_scores(
            {
                "valid_structure": valid_structure,
                "risk_level": risk_level,
                "narrative": "full",  # Beauty
                "valid": True,
            }
        )

        score = trinity_calculator.calculate_trinity_score(raw_scores)
        logger.info(f"⚖️ [Sejong] Validation Score: {score}")
        return float(score)

    @validate_with_trinity
    def adopt_knowledge(self, data: dict[str, Any], score: float) -> bool:
        """
        Step 3: Adopt (우리 것으로 만든다)
        Save validated knowledge to persistent storage.
        """
        if score < 90.0:
            logger.warning(
                f"🚫 [Sejong] Rejected knowledge (Score {score} < 90): {data.get('topic')}"
            )
            return False

        logger.info(f"📜 [Sejong] Adopting knowledge: {data.get('topic')}")

        entry = {
            "data": data,
            "validation_score": score,
            "adopted_at": datetime.now().isoformat(),
            "status": "APPROVED",
        }

        try:
            with open(KNOWLEDGE_BASE_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            return True
        except Exception as e:
            logger.error(f"Failed to save knowledge: {e}")
            return False


# Singleton Instance
sejong = SejongResearcher()
