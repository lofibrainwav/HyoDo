from __future__ import annotations

import asyncio
import logging
from typing import Any

from AFO.config.settings import settings

from .cache import RouterCache
from .classifier import TaskClassifier
from .config import ScholarConfigLoader
from .executor import ScholarExecutor
from .scorer import TrinityScorer

logger = logging.getLogger(__name__)


class SSOTCompliantLLMRouter:
    """
    SSOT 준수 LLM 라우터 (Composition Root)
    Modularized in Phase 74
    """

    def __init__(self) -> None:
        """SSOT 준수 라우터 초기화"""
        self.scholars_config = ScholarConfigLoader.load_ssot_scholars()
        self.executor = ScholarExecutor()
        self.cache = RouterCache()
        self.classifier = TaskClassifier(self.scholars_config)

    def classify_task(self, query: str) -> str:
        return self.classifier.classify_task(query)

    def get_scholar_for_task(self, task_type: str) -> str:
        return self.classifier.get_scholar_for_task(task_type)

    async def call_scholar_via_wallet(
        self, scholar_key: str, query: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """API Wallet을 통한 SSOT 준수 학자 호출 (캐싱 및 중복 제거 포함)"""
        # OPTIMIZATION: Check cache first
        cache_key = self.cache.get_cache_key(scholar_key, query, context)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info(f"🎯 Scholar Cache HIT: {scholar_key} ({cache_key[:8]}...)")
            return {**cached_result, "cache_hit": True}

        # OPTIMIZATION: Deduplicate in-flight requests
        if cache_key in self.cache.inflight_requests:
            logger.info(f"⏳ Scholar Request Dedup: {scholar_key} (waiting for existing request)")
            self.cache.record_dedup()
            return await self.cache.inflight_requests[cache_key]

        # Config Check
        if scholar_key not in self.scholars_config:
            raise ValueError(f"Unknown scholar: {scholar_key}")

        scholar_info = self.scholars_config[scholar_key]
        logger.info(
            f"🎓 Calling Scholar: {scholar_info['codename']} ({scholar_info['chinese']}) - {scholar_info['role']}"
        )

        # Create future for deduplication
        loop = asyncio.get_event_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self.cache.inflight_requests[cache_key] = future

        try:
            # Wallet Config Preparation
            pillar_scholars = {
                "truth_scholar",
                "goodness_scholar",
                "beauty_scholar",
                "serenity_scholar",
                "eternity_scholar",
            }

            wallet_config = {}
            if scholar_key in pillar_scholars or scholar_info.get("provider") == "ollama":
                wallet_config = {
                    "model": settings.OLLAMA_MODEL,
                    "base_url": settings.OLLAMA_BASE_URL,
                }
            elif not self.executor.api_wallet:
                raise RuntimeError(
                    "API Wallet not available - SSOT compliance cannot be maintained"
                )
            else:
                wallet_config = self.executor.api_wallet.get(scholar_key)
                if not wallet_config:
                    raise ValueError(f"Scholar '{scholar_key}' not configured in API Wallet")

            # Execute
            result = await self.executor.execute_scholar_call(
                scholar_key, wallet_config, query, context or {}, self.scholars_config
            )

            # Scoring
            trinity_score = TrinityScorer.calculate_ssot_trinity_score(
                result.get("response", ""), scholar_key, scholar_info
            )

            result["trinity_score"] = trinity_score.to_dict()
            result["scholar"] = scholar_key
            result["scholar_codename"] = scholar_info["codename"]
            result["cache_hit"] = False

            logger.info(
                f"✅ Scholar {scholar_info['codename']} completed with Trinity Score: {trinity_score.trinity_score:.3f}"
            )

            # Cache the result
            self.cache.set(cache_key, result)

            # Resolve future
            if not future.done():
                future.set_result(result)

            return result

        except Exception as e:
            logger.error(f"❌ Scholar {scholar_key} call failed: {e}")
            if not future.done():
                future.set_exception(e)
            raise

        finally:
            self.cache.inflight_requests.pop(cache_key, None)

    def get_routing_stats(self) -> dict[str, Any]:
        """SSOT 준수 라우팅 통계"""
        return {
            "scholars_available": list(self.scholars_config.keys()),
            "api_wallet_status": "connected" if self.executor.api_wallet else "disconnected",
            "ssot_compliance": True,
            "trinity_score_weighting": "0.35×眞 + 0.35×善 + 0.20×美 + 0.08×孝 + 0.02×永",
            "cache_stats": self.cache.get_stats(),
        }
