# Trinity Score: 91.0 (Established by Chancellor)
"""RAG Evaluation Framework (RAGAS-style metrics)
Specialized evaluation for Retrieval-Augmented Generation systems.

2026 Best Practices Implementation:
- Faithfulness: Does response match retrieved context?
- Context Relevancy: Is retrieved context relevant to query?
- Answer Relevancy: Does answer address the question?
- Context Precision: Are retrieved docs appropriately ranked?

Philosophy:
- 眞 (Truth): Verify factual grounding in sources
- 善 (Goodness): Prevent hallucination
- 美 (Beauty): Clear, coherent responses
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RAGEvalResult:
    """RAG evaluation result with RAGAS metrics."""

    query: str
    answer: str
    contexts: list[str]
    faithfulness: float
    context_relevancy: float
    answer_relevancy: float
    overall_score: float
    is_hallucination: bool
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class RAGEvaluator:
    """RAG Evaluation Framework using RAGAS-style metrics.

    Implements:
    1. Faithfulness: Answer grounded in context
    2. Context Relevancy: Retrieved context matches query
    3. Answer Relevancy: Answer addresses the question
    4. Hallucination Detection: Identifies ungrounded claims
    """

    def __init__(self) -> None:
        self.name = "RAG Evaluator (龐統)"

        # Thresholds
        self.thresholds = {
            "faithfulness": 0.8,
            "context_relevancy": 0.7,
            "answer_relevancy": 0.75,
        }
        self.metrics = list(self.thresholds.keys())

        # Hallucination indicator phrases
        self.hallucination_indicators = [
            "as an ai",
            "i don't have access",
            "i cannot confirm",
            "based on my training",
            "i'm not sure but",
        ]

        # Statistics
        self._stats = {
            "evaluations_run": 0,
            "avg_faithfulness": 0.0,
            "hallucination_rate": 0.0,
        }

    def evaluate(
        self,
        query: str,
        answer: str,
        contexts: list[str],
    ) -> RAGEvalResult:
        """Evaluate RAG response quality.

        Args:
            query: User's question
            answer: Generated answer
            contexts: Retrieved context documents

        Returns:
            RAGEvalResult with all metrics
        """
        self._stats["evaluations_run"] += 1

        # 1. Faithfulness: Is answer grounded in contexts?
        faithfulness = self._compute_faithfulness(answer, contexts)

        # 2. Context Relevancy: Are contexts relevant to query?
        context_relevancy = self._compute_context_relevancy(query, contexts)

        # 3. Answer Relevancy: Does answer address the query?
        answer_relevancy = self._compute_answer_relevancy(query, answer)

        # 4. Hallucination Detection
        is_hallucination = self._detect_hallucination(answer, contexts, faithfulness)

        # Overall score
        overall = (faithfulness + context_relevancy + answer_relevancy) / 3

        # Penalize hallucination
        if is_hallucination:
            overall *= 0.5

        result = RAGEvalResult(
            query=query,
            answer=answer,
            contexts=contexts,
            faithfulness=faithfulness,
            context_relevancy=context_relevancy,
            answer_relevancy=answer_relevancy,
            overall_score=overall,
            is_hallucination=is_hallucination,
            details={
                "context_count": len(contexts),
                "answer_length": len(answer),
            },
        )

        self._update_stats(faithfulness, is_hallucination)
        self._persist_evaluation(result)

        logger.info(
            f"[{self.name}] RAG Eval: faithfulness={faithfulness:.2f}, "
            f"hallucination={is_hallucination}"
        )

        return result

    def _compute_faithfulness(
        self,
        answer: str,
        contexts: list[str],
    ) -> float:
        """Compute faithfulness score: how grounded is answer in contexts."""
        if not contexts:
            return 0.0

        combined_context = " ".join(contexts).lower()
        answer_sentences = self._split_sentences(answer)

        if not answer_sentences:
            return 0.0

        grounded_count = 0
        for sentence in answer_sentences:
            # Check if key terms from sentence appear in context
            words = [w for w in sentence.lower().split() if len(w) > 4]
            if not words:
                grounded_count += 1  # Short sentences are assumed grounded
                continue

            matches = sum(1 for w in words if w in combined_context)
            if matches / len(words) >= 0.3:
                grounded_count += 1

        return grounded_count / len(answer_sentences)

    def _compute_context_relevancy(
        self,
        query: str,
        contexts: list[str],
    ) -> float:
        """Compute context relevancy: how relevant are contexts to query."""
        if not contexts:
            return 0.0

        query_words = {w.lower() for w in query.split() if len(w) > 3}

        if not query_words:
            return 0.5  # Neutral for very short queries

        relevancy_scores = []
        for ctx in contexts:
            ctx_lower = ctx.lower()
            matches = sum(1 for w in query_words if w in ctx_lower)
            relevancy_scores.append(matches / len(query_words))

        return sum(relevancy_scores) / len(relevancy_scores)

    def _compute_answer_relevancy(
        self,
        query: str,
        answer: str,
    ) -> float:
        """Compute answer relevancy: does answer address the query."""
        query_words = {w.lower() for w in query.split() if len(w) > 3}
        answer_lower = answer.lower()

        if not query_words:
            return 0.5

        # Check if query terms appear in answer
        matches = sum(1 for w in query_words if w in answer_lower)
        term_coverage = matches / len(query_words)

        # Check if answer has reasonable length
        length_score = min(1.0, len(answer) / 50)  # Expect at least 50 chars

        return (term_coverage + length_score) / 2

    def _detect_hallucination(
        self,
        answer: str,
        contexts: list[str],
        faithfulness: float,
    ) -> bool:
        """Detect if answer contains hallucinated content."""
        answer_lower = answer.lower()

        # Check for explicit uncertainty phrases
        for indicator in self.hallucination_indicators:
            if indicator in answer_lower:
                return False  # Agent admits uncertainty, not hallucination

        # Low faithfulness with high confidence = hallucination
        if faithfulness < 0.3 and "definitely" in answer_lower:
            return True

        if faithfulness < 0.2 and len(answer) > 100:
            return True  # Long answer with no grounding

        # Check for specific claims not in context
        if contexts:
            combined = " ".join(contexts).lower()

            # Look for numbers/dates in answer not in context
            answer_numbers = set(re.findall(r"\b\d+\b", answer))
            context_numbers = set(re.findall(r"\b\d+\b", combined))

            ungrounded_numbers = answer_numbers - context_numbers
            if len(ungrounded_numbers) > 2:
                return True  # Many ungrounded numbers

        return faithfulness < self.thresholds["faithfulness"]

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _update_stats(self, faithfulness: float, is_hallucination: bool) -> None:
        """Update running statistics."""
        n = self._stats["evaluations_run"]
        old_avg = self._stats["avg_faithfulness"]
        self._stats["avg_faithfulness"] = ((old_avg * (n - 1)) + faithfulness) / n

        old_hall = self._stats["hallucination_rate"]
        hall_count = int(old_hall * (n - 1)) + (1 if is_hallucination else 0)
        self._stats["hallucination_rate"] = hall_count / n

    def _persist_evaluation(self, result: RAGEvalResult) -> None:
        """Persist RAG evaluation for audit."""
        try:
            eval_dir = Path(__file__).parent.parent.parent.parent / "docs" / "ssot" / "evaluations"
            eval_dir.mkdir(parents=True, exist_ok=True)

            import json

            log_file = eval_dir / "rag_evaluations.jsonl"
            entry = {
                "query": result.query[:100],
                "faithfulness": result.faithfulness,
                "context_relevancy": result.context_relevancy,
                "answer_relevancy": result.answer_relevancy,
                "overall_score": result.overall_score,
                "is_hallucination": result.is_hallucination,
                "timestamp": result.timestamp,
            }

            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.warning(f"Failed to persist RAG evaluation: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get RAG evaluation statistics."""
        return self._stats.copy()


# Singleton
rag_evaluator = RAGEvaluator()


# Convenience functions
def evaluate_rag_response(
    query: str,
    answer: str,
    contexts: list[str],
) -> RAGEvalResult:
    """Evaluate a RAG response."""
    return rag_evaluator.evaluate(query, answer, contexts)


def is_response_faithful(
    answer: str,
    contexts: list[str],
    threshold: float = 0.8,
) -> bool:
    """Quick check if response is faithful to contexts."""
    result = rag_evaluator.evaluate("", answer, contexts)
    return result.faithfulness >= threshold
