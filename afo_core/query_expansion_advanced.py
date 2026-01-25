# Trinity Score: 90.0 (Established by Chancellor)
"""Query Expansion Advanced for AFO Kingdom (Phase 2.3)
Expands user queries to improve RAG retrieval.
"""

import re


class QueryExpander:
    """Advanced Query Expander for RAG systems.
    Generates expanded queries for better document retrieval.
    """

    def __init__(self, expansion_factor: int = 3) -> None:
        self.expansion_factor = expansion_factor
        self.synonyms: dict[str, list[str]] = {
            # Korean tech terms
            "api": ["인터페이스", "엔드포인트", "서비스"],
            "서버": ["백엔드", "서비스", "시스템"],
            "데이터베이스": ["db", "저장소", "데이터"],
            "에러": ["오류", "버그", "문제"],
            "성능": ["속도", "효율", "최적화"],
            # English terms
            "query": ["search", "request", "question"],
            "error": ["bug", "issue", "problem"],
            "performance": ["speed", "optimization", "efficiency"],
        }

    def expand(self, query: str) -> list[str]:
        """Expand a query into multiple variations.

        Args:
            query: Original user query

        Returns:
            List of expanded queries

        """
        expanded = [query]  # Always include original

        # Add synonym expansions
        words = query.lower().split()
        for word in words:
            if word in self.synonyms:
                for synonym in self.synonyms[word][:2]:
                    new_query = query.lower().replace(word, synonym)
                    if new_query not in expanded:
                        expanded.append(new_query)

        # Add question variations
        if not query.endswith("?"):
            expanded.append(f"{query}?")

        # Add context-aware expansions
        if "어떻게" not in query and "how" not in query.lower():
            expanded.append(f"어떻게 {query}")

        if "왜" not in query and "why" not in query.lower():
            expanded.append(f"왜 {query}")

        return expanded[: self.expansion_factor + 1]

    def get_keywords(self, query: str) -> list[str]:
        """Extract important keywords from query."""
        # Remove common stop words
        stop_words = {
            "은",
            "는",
            "이",
            "가",
            "을",
            "를",
            "의",
            "에",
            "로",
            "a",
            "the",
            "is",
            "are",
        }
        words = re.findall(r"\w+", query.lower())
        return [w for w in words if w not in stop_words and len(w) > 1]


# Default instance
query_expander = QueryExpander()


def expand_query(query: str) -> list[str]:
    """Convenience function for query expansion."""
    return query_expander.expand(query)
