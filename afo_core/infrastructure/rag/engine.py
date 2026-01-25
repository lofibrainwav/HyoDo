"""
RAG Engine Adapter
Handles context retrieval for Retrieval-Augmented Generation.
Supports Hybrid Search strategy (mocked for now, intended for LanceDB/Upstash).
"""

import logging
from dataclasses import dataclass
from typing import Any

try:
    import lancedb

    LANCEDB_AVAILABLE = True
except ImportError:
    lancedb = None  # type: ignore[assignment, misc]
    LANCEDB_AVAILABLE = False

from config.settings import settings
from utils.embedding import get_embedding

logger = logging.getLogger(__name__)


@dataclass
class ContextChunk:
    """Represents a retrieved chunk of information."""

    content: str
    source: str
    score: float
    metadata: dict[str, Any]


class RAGEngine:
    """
    Engine for retrieving relevant context based on queries.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or settings.LANCEDB_PATH
        self._db = None

    def _get_db(self):
        """Lazy initialization of LanceDB."""
        if self._db is None:
            self._db = lancedb.connect(self.db_path)
        return self._db

    async def retrieve_context(
        self, query: str, filters: dict[str, Any] | None = None, limit: int = 3
    ) -> list[ContextChunk]:
        """
        Retrieves relevant context chunks from LanceDB using semantic search.
        """
        try:
            db = self._get_db()
            table_name = "kingdom_identity"  # Default table for now
            if table_name not in db.table_names():
                logger.warning(f"Table {table_name} not found in LanceDB.")
                return []

            table = db.open_table(table_name)

            # 1. Generate Query Embedding
            # LanceDB kingdom_identity table uses 768D (Ollama)
            query_vector = await get_embedding(query, target_dim=768)
            if not query_vector:
                logger.error("Failed to generate query embedding.")
                return []

            # 2. Perform Semantic Search
            search_builder = table.search(query_vector).limit(limit)

            # Apply filters if provided (LanceDB specific SQL-like filters)
            if filters:
                # Simple implementation: convert dict items to WHERE clause
                # e.g., {"source": "AGENTS.md"} -> "source = 'AGENTS.md'"
                where_clauses = []
                for k, v in filters.items():
                    if isinstance(v, str):
                        where_clauses.append(f"{k} = '{v}'")
                    else:
                        where_clauses.append(f"{k} = {v}")

                if where_clauses:
                    search_builder = search_builder.where(" AND ".join(where_clauses))

            results = search_builder.to_list()

            # 3. Transform to ContextChunk
            chunks = []
            for r in results:
                chunks.append(
                    ContextChunk(
                        content=r.get("content", ""),
                        source=r.get("source", "Unknown"),
                        score=1.0 - r.get("_distance", 1.0),  # Simple score conversion
                        metadata={
                            k: v
                            for k, v in r.items()
                            if k not in ["content", "source", "vector", "_distance"]
                        },
                    )
                )

            return chunks

        except Exception as e:
            logger.error(f"RAG Retrieval failed: {e}")
            return []
