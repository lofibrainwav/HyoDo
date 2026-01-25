"""
Ragas Evaluator Skill Tests

Tests for RAG quality evaluation using Ragas framework.

Metrics: Faithfulness, Answer Relevancy, Context Precision, Context Recall
"""

import pytest

from AFO.evaluation.rag_evaluator import RAGEvaluator


class TestRagasEvaluator:
    """RagasEvaluator Tests"""

    def test_ragas_evaluator_init(self) -> None:
        """RagasEvaluator should initialize successfully."""

        evaluator = RAGEvaluator()

        assert evaluator is not None, "Evaluator should be initialized"
        assert hasattr(evaluator, "metrics"), "Evaluator should have metrics attribute"

    def test_ragas_metrics_exist(self) -> None:
        """RagasEvaluator metrics should be defined."""

        evaluator = RAGEvaluator()

        expected_metrics = [
            "faithfulness",
            "answer_relevancy",
            "context_relevancy",
        ]

        for metric in expected_metrics:
            assert metric in evaluator.metrics, f"Metrics should contain {metric}"

    def test_ragas_evaluate_signature(self) -> None:
        """RagasEvaluator evaluate method should have correct signature."""

        evaluator = RAGEvaluator()

        assert hasattr(evaluator, "evaluate"), "Evaluator should have evaluate method"
