"""
HybridRAG Result Fusion & Reranking Functions

Trinity Score: 90.0 (Established by Chancellor)
- rerank_results: 결과 재정렬 및 중복 제거
- blend_results: PG/Redis 결과 통합
- blend_results_advanced: RRF 기반 고급 통합
- select_context: 토큰 제한에 맞춰 컨텍스트 선별
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

# Executor for CPU-bound tasks
_executor = ThreadPoolExecutor(max_workers=16)


def rerank_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    善 (Goodness): Reranking & Deduplication
    여러 소스(PG, Redis, Qdrant)의 결과를 재정렬 및 중복 제거.
    (추후 Cross-Encoder 모델 도입 가능)
    """
    unique_map = {}
    for r in results:
        # Content hash or ID based deduplication
        key = r.get("id")
        if not key or key in unique_map:
            continue
        unique_map[key] = r

    # Simple score sort for now (Placeholder for Cohere/CrossEncoder)
    deduplicated = list(unique_map.values())
    deduplicated.sort(key=lambda x: x["score"], reverse=True)
    return deduplicated


def blend_results(
    pg_rows: list[dict[str, Any]], redis_rows: list[dict[str, Any]], top_k: int
) -> list[dict[str, Any]]:
    """
    美 (Beauty): PGVector와 Redis 결과를 통합 및 가중치 정렬 (RRF 유사 방식)

    Args:
        pg_rows: DB 검색 결과
        redis_rows: Cache 검색 결과
        top_k: 최종 반환 수

    Returns:
        list[dict]: 혼합 및 정렬된 결과
    """
    merged: dict[str, dict[str, Any]] = {}

    def boost(row: dict[str, Any], origin: str) -> None:
        row_id = str(row["id"])
        existing = merged.get(row_id)
        adjusted = row["score"] * (1.1 if origin == "pg" else 1.0)
        if existing is None or adjusted > existing["score"]:
            merged[row_id] = {**row, "score": adjusted}

    for row in pg_rows:
        boost(row, "pg")
    for row in redis_rows:
        boost(row, "redis")

    return sorted(merged.values(), key=lambda r: r["score"], reverse=True)[:top_k]


def blend_results_advanced(
    pg_rows: list[dict[str, Any]],
    redis_rows: list[dict[str, Any]],
    qdrant_rows: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    """
    美 (Beauty): Advanced RRF (Reciprocal Rank Fusion)
    PGVector(구조적), Redis(빈도/캐시), Qdrant(의미적) 결과 통합
    """
    merged: dict[str, dict[str, Any]] = {}

    # RRF constant
    k = 60

    def apply_rrf(rows: list[dict[str, Any]], source_weight: float) -> None:
        for rank, row in enumerate(rows):
            row_id = str(row["id"])
            if row_id not in merged:
                merged[row_id] = {
                    **row,
                    "rrf_score": 0.0,
                    "score": row["score"],
                }  # Keep original score mostly

            # RRF formula: 1 / (k + rank)
            # We multiply by source_weight to prioritize trusted sources
            rrf_score = (1 / (k + rank)) * source_weight
            merged[row_id]["rrf_score"] += rrf_score

            # Update source list
            if "sources" not in merged[row_id]:
                merged[row_id]["sources"] = []
            merged[row_id]["sources"].append(row.get("source", "unknown"))

    # Apply Fusion
    apply_rrf(pg_rows, 1.0)  # PostgreSQL (Baseline)
    apply_rrf(redis_rows, 0.8)  # Redis (Cache/Recent)
    apply_rrf(qdrant_rows, 1.2)  # Qdrant (Semantic/Brain - High Trust)

    # Sort by RRF score
    final_results = list(merged.values())
    final_results.sort(key=lambda r: r["rrf_score"], reverse=True)

    return final_results[:top_k]


def select_context(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """
    眞 (Truth): 토큰 제한에 맞춰 컨텍스트 선별

    Args:
        rows: 검색된 청크들
        limit: 글자수 제한

    Returns:
        list[dict]: 선별된 청크들
    """
    selected: list[dict[str, Any]] = []
    used = 0

    for row in rows:
        content = row.get("content") or ""
        if not content:
            continue
        if used + len(content) > limit:
            break
        selected.append(row)
        used += len(content)

    return selected


async def blend_results_async(
    pg_rows: list[dict[str, Any]], redis_rows: list[dict[str, Any]], top_k: int
) -> list[dict[str, Any]]:
    """비동기 결과 혼합 래퍼"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, blend_results, pg_rows, redis_rows, top_k)
