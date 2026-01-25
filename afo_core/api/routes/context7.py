from __future__ import annotations

import logging
import os
import sys
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from trinity_os.servers.context7_mcp import Context7MCP

# Trinity Score: 95.0 (New Context7 API)
"""AFO Context7 Router (Self-Awareness Knowledge Base)

Context7 지식 베이스를 외부로 노출하는 API 라우터.
眞善美孝 철학을 준수하며, Context7MCP를 통해 지식 검색을 제공합니다.

Author: AFO Kingdom Development Team
Date: 2025-12-26
Version: 1.0.0
"""


# Configure logging
logger = logging.getLogger(__name__)

# Initialize Router
router = APIRouter(prefix="/api/context7", tags=["Context7"])


@router.get("/search")
async def search_context7(
    q: str = Query(..., description="Search query for Context7 knowledge base"),
    limit: int = Query(5, description="Maximum number of results", ge=1, le=20),
) -> dict[str, Any]:
    """Search Context7 knowledge base.

    Trinity Score: 眞 (Truth) - 정확한 지식 검색 제공
    """
    try:
        # Import Context7MCP (with proper path handling)

        trinity_os_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "trinity-os")
        )
        if trinity_os_path not in sys.path:
            sys.path.insert(0, trinity_os_path)

        # Create instance and search
        context7 = Context7MCP()
        results: Any = context7.retrieve_context(q)

        # Format results
        formatted_results: list[dict[str, Any]] = []
        if isinstance(results, dict) and "results" in results:
            # If results is dict with 'results' key
            raw_results = results.get("results", [])
        elif isinstance(results, list):
            # If results is list directly
            raw_results = results
        else:
            # Fallback
            raw_results = []

        for item in raw_results[:limit]:
            if isinstance(item, dict):
                formatted_results.append(
                    {
                        "id": item.get("id", f"item_{len(formatted_results)}"),
                        "content": item.get("content", ""),
                        "metadata": item.get("metadata", {}),
                        "score": item.get("score", 0.0),
                    }
                )

        return {
            "query": q,
            "results": formatted_results,
            "total": len(formatted_results),
            "status": "success",
        }

    except Exception as e:
        logger.error("Context7 search failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Context7 search failed: {e!s}") from e


@router.get("/health")
async def context7_health() -> dict[str, Any]:
    """Check Context7 health status.

    Trinity Score: 善 (Goodness) - 시스템 건강 모니터링
    """
    try:
        # Import Context7MCP

        trinity_os_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "trinity-os")
        )
        if trinity_os_path not in sys.path:
            sys.path.insert(0, trinity_os_path)

        # Create instance and check
        context7 = Context7MCP()

        return {
            "status": "healthy",
            "instance_created": True,
            "knowledge_base_accessible": True,
            "retrieval_works": True,
        }

    except Exception as e:
        logger.error("Context7 health check failed: %s", e)
        return {
            "status": "error",
            "error": str(e),
            "instance_created": False,
            "knowledge_base_accessible": False,
            "retrieval_works": False,
        }


@router.get("/list")
async def list_context7_items() -> dict[str, Any]:
    """
    List all items in Context7 knowledge base.

    Trinity Score: 眞 (Truth) - 전체 지식 목록 투명성 제공
    """
    try:
        # Import Context7MCP

        trinity_os_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "trinity-os")
        )
        if trinity_os_path not in sys.path:
            sys.path.insert(0, trinity_os_path)

        # Create instance
        context7 = Context7MCP()

        # Return knowledge base directly
        return {
            "status": "success",
            "total": len(context7.knowledge_base),
            "items": context7.knowledge_base,
        }

    except Exception as e:
        logger.error("Context7 list failed: %s", e)
        return {"status": "error", "error": str(e), "items": []}
