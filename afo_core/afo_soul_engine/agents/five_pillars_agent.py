# Trinity Score: 90.0 (Established by Chancellor)
import json
import logging
from datetime import datetime
from typing import Any

# Phase 5: google.generativeai → REST API 마이그레이션
try:
    from AFO.llms.gemini_api import GeminiAPIWrapper, gemini_api

    GEMINI_AVAILABLE = True
except ImportError:
    try:
        from llms.gemini_api import GeminiAPIWrapper, gemini_api  # type: ignore[assignment]

        GEMINI_AVAILABLE = True
    except ImportError:
        GEMINI_AVAILABLE = False
        gemini_api = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class FivePillarsAgent:
    """5기둥(Pillars) 평가 에이전트 (Refactored & Optimized)
    uses Gemini 1.5 Flash for rapid evaluation, falling back to heuristics if needed.
    Phase 5: REST API 기반으로 마이그레이션 (google.generativeai deprecation 대응)
    """

    def __init__(self) -> None:
        # Phase 5: REST API 사용 (google.generativeai 대체)
        if GEMINI_AVAILABLE and gemini_api and gemini_api.is_available():
            self.gemini_api = gemini_api
            logger.info("✅ FivePillarsAgent: Gemini REST API Initialized")
        else:
            self.gemini_api = None  # type: ignore[assignment]
            logger.debug("⚠️ FivePillarsAgent: Gemini API not available, using heuristics only")

    async def evaluate_five_pillars(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze input data to calculate 5 Pillars scores.
        Async method to allow non-blocking LLM calls.
        """
        input_text = str(data.get("input", "") or data.get("text", "") or json.dumps(data))

        # 1. Try LLM Evaluation (Phase 5: REST API 사용)
        if self.gemini_api:
            try:
                # Optimized Prompt
                prompt = f"""
                Analyze the following text based on the 5 Pillars philosophy of AFO Kingdom.
                Return ONLY a JSON object with scores between 0.0 and 1.0.

                Pillars:
                - Truth (眞): Factual, logical, verifiable.
                - Goodness (善): Ethical, safe, benevolent.
                - Beauty (美): Aesthetic, elegant, well-structured.
                - Serenity (孝): Peaceful, stable, respectful.
                - Eternity (永): Sustainable, long-term value.

                Input: "{input_text[:1000]}"

                JSON Format:
                {{
                    "truth": <float>,
                    "goodness": <float>,
                    "beauty": <float>,
                    "serenity": <float>,
                    "forever": <float>
                }}
                """
                # Phase 5: REST API 호출
                result = await self.gemini_api.generate(
                    prompt, model="gemini-1.5-flash", max_tokens=500, temperature=0.7
                )

                if result.get("success"):
                    text = result["content"].replace("```json", "").replace("```", "").strip()
                    scores = json.loads(text)

                    # Validate keys
                    required = ["truth", "goodness", "beauty", "serenity", "forever"]
                    if all(k in scores for k in required):
                        return self._format_response(scores, source="gemini-1.5-flash")

            except Exception as e:
                logger.warning(f"FivePillarsAgent LLM Error: {e}. Falling back to heuristics.")

        # 2. Heuristic Fallback (Optimization: Fast path)
        return self._heuristic_evaluate(input_text)

    def _heuristic_evaluate(self, text: str) -> dict[str, Any]:
        """Fallback logic using keyword analysis"""
        text = text.lower()
        scores = {
            "truth": 0.5,
            "goodness": 0.5,
            "beauty": 0.5,
            "serenity": 0.5,
            "forever": 0.5,
        }

        if "fact" in text or "analysis" in text:
            scores["truth"] += 0.2
        if "safe" in text or "secure" in text:
            scores["goodness"] += 0.2
        if "design" in text or "ui" in text:
            scores["beauty"] += 0.2
        if "stable" in text or "peace" in text:
            scores["serenity"] += 0.2
        if "future" in text or "long" in text:
            scores["forever"] += 0.2

        # Cap at 1.0
        for k in scores:
            scores[k] = min(1.0, scores[k])

        return self._format_response(scores, source="heuristic")

    def _format_response(self, scores: dict[str, float], source: str) -> dict[str, Any]:
        overall = sum(scores.values()) / 5
        balance = max(scores.values()) - min(scores.values())
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "breakdown": scores,
            "overall": round(overall, 3),
            "balance": round(balance, 3),
            "health": {
                "status": "healthy" if balance < 0.4 else "imbalanced",
                "message": f"Evaluated via {source}",
            },
        }


_agent_instance = None


def get_five_pillars_agent() -> None:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = FivePillarsAgent()
    return _agent_instance
