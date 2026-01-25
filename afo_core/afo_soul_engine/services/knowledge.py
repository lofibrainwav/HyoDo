import logging
import os
import time
from pathlib import Path
from typing import Any

import lancedb
import pyarrow as pa

from config.settings import settings
from utils.embedding import get_ollama_embedding

logger = logging.getLogger(__name__)

# Context7 초기화 상태
_context7_initialized = False
_context7_document_count = 0


class KnowledgeService:
    """Context7 및 지식 베이스 관리 서비스"""

    @property
    def is_initialized(self) -> bool:
        return _context7_initialized

    @property
    def document_count(self) -> int:
        return _context7_document_count

    async def initialize_context7(self) -> tuple[bool, int]:
        """Context7 내부 초기화 로직"""
        global _context7_initialized, _context7_document_count

        db_path = settings.LANCEDB_PATH
        collection_name = "afokingdom_knowledge"

        try:
            # 1. LanceDB 디렉토리 생성
            os.makedirs(db_path, exist_ok=True)
            db = lancedb.connect(db_path)
            logger.info(f"[Context7] Connected to LanceDB at {db_path}")

            # 2. 임베딩 차원 감지
            test_embedding = await get_ollama_embedding("dimension test")
            embed_dim = len(test_embedding) if test_embedding else 768
            logger.info(f"[Context7] Detected embedding dimension: {embed_dim}")

            # 3. 테이블 생성 (없으면)
            if collection_name not in db.table_names():
                schema = pa.schema(
                    [
                        ("id", pa.string()),
                        ("content", pa.string()),
                        ("source", pa.string()),
                        ("vector", pa.list_(pa.float32(), embed_dim)),
                    ]
                )
                table = db.create_table(collection_name, schema=schema)
                logger.info(f"[Context7] Created table: {collection_name}")
            else:
                table = db.open_table(collection_name)
                logger.info(f"[Context7] Opened existing table: {collection_name}")

            # 4. 핵심 문서 인덱싱 (CLAUDE.md, AGENTS.md 등)
            kingdom_root = Path(settings.BASE_DIR)
            core_docs = [
                kingdom_root / "CLAUDE.md",
                kingdom_root / "AGENTS.md",
                kingdom_root / "docs" / "AFO_ROYAL_LIBRARY.md",
                kingdom_root / "packages" / "afo-core" / "CLAUDE.md",
            ]

            all_data = []
            for doc_path in core_docs:
                if not doc_path.exists():
                    logger.warning(f"[Context7] Skipping missing doc: {doc_path}")
                    continue

                try:
                    content = doc_path.read_text(encoding="utf-8")
                    paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 50]

                    for i, p in enumerate(paragraphs):
                        embedding = await get_ollama_embedding(p)
                        if not embedding or len(embedding) != embed_dim:
                            continue

                        all_data.append(
                            {
                                "id": f"{doc_path.name}_{i}",
                                "content": p,
                                "vector": embedding,
                                "source": doc_path.name,
                            }
                        )

                    logger.info(f"[Context7] Indexed: {doc_path.name} ({len(paragraphs)} chunks)")
                except Exception as e:
                    logger.error(f"[Context7] Failed to index {doc_path.name}: {e}")

            # 5. 데이터 삽입
            if all_data:
                table.add(all_data)
                _context7_document_count = table.count_rows()
                logger.info(
                    f"[Context7] Inserted {len(all_data)} chunks, total: {_context7_document_count}"
                )

            _context7_initialized = True
            return True, _context7_document_count

        except Exception as e:
            logger.error(f"[Context7] Initialization failed: {e}")
            return False, 0

    async def sync_knowledge(self, agent_id: str, knowledge: str) -> dict[str, Any]:
        """에이전트 지식 동기화"""
        db_path = settings.LANCEDB_PATH
        if not os.path.exists(db_path):
            raise Exception("Context7 not initialized")

        try:
            db = lancedb.connect(db_path)
            table = db.open_table("afokingdom_knowledge")

            embedding = await get_ollama_embedding(knowledge)
            if not embedding:
                raise Exception("Failed to generate embedding")

            doc_id = f"{agent_id}_{int(time.time())}"
            table.add(
                [
                    {
                        "id": doc_id,
                        "content": knowledge,
                        "vector": embedding,
                        "source": f"agent:{agent_id}",
                    }
                ]
            )

            return {
                "status": "synced",
                "document_id": doc_id,
                "agent_id": agent_id,
            }

        except Exception as e:
            logger.error(f"[Context7] Sync failed: {e}")
            raise

    async def query_knowledge(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """지식 검색"""
        try:
            embedding = await get_ollama_embedding(query)
            if not embedding:
                return []

            db_path = settings.LANCEDB_PATH
            if not os.path.exists(db_path):
                return []

            db = lancedb.connect(db_path)
            if "afokingdom_knowledge" not in db.table_names():
                return []

            table = db.open_table("afokingdom_knowledge")
            search_results = table.search(embedding).limit(top_k).to_list()

            return [
                {
                    "content": r.get("content", ""),
                    "source": r.get("source", ""),
                    "score": r.get("_distance", 0.0),
                }
                for r in search_results
            ]

        except Exception as e:
            logger.error(f"[Context7] Query failed: {e}")
            return []

    def get_status(self) -> dict[str, Any]:
        """상태 조회"""
        db_path = settings.LANCEDB_PATH
        db_exists = os.path.exists(db_path)
        document_count = 0

        if db_exists:
            try:
                db = lancedb.connect(db_path)
                if "afokingdom_knowledge" in db.table_names():
                    table = db.open_table("afokingdom_knowledge")
                    document_count = table.count_rows()
            except Exception as e:
                logger.warning(f"[Context7] Status check failed: {e}")

        return {
            "is_initialized": _context7_initialized or document_count > 0,
            "db_path": db_path,
            "db_exists": db_exists,
            "document_count": document_count,
            "embed_model": settings.EMBED_MODEL,
            "ollama_url": settings.OLLAMA_BASE_URL,
        }


# Global Instance
knowledge_service = KnowledgeService()
