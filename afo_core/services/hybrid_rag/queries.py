"""
HybridRAG Database Query Functions

Trinity Score: 90.0 (Established by Chancellor)
- query_pgvector: PostgreSQL pgvector 검색
- query_redis: Redis RediSearch KNN 검색
- query_qdrant: Qdrant/LanceDB 벡터 검색
- query_graph_context: Neo4j GraphRAG 검색
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import struct
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from neo4j import GraphDatabase
from pgvector.psycopg2 import register_vector
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from redis.commands.search.query import Query as RedisQuery

from AFO.config.settings import get_settings
from AFO.utils.vector_store import query_vector_store

logger = logging.getLogger(__name__)

# Executor for CPU-bound tasks
_executor = ThreadPoolExecutor(max_workers=16)

# 眞 (Truth): Neo4j Integration (GraphRAG)
try:
    GraphDatabaseType = GraphDatabase
except ImportError:
    GraphDatabaseType = None

# Qdrant Integration
try:
    QdrantClientType = QdrantClient
    QdrantModelsType = qmodels
except ImportError:
    QdrantClientType = None
    QdrantModelsType = None


def query_pgvector(embedding: list[float], top_k: int, pg_pool: Any) -> list[dict[str, Any]]:
    """
    眞 (Truth): PostgreSQL pgvector를 이용한 벡터 검색
    善 (Goodness): 연결 풀 관리 및 예외 처리

    Args:
        embedding: 검색할 벡터
        top_k: 반환할 상위 항목 수
        pg_pool: PostgreSQL 연결 풀

    Returns:
        list[dict]: 검색 결과 리스트
    """
    if pg_pool is None or not embedding:
        return []

    conn = pg_pool.getconn()
    try:
        if register_vector:
            register_vector(conn)

        cursor_factory = RealDictCursor if RealDictCursor is not None else None
        with conn.cursor(cursor_factory=cursor_factory) as cur:
            cur.execute(
                """
                SELECT id, title, url, content, embedding
                FROM rag_documents
                LIMIT 200;
                """
            )
            rows = cur.fetchall() if cur else []
    except Exception as e:
        logger.error(
            f"[Hybrid RAG] PGVector query failed: {e}", exc_info=True, extra={"pillar": "善"}
        )
        return []
    finally:
        pg_pool.putconn(conn)

    if not rows:
        return []

    norm_query = math.sqrt(sum(v * v for v in embedding)) or 1.0
    scored: list[dict[str, Any]] = []
    for row in rows:
        content = row.get("content") or ""
        if not content:
            continue
        vector = row.get("embedding")
        if vector is None:
            continue
        if not isinstance(vector, (list, tuple)):
            vector = vector.tolist() if hasattr(vector, "tolist") else list(vector)

        norm_doc = math.sqrt(sum(v * v for v in vector)) or 1.0
        dot = sum(a * b for a, b in zip(embedding, vector, strict=False))
        similarity = dot / (norm_query * norm_doc)
        scored.append(
            {
                "id": str(row["id"]),
                "content": content,
                "score": float(similarity),
                "source": row.get("url") or row.get("title") or "pgvector",
            }
        )

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]


def query_redis(embedding: list[float], top_k: int, redis_client: Any) -> list[dict[str, Any]]:
    """
    眞 (Truth): Redis RediSearch를 이용한 KNN 벡터 검색
    善 (Goodness): 인덱스 확인 및 예외 차단

    Args:
        embedding: 검색할 벡터
        top_k: 반환할 상위 항목 수
        redis_client: Redis 클라이언트

    Returns:
        list[dict]: 검색 결과 리스트
    """
    if redis_client is None or not embedding:
        return []

    try:
        settings = get_settings()
        index_name = settings.REDIS_RAG_INDEX
    except Exception:
        index_name = os.getenv("REDIS_RAG_INDEX", "rag_docs")

    try:
        vector_blob = struct.pack(f"<{len(embedding)}f", *embedding)
        query = RedisQuery(f"*=>[KNN {top_k} @embedding $vector AS score]")
        query = query.return_fields("content", "source", "score").dialect(2)
        search_result = redis_client.ft(index_name).search(
            query, query_params={"vector": vector_blob}
        )
    except Exception as exc:
        logger.error(f"[Hybrid RAG] Redis 검색 실패: {exc}", exc_info=True, extra={"pillar": "善"})
        return []

    docs = getattr(search_result, "docs", getattr(search_result, "documents", []))
    rows: list[dict[str, Any]] = []
    for doc in docs:
        payload = getattr(doc, "__dict__", doc)
        content = payload.get("content") or ""
        if not content:
            continue
        score_value = payload.get("score")
        try:
            score = float(score_value)
        except (TypeError, ValueError):
            score = 0.0

        rows.append(
            {
                "id": getattr(doc, "id", payload.get("id", "redis")),
                "content": content,
                "score": score,
                "source": payload.get("source") or "redis",
            }
        )

    return rows


def query_graph_context(entities: list[str], limit: int = 5) -> list[dict[str, Any]]:
    """
    美 (Beauty): GraphRAG Context Retrieval
    Neo4j 지식 그래프에서 엔티티 간의 관계를 탐색.
    """
    if GraphDatabaseType is None or not entities:
        return []

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    # 보안: 환경변수에서 패스워드 로드 (하드코딩 제거)
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")
    if not neo4j_password:
        logger.warning("[GraphRAG] NEO4J_PASSWORD 환경변수 미설정", extra={"pillar": "善"})
        return []
    auth = ("neo4j", neo4j_password)

    try:
        results = []
        with (
            GraphDatabase.driver(uri, auth=auth) as driver,
            driver.session() as session,
        ):
            # Find related nodes (1-hop)
            query = """
                MATCH (n)-[r]-(m)
                WHERE n.name IN $entities OR n.id IN $entities
                RETURN n.name AS source, type(r) AS rel, m.name AS target, m.description AS desc
                LIMIT $limit
                """
            records = session.run(query, entities=entities, limit=limit)
            for record in records:
                results.append(
                    {
                        "source": record["source"],
                        "relationship": record["rel"],
                        "target": record["target"],
                        "description": record["desc"] or "",
                    }
                )
        return results
    except Exception as e:
        logger.error(f"[GraphRAG] Neo4j query failed: {e}", exc_info=True, extra={"pillar": "善"})
        return []


def query_qdrant(embedding: list[float], top_k: int, qdrant_client: Any) -> list[dict[str, Any]]:
    """
    眞 (Truth): 통합 벡터 검색 (Brain Organ) - 환경변수 기반 어댑터 사용

    환경변수 VECTOR_DB에 따라 자동으로 적절한 벡터 스토어 선택:
    - VECTOR_DB=lancedb: LanceDB 사용
    - VECTOR_DB=chroma: Chroma 사용
    - 그 외: Qdrant 사용 (기존 호환성 유지)

    Args:
        embedding: 검색할 벡터
        top_k: 반환할 상위 항목 수
        qdrant_client: 기존 호환성을 위한 Qdrant 클라이언트 (사용되지 않음)

    Returns:
        list[dict]: 검색 결과 리스트
    """
    if not embedding:
        return []

    try:
        # 환경변수 기반 벡터 스토어 선택
        return query_vector_store(embedding, top_k)

    except Exception as exc:
        logger.error(f"[Hybrid RAG] 벡터 검색 실패: {exc}", exc_info=True, extra={"pillar": "善"})
        return []


async def query_pgvector_async(
    embedding: list[float], top_k: int, pool: Any
) -> list[dict[str, Any]]:
    """비동기 PGVector 검색 래퍼"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, query_pgvector, embedding, top_k, pool)


async def query_redis_async(
    embedding: list[float], top_k: int, client: Any
) -> list[dict[str, Any]]:
    """비동기 Redis 검색 래퍼"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, query_redis, embedding, top_k, client)


async def query_qdrant_async(
    embedding: list[float], top_k: int, client: Any
) -> list[dict[str, Any]]:
    """비동기 Qdrant 검색 래퍼"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, query_qdrant, embedding, top_k, client)
