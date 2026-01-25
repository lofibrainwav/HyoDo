# Trinity Score: 90.0 (Established by Chancellor)
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TrinityPillar(Enum):
    TRUTH = "Truth (眞)"
    GOODNESS = "Goodness (善)"
    BEAUTY = "Beauty (美)"
    SERENITY = "Serenity (孝)"
    ETERNITY = "Eternity (永)"


class EvaluationResult:
    def __init__(self, passed: bool, score: int, feedback: list[str]) -> None:
        self.passed = passed
        self.score = score
        self.feedback = feedback


class CriticAgent:
    """Jang Yeong-sil (장영실) - The Guardian of Truth & Strategy.
    Evaluates code and artifacts against the 41 Royal Rules.
    """

    def __init__(self) -> None:
        self.name = "Jang Yeong-sil"
        self.role = "Guardian Critic"
        logger.info(f"🛡️ Guardian {self.name} Awoken.")

    async def critique_code(self, code_snippet: str, context: str = "") -> EvaluationResult:
        """Analyzes code for Trinity Compliance.
        Currently a logic skeleton - will connect to LLM later.
        """
        feedback = []
        score = 100

        # 1. Truth Check (Type Safety)
        if "Any" in code_snippet or "# type: ignore" in code_snippet:
            feedback.append("❌ Truth: Avoid 'Any' or type ignores. Be precise.")
            score -= 10

        # 2. Goodness Check (Safety)
        if "os.system" in code_snippet or "subprocess.call" in code_snippet:
            feedback.append("⚠️ Goodness: Shell execution detected. Ensure safety gates.")
            score -= 5

        # 3. Beauty Check (Simulated)
        if len(code_snippet.splitlines()) > 200:
            feedback.append("🎨 Beauty: File too long. Consider modularizing.")
            score -= 5

        passed = score >= 90

        if passed:
            logger.info("✅ Jang Yeong-sil approves this code.")
        else:
            logger.warning(f"⚠️ Jang Yeong-sil requires improvements. Score: {score}")

        return EvaluationResult(passed, score, feedback)
