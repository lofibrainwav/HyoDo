# Trinity Score: 91.0 (Established by Chancellor)
"""Agentic RAG Enhancement Module (TICKET-100)
Advanced RAG with agent reasoning for improved retrieval accuracy.

LangGraph Agentic RAG Patterns:
1. Query Rewriting: Agent reasons about and improves user queries
2. Document Relevance Grading: Score and filter retrieved documents
3. Web Search Fallback: Fall back to web when local knowledge insufficient
4. Hallucination Self-Correction: Detect and correct hallucinations

Philosophy:
- 眞 (Truth): Only return verified, relevant information
- 善 (Goodness): Admit uncertainty rather than hallucinate
- 美 (Beauty): Seamless user experience with transparent reasoning
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RetrievalDecision(Enum):
    """Decision after evaluating retrieved documents."""

    USE_RETRIEVAL = "use_retrieval"  # Docs are relevant, use them
    REWRITE_QUERY = "rewrite_query"  # Docs not relevant, rewrite query
    WEB_SEARCH = "web_search"  # Fall back to web search
    ADMIT_UNKNOWN = "admit_unknown"  # Cannot find reliable answer


@dataclass
class RetrievedDocument:
    """A document retrieved from the knowledge base."""

    content: str
    source: str
    relevance_score: float
    metadata: dict[str, Any] = field(default_factory=lambda: {})


@dataclass
class AgenticRAGResult:
    """Result from agentic RAG pipeline."""

    answer: str
    sources: list[RetrievedDocument]
    decision_path: list[str]  # Trace of decisions made
    confidence: float
    was_corrected: bool = False
    original_query: str = ""
    rewritten_query: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class AgenticRAG:
    """Agentic RAG with reasoning and self-correction.

    Implements 2026 LangGraph best practices:
    1. Query rewriting with agent reasoning
    2. Document relevance grading
    3. Web search fallback
    4. Hallucination self-correction
    """

    def __init__(self) -> None:
        self.name = "Agentic RAG (華佗)"

        # Thresholds for decision making
        self.thresholds = {
            "relevance_min": 0.6,  # Minimum relevance score to use doc
            "confidence_min": 0.7,  # Minimum confidence to return answer
            "rewrite_attempts_max": 2,  # Max query rewrite attempts
            "web_search_relevance": 0.5,  # Trigger web search below this
        }

        # Hallucination detection patterns
        self.hallucination_patterns = [
            "I think",
            "probably",
            "might be",
            "I'm not sure",
            "as far as I know",
            "based on my training",
        ]

        self._query_history: list[dict[str, Any]] = []

    async def query(
        self,
        user_query: str,
        context: dict[str, Any] | None = None,
    ) -> AgenticRAGResult:
        """Execute agentic RAG pipeline.

        Args:
            user_query: The user's question
            context: Optional context (user info, session, etc.)

        Returns:
            AgenticRAGResult with answer, sources, and decision trace
        """
        context = context or {}
        decision_path: list[str] = []

        logger.info(f"[{self.name}] Processing query: {user_query[:100]}...")
        decision_path.append(f"Received query: {user_query[:50]}...")
        relevant_docs: list[RetrievedDocument] = []

        # Step 1: Analyze and potentially rewrite query
        analyzed_query, reasoning = await self._analyze_query(user_query)
        decision_path.append(f"Query analysis: {reasoning}")

        current_query = analyzed_query
        rewrite_count = 0

        while rewrite_count < self.thresholds["rewrite_attempts_max"]:
            # Step 2: Retrieve documents
            documents = await self._retrieve_documents(current_query)
            decision_path.append(f"Retrieved {len(documents)} documents")

            # Step 3: Grade document relevance
            relevant_docs = self._grade_documents(documents, current_query)
            avg_relevance = (
                sum(d.relevance_score for d in relevant_docs) / len(relevant_docs)
                if relevant_docs
                else 0
            )
            decision_path.append(f"Relevance grade: {avg_relevance:.2f}")

            # Step 4: Decide next action
            decision = self._decide_action(relevant_docs, avg_relevance)
            decision_path.append(f"Decision: {decision.value}")

            if decision == RetrievalDecision.USE_RETRIEVAL:
                break
            elif decision == RetrievalDecision.REWRITE_QUERY:
                current_query = await self._rewrite_query(current_query, documents)
                decision_path.append(f"Rewrote query to: {current_query[:50]}...")
                rewrite_count += 1
            elif decision == RetrievalDecision.WEB_SEARCH:
                web_docs = await self._web_search_fallback(current_query)
                relevant_docs.extend(web_docs)
                decision_path.append(f"Added {len(web_docs)} web results")
                break
            else:  # ADMIT_UNKNOWN
                return AgenticRAGResult(
                    answer="I don't have reliable information to answer this question.",
                    sources=[],
                    decision_path=decision_path,
                    confidence=0.0,
                    original_query=user_query,
                    rewritten_query=(current_query if current_query != user_query else None),
                )

        # Step 5: Generate answer from relevant documents
        answer, confidence = await self._generate_answer(current_query, relevant_docs)
        decision_path.append(f"Generated answer with confidence: {confidence:.2f}")

        # Step 6: Check for hallucinations and self-correct
        corrected_answer, was_corrected = await self._check_and_correct(
            answer, relevant_docs, current_query
        )
        if was_corrected:
            decision_path.append("Self-correction applied")

        result = AgenticRAGResult(
            answer=corrected_answer,
            sources=relevant_docs,
            decision_path=decision_path,
            confidence=confidence,
            was_corrected=was_corrected,
            original_query=user_query,
            rewritten_query=current_query if current_query != user_query else None,
        )

        # Persist result for analysis
        self._persist_result(result)

        return result

    async def _analyze_query(self, query: str) -> tuple[str, str]:
        """Analyze query and determine if it needs modification.

        Returns:
            Tuple of (modified_query, reasoning)
        """
        # Simple analysis - in production would use LLM
        query_lower = query.lower()

        # Check for ambiguous queries
        if len(query.split()) < 3:
            return query, "Query too short, keeping as-is"

        # Check for common query patterns that need expansion
        if "what is" in query_lower or "who is" in query_lower:
            return query, "Definition query detected, keeping as-is"

        if "how to" in query_lower:
            return query, "How-to query detected, keeping as-is"

        return query, "Query appears well-formed"

    async def _retrieve_documents(self, query: str) -> list[RetrievedDocument]:
        """Retrieve documents from knowledge base.

        Note: This is a placeholder - in production would use actual vector search.
        """
        # Placeholder - would integrate with existing RAG infrastructure
        # For now, return mock documents for demonstration

        logger.info(f"[{self.name}] Retrieving documents for: {query[:50]}...")

        # In production, this would call:
        # - Qdrant vector search
        # - pgvector similarity search
        # - Or existing RAG pipeline

        return []  # Return empty - actual implementation would populate

    def _grade_documents(
        self, documents: list[RetrievedDocument], query: str
    ) -> list[RetrievedDocument]:
        """Grade documents for relevance to query.

        Returns:
            List of documents that meet relevance threshold
        """
        relevant: list[RetrievedDocument] = []

        for doc in documents:
            # In production, would use cross-encoder or LLM for grading
            # Simple keyword overlap for now
            query_terms = set(query.lower().split())
            doc_terms = set(doc.content.lower().split())

            overlap = len(query_terms & doc_terms) / max(len(query_terms), 1)
            doc.relevance_score = min(overlap * 2, 1.0)  # Scale up

            if doc.relevance_score >= self.thresholds["relevance_min"]:
                relevant.append(doc)

        relevant.sort(key=lambda d: d.relevance_score, reverse=True)
        return relevant

    def _decide_action(
        self, docs: list[RetrievedDocument], avg_relevance: float
    ) -> RetrievalDecision:
        """Decide what action to take based on retrieval quality."""

        if not docs:
            return RetrievalDecision.WEB_SEARCH

        if avg_relevance >= self.thresholds["relevance_min"]:
            return RetrievalDecision.USE_RETRIEVAL

        if avg_relevance >= self.thresholds["web_search_relevance"]:
            return RetrievalDecision.REWRITE_QUERY

        return RetrievalDecision.WEB_SEARCH

        """Rewrite query to improve retrieval.

        Uses failed documents to understand what went wrong.
        """
        # In production, would use LLM for intelligent rewriting
        # Simple expansion for now

        # Add context words if query is short
        if len(query.split()) < 5:
            return f"detailed explanation of {query}"

        # Try adding "AFO Kingdom" context if not present
        if "afo" not in query.lower():
            return f"{query} in AFO Kingdom system"

        return query

    async def _web_search_fallback(self, query: str) -> list[RetrievedDocument]:
        """Fall back to web search when local knowledge is insufficient.

        Note: Placeholder - would integrate with web search API.
        """
        logger.info(f"[{self.name}] Web search fallback for: {query[:50]}...")

        # In production, would use:
        # - Brave Search API
        # - DuckDuckGo API
        # - Or other web search integration

        return []

    async def _generate_answer(
        self, query: str, docs: list[RetrievedDocument]
    ) -> tuple[str, float]:
        """Generate answer from retrieved documents.

        Returns:
            Tuple of (answer, confidence_score)
        """
        if not docs:
            return "I couldn't find relevant information to answer your question.", 0.3

        # In production, would use LLM with retrieved context
        # Simple concatenation for demonstration

        context = "\n".join(d.content[:500] for d in docs[:3])
        answer = f"Based on the available information: {context[:200]}..."

        confidence = min(sum(d.relevance_score for d in docs) / len(docs), 1.0)

        return answer, confidence

    async def _check_and_correct(
        self,
        answer: str,
        docs: list[RetrievedDocument],
        query: str,
    ) -> tuple[str, bool]:
        """Check for hallucinations and self-correct.

        Returns:
            Tuple of (corrected_answer, was_corrected)
        """
        answer_lower = answer.lower()

        # Check for hallucination patterns
        hallucination_detected = any(
            pattern.lower() in answer_lower for pattern in self.hallucination_patterns
        )

        if hallucination_detected:
            # Ground the answer more firmly in sources
            if docs:
                source_text = docs[0].content[:300]
                corrected = f"According to the sources: {source_text}..."
                return corrected, True
            else:
                return (
                    "I cannot provide a confident answer without reliable sources.",
                    True,
                )

        return answer, False

    def _persist_result(self, result: AgenticRAGResult) -> None:
        """Persist RAG result for analysis and improvement."""
        try:
            rag_dir = Path(__file__).parent.parent.parent.parent / "docs" / "ssot" / "rag"
            rag_dir.mkdir(parents=True, exist_ok=True)

            import json
            from dataclasses import asdict

            log_file = rag_dir / "agentic_rag_log.jsonl"
            with log_file.open("a", encoding="utf-8") as f:
                entry = asdict(result)
                # Convert sources to serializable format
                entry["sources"] = [
                    {
                        "content": s.content[:200],
                        "source": s.source,
                        "score": s.relevance_score,
                    }
                    for s in result.sources
                ]
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.warning(f"Failed to persist RAG result: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get RAG pipeline statistics."""
        return {
            "queries_processed": len(self._query_history),
            "thresholds": self.thresholds,
        }


# Singleton instance
agentic_rag = AgenticRAG()


async def query(user_query: str, **context: Any) -> AgenticRAGResult:
    """Convenience function for agentic RAG query."""
    return await agentic_rag.query(user_query, context)
