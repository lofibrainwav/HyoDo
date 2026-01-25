"""
Vector Memory Service
Provides persistent vector storage for Julie's knowledge using ChromaDB.
"""

import logging
import os
from typing import Any

try:
    import chromadb

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)

# Constants
# Store in packages/afo-core/chroma_db
CHROMA_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db"
)
COLLECTION_NAME = "julie_knowledge"


class VectorMemoryService:
    def __init__(self) -> None:
        self.client = None
        self.collection = None
        self._initialize()

    def _initialize(self) -> None:
        if not CHROMA_AVAILABLE:
            logger.warning("ChromaDB library not found. Vector Memory disabled.")
            return

        try:
            # Persistent Client
            self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

            # Get or Create Collection
            # Uses default embedding function (all-MiniLM-L6-v2) automatically if not specified
            self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
            logger.info(f"Vector Memory initialized at {CHROMA_DB_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None

    async def add_text(
        self, text: str, metadata: dict[str, Any], doc_id: str | None = None
    ) -> bool:
        """Adds text to the vector store."""
        if not self.collection:
            return False

        try:
            # Generate ID if not provided
            if not doc_id:
                import uuid

                doc_id = str(uuid.uuid4())

            # Filter metadata to ensure flat structure (Chroma requirement)
            clean_metadata = {}
            for k, v in metadata.items():
                if v is None:
                    continue
                if isinstance(v, (str, int, float, bool)):
                    clean_metadata[k] = v
                else:
                    clean_metadata[k] = str(v)

            self.collection.add(documents=[text], metadatas=[clean_metadata], ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Failed to add text to memory: {e}")
            return False

    async def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Searches the vector store."""
        if not self.collection:
            return []

        try:
            results = self.collection.query(query_texts=[query], n_results=n_results)

            # Reformat results
            hits = []
            if results["ids"]:
                count = len(results["ids"][0])
                for i in range(count):
                    hit = {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    }
                    hits.append(hit)
            return hits
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []


vector_memory_service = VectorMemoryService()
