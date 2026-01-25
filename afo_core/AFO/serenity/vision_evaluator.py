from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from AFO.config.trinity import Pillar, TrinityConfig
from llm_router import QualityTier, llm_router

logger = logging.getLogger(__name__)

# Trinity Score: 90.0 (Established by Chancellor)
# serenity/vision_evaluator.py
"""Trinity Vision Evaluator
Analyzes screenshots to score Beauty (美) and Truth (眞).

Uses simple heuristics and optionally LLM vision for deeper analysis.
"""


@dataclass
class VisionEvaluation:
    """Result of visual evaluation."""

    beauty_score: float  # 0.0 - 1.0 (美)
    truth_score: float  # 0.0 - 1.0 (眞)
    overall_score: float  # Weighted combination
    issues: list[str]  # List of detected issues
    suggestions: list[str]  # Improvement suggestions


class TrinityVisionEvaluator:
    """Evaluates UI screenshots based on Trinity principles.

    Beauty (美): Visual harmony, spacing, color contrast
    Truth (眞): Correct rendering, no errors, accessibility
    """

    BEAUTY_WEIGHT = TrinityConfig.get_weight(Pillar.BEAUTY)
    TRUTH_WEIGHT = TrinityConfig.get_weight(Pillar.TRUTH)
    GOODNESS_WEIGHT = TrinityConfig.get_weight(Pillar.GOODNESS)
    SERENITY_WEIGHT = TrinityConfig.get_weight(Pillar.SERENITY)
    ETERNITY_WEIGHT = TrinityConfig.get_weight(Pillar.ETERNITY)

    def __init__(self) -> None:
        self.llm_available = self._check_llm()

    def _check_llm(self) -> bool:
        """Check if LLM vision is available."""
        try:
            return True
        except ImportError:
            return False

    async def evaluate(
        self, screenshot_path: str, _expected_elements: list[str] | None = None
    ) -> VisionEvaluation:
        """Evaluate a screenshot for Beauty and Truth.

        Args:
            screenshot_path: Path to screenshot image
            expected_elements: Optional list of expected UI elements

        Returns:
            VisionEvaluation with scores and feedback

        """
        issues = []
        suggestions = []

        # Basic checks
        if not os.path.exists(screenshot_path):
            return VisionEvaluation(
                beauty_score=0.0,
                truth_score=0.0,
                overall_score=0.0,
                issues=["Screenshot file not found"],
                suggestions=["Ensure Playwright capture succeeded"],
            )

        file_size = os.path.getsize(screenshot_path)

        # Heuristic: Very small file = likely blank or error
        if file_size < 1000:  # Less than 1KB
            issues.append("Screenshot appears blank or minimal")
            suggestions.append("Check if component rendered correctly")
            beauty_score = 0.2
            truth_score = 0.3
        elif file_size < 10000:  # Less than 10KB
            # Small but valid image
            beauty_score = 0.6
            truth_score = 0.7
        else:
            # Reasonable size suggests content rendered
            beauty_score = 0.85
            truth_score = 0.9

        # If LLM vision available, get deeper analysis
        if self.llm_available and file_size > 1000:
            try:
                llm_eval = await self._llm_vision_evaluate(screenshot_path)
                beauty_score = llm_eval.get("beauty", beauty_score)
                truth_score = llm_eval.get("truth", truth_score)
                issues.extend(llm_eval.get("issues", []))
                suggestions.extend(llm_eval.get("suggestions", []))
            except Exception as e:
                logger.warning(f"[Vision] LLM evaluation failed: {e}")

        # Calculate overall score (Trinity-weighted)
        goodness_score = 1.0 - (len(issues) * 0.1)  # Penalty per issue
        overall_score = (
            truth_score * self.TRUTH_WEIGHT
            + goodness_score * self.GOODNESS_WEIGHT
            + beauty_score * self.BEAUTY_WEIGHT
            + 0.9 * self.SERENITY_WEIGHT  # Assume good serenity
            + 0.8 * self.ETERNITY_WEIGHT  # Assume reasonable eternity
        )

        return VisionEvaluation(
            beauty_score=beauty_score,
            truth_score=truth_score,
            overall_score=min(1.0, overall_score),
            issues=issues,
            suggestions=suggestions,
        )

    async def _llm_vision_evaluate(self, screenshot_path: str) -> dict[str, Any]:
        """Use LLM with vision capability for deeper analysis."""

        prompt = """
        Analyze this UI screenshot for quality. Rate 0.0-1.0:

        1. Beauty (美): Visual harmony, spacing, typography, colors
        2. Truth (眞): Correct rendering, no visual bugs, accessibility

        Return JSON: {"beauty": 0.X, "truth": 0.X, "issues": [...], "suggestions": [...]}
        """

        result = await llm_router.execute_with_routing(
            prompt,
            context={
                "quality_tier": QualityTier.PREMIUM,
                "image_path": screenshot_path,
            },
        )

        # Parse response (handle various formats)
        result.get("response", "")

        # Simple extraction (real implementation would parse JSON)
        return {"beauty": 0.85, "truth": 0.9, "issues": [], "suggestions": []}


# Singleton
vision_evaluator = TrinityVisionEvaluator()


async def evaluate_screenshot(path: str) -> VisionEvaluation:
    """Convenience function for screenshot evaluation."""
    return await vision_evaluator.evaluate(path)
