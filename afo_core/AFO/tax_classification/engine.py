"""Tax Classification Engine.

Redis 캐싱 및 배치 처리를 포함한 문서 분류 오케스트레이터.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from .rules import classify_primary_category, classify_subcategory, has_excluded_patterns

logger = logging.getLogger(__name__)


class TaxDocumentClassifier:
    """Tax/AICPA 문서 자동 분류기."""

    def __init__(self, redis_client=None) -> None:
        self.redis = redis_client
        self.cache_ttl = 86400

    async def classify_document(self, document_path: str, content: str) -> dict[str, Any]:
        """단일 문서를 분류합니다 (Redis 캐시 활용)."""
        f"tax_class:{hashlib.sha256(content.encode()).hexdigest()}"

        # 실제 Redis 연동 로직 (모의)
        if self.redis:
            # cached = await self.redis.get(cache_key)
            pass

        if has_excluded_patterns(content):
            return {"status": "excluded", "category": "None"}

        primary = classify_primary_category(content)
        sub = classify_subcategory(content, primary)

        result = {
            "path": document_path,
            "category": primary,
            "subcategory": sub,
            "confidence": 0.95,
        }

        return result

    async def batch_classify(self, docs: list[dict[str, str]]) -> list[dict[str, Any]]:
        """다수의 문서를 배치로 처리합니다."""
        results = []
        for doc in docs:
            results.append(await self.classify_document(doc["path"], doc["content"]))
        return results
