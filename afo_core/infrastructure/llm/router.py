from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections import OrderedDict
from typing import Any

from AFO.config.settings import get_settings
from AFO.security.vault_manager import vault as _vault
from infrastructure.json_fast import dumps as json_dumps_fast

from .mcp_integration import enrich_query_context, mcp_integration, parse_llm_tool_calls
from .model_routing import ModelConfig, classify_task, get_model_for_task
from .models import LLMConfig, LLMProvider, QualityTier, RoutingDecision
from .providers import call_llm
from .ssot_compliant_router import ssot_router

# Trinity Score: 95.0 (Established by Chancellor)
"""
AFO LLM Router Core (infrastructure/llm/router.py)

SSOT 준수 하이브리드 LLM 라우터 - API Wallet 기반 집현전 학자 호출
"""


logger = logging.getLogger(__name__)


class LLMRouter:
    """
    SSOT 준수 하이브리드 LLM 라우터 (SSOT Compliant Hybrid LLM Router)
    API Wallet을 통한 집현전 학자 호출 + 기존 라우팅 호환성 유지
    """

    def __init__(self) -> None:
        # SSOT 준수 라우터 초기화 (API Wallet 기반)
        self.ssot_router = ssot_router

        # 기존 호환성을 위한 설정 유지
        self.llm_configs: dict[LLMProvider, LLMConfig] = {}
        self._initialize_configs()
        self.routing_history: list[dict[str, Any]] = []

        # OPTIMIZATION: Response cache with TTL
        self._response_cache: OrderedDict[str, tuple[dict[str, Any], float]] = OrderedDict()
        self._cache_max_size = int(os.getenv("AFO_LLM_CACHE_SIZE", "500"))
        self._cache_ttl = float(os.getenv("AFO_LLM_CACHE_TTL", "3600"))  # 1 hour default
        self._cache_hits = 0
        self._cache_misses = 0

        # Timeout settings based on environment
        self._setup_timeout_configs()

    def _cache_key(self, query: str, context: dict[str, Any] | None) -> str:
        """Generate cache key from query and context."""
        # Sort context keys for consistent hashing
        # OPTIMIZATION: Use fast json for non-sorted cases, fallback for sorted
        ctx_str = json_dumps_fast(context or {}, sort_keys=True, ensure_ascii=False)
        combined = f"{query}:{ctx_str}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def _cache_get(self, key: str) -> dict[str, Any] | None:
        """Get cached response if valid (not expired)."""
        if key not in self._response_cache:
            return None

        cached_value, timestamp = self._response_cache[key]
        if time.time() - timestamp > self._cache_ttl:
            # Expired, remove from cache
            del self._response_cache[key]
            return None

        # Move to end for LRU
        self._response_cache.move_to_end(key)
        self._cache_hits += 1
        return cached_value

    def _cache_set(self, key: str, value: dict[str, Any]) -> None:
        """Store response in cache with timestamp."""
        # Evict oldest if at capacity
        while len(self._response_cache) >= self._cache_max_size:
            self._response_cache.popitem(last=False)

        self._response_cache[key] = (value, time.time())
        self._cache_misses += 1

    def _initialize_configs(self) -> None:
        """LLM 설정 초기화 (Initialize LLM Configurations)"""
        try:
            settings = get_settings()
        except ImportError:
            settings = None

        # Ollama (Internal Wisdom)
        ollama_model = settings.OLLAMA_MODEL if settings else "qwen3-vl:8b"
        ollama_url = settings.OLLAMA_BASE_URL if settings else "http://localhost:11434"

        self.llm_configs[LLMProvider.OLLAMA] = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model=ollama_model,
            base_url=ollama_url,
            latency_ms=500,
            quality_tier=QualityTier.PREMIUM,
            context_window=8192,
        )

        # Vault Integration
        vault = None
        try:
            vault = _vault
        except Exception:  # nosec
            pass

        def get_secret(name: str) -> str | None:
            if vault:
                try:
                    res = vault.get_secret(name)
                    if isinstance(res, str):
                        return res
                except Exception:  # nosec
                    pass
            return getattr(settings, name, None) if settings else os.getenv(name)

        # External Providers (Claude, Gemini, GPT)
        self._add_provider_config(
            LLMProvider.ANTHROPIC,
            "claude-3-sonnet-20240229",
            "ANTHROPIC_API_KEY",
            get_secret,
            quality=QualityTier.ULTRA,
        )
        self._add_provider_config(
            LLMProvider.GEMINI,
            "gemini-2.0-flash-exp",
            "GEMINI_API_KEY",
            get_secret,
            quality=QualityTier.PREMIUM,
        )
        self._add_provider_config(
            LLMProvider.OPENAI,
            "gpt-4o-mini",
            "OPENAI_API_KEY",
            get_secret,
            quality=QualityTier.ULTRA,
        )

        logger.info(f"✅ LLM Router 초기화: {len(self.llm_configs)}개 LLM 설정됨")

    def _setup_timeout_configs(self) -> None:
        """Setup timeout configurations based on environment."""
        # Environment-based timeout settings
        env = os.getenv("AFO_ENV", "dev").lower()

        if env == "dev":
            # Development: shorter timeouts for faster feedback
            self.default_timeout = 10.0  # 10 seconds
            self.scholar_timeout = 15.0  # 15 seconds for scholar calls
            self.pillar_timeout = 8.0  # 8 seconds for pillar nodes
        elif env == "staging":
            # Staging: moderate timeouts
            self.default_timeout = 30.0  # 30 seconds
            self.scholar_timeout = 45.0  # 45 seconds for scholar calls
            self.pillar_timeout = 20.0  # 20 seconds for pillar nodes
        else:  # production
            # Production: longer timeouts for reliability
            self.default_timeout = 60.0  # 60 seconds
            self.scholar_timeout = 90.0  # 90 seconds for scholar calls
            self.pillar_timeout = 45.0  # 45 seconds for pillar nodes

        # Circuit breaker settings
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 3
        self.circuit_breaker_timeout = 300  # 5 minutes

        logger.info(
            f"⏰ Timeout configs set for {env}: default={self.default_timeout}s, scholar={self.scholar_timeout}s, pillar={self.pillar_timeout}s"
        )

    def _add_provider_config(
        self,
        provider: LLMProvider,
        model: str,
        key_env: str,
        secret_fn: Any,
        quality: QualityTier,
    ) -> None:
        key = secret_fn(key_env)
        if key:
            self.llm_configs[provider] = LLMConfig(
                provider=provider,
                model=model,
                api_key_env=key_env,
                quality_tier=quality,
            )

    def route_request(self, query: str, context: dict[str, Any] | None = None) -> RoutingDecision:
        """쿼리에 대한 최적 LLM 라우팅 결정 (Determine Optimal Routing with Task Classification)"""

        ctx = context or {}
        requested = ctx.get("provider")

        # Explicit provider request
        if requested and requested != "auto":
            try:
                p = LLMProvider(requested)
                if p in self.llm_configs:
                    config = self.llm_configs[p]
                    return RoutingDecision(
                        selected_provider=p,
                        selected_model=config.model,
                        reasoning=f"User request: {requested}",
                        confidence=1.0,
                        estimated_cost=0.0,
                        estimated_latency=config.latency_ms,
                        fallback_providers=[LLMProvider.OLLAMA],
                    )
            except ValueError:  # nosec
                pass

        # Task-Type Based Routing (NEW)
        if LLMProvider.OLLAMA in self.llm_configs:
            # Classify task and select appropriate model
            task_type = classify_task(query, ctx)
            selected_model = get_model_for_task(task_type)
            scholar = ModelConfig.TASK_SCHOLAR_MAP.get(task_type, "Unknown")

            decision = RoutingDecision(
                selected_provider=LLMProvider.OLLAMA,
                selected_model=selected_model,
                reasoning=f"Task-Type Routing: {task_type.value} → {scholar}",
                confidence=0.95,
                estimated_cost=0.0,
                estimated_latency=500,
                fallback_providers=[p for p in self.llm_configs if p != LLMProvider.OLLAMA],
            )

            # Ultra quality override for external APIs
            if ctx.get("quality_tier") == QualityTier.ULTRA:
                return self._select_api_llm(query, ctx, QualityTier.ULTRA)

            logger.info(f"🧭 Routing: '{query[:50]}...' → {selected_model} ({scholar})")
            return decision

        return self._select_api_llm(query, ctx, QualityTier.STANDARD)

    def _select_api_llm(
        self, query: str, ctx: dict[str, Any], quality: QualityTier
    ) -> RoutingDecision:
        candidates = [
            c
            for p, c in self.llm_configs.items()
            if p != LLMProvider.OLLAMA and c.quality_tier.value_rank >= quality.value_rank
        ]
        if not candidates:
            candidates = list(self.llm_configs.values())

        best = max(candidates, key=self._calculate_llm_score)
        return RoutingDecision(
            selected_provider=best.provider,
            selected_model=best.model,
            reasoning=f"Best candidate by score: {best.provider}",
            confidence=0.8,
            estimated_cost=0.0,
            estimated_latency=best.latency_ms,
            fallback_providers=[c.provider for c in candidates if c != best],
        )

    def _calculate_llm_score(self, config: LLMConfig) -> float:
        quality = config.quality_tier.value_rank * 0.4
        latency = (2000 / config.latency_ms) * 0.3
        cost = (1.0 / (config.cost_per_token * 1000 + 1)) * 0.3
        return quality + latency + cost

    def _generate_mock_response(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        """Generate mock LLM response for development/testing."""
        # Create deterministic but varied mock responses based on query
        query_hash = hash(query) % 1000

        mock_responses = [
            "이해했습니다. 요청하신 작업을 수행하겠습니다.",
            "분석 결과는 다음과 같습니다: 모든 시스템이 정상 작동 중입니다.",
            "평가 완료: 코드 품질이 우수하며 개선이 필요하지 않습니다.",
            "테스트 결과: 모든 검증 항목이 통과되었습니다.",
            "권장사항: 현재 설정이 최적화되어 있습니다.",
        ]

        selected_response = mock_responses[query_hash % len(mock_responses)]

        # Extract provider from context or use default
        provider = context.get("provider", "ollama") if context else "ollama"
        model = context.get("model", "qwen2.5-coder:7b") if context else "qwen2.5-coder:7b"

        return {
            "success": True,
            "response": f"[MOCK] {selected_response}",
            "routing": {
                "provider": provider,
                "model": model,
                "reasoning": "Mock mode: No actual LLM call made",
            },
            "iterations": 1,
            "tool_results": [],
            "mock_mode": True,
        }

    def _generate_mock_scholar_response(
        self, query: str, scholar_key: str | None, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Generate mock scholar response for development/testing."""
        # Mock scholar response with appropriate Trinity score
        scholar_codename = scholar_key or "MockScholar"

        # Generate mock Trinity scores based on scholar type
        if "truth" in scholar_codename.lower():
            trinity_scores = {"眞": 0.9, "善": 0.8, "美": 0.7, "孝": 0.85, "永": 0.75}
        elif "goodness" in scholar_codename.lower():
            trinity_scores = {"眞": 0.8, "善": 0.95, "美": 0.75, "孝": 0.9, "永": 0.8}
        elif "beauty" in scholar_codename.lower():
            trinity_scores = {"眞": 0.75, "善": 0.8, "美": 0.95, "孝": 0.85, "永": 0.7}
        else:
            trinity_scores = {"眞": 0.85, "善": 0.85, "美": 0.85, "孝": 0.85, "永": 0.85}

        # Calculate overall Trinity score
        trinity_score = sum(trinity_scores.values()) / len(trinity_scores)

        # Generate JSON response compatible with Pillar nodes
        mock_analysis = {
            "score": trinity_scores.get("眞", 0.8) if "truth" in scholar_codename.lower() else 0.8,
            "reasoning": f"Mock analysis by {scholar_codename}: System integrity verified.",
            "issues": [],
            "trinity_scores": trinity_scores,
        }

        return {
            "success": True,
            "scholar": scholar_key or "mock_scholar",
            "scholar_codename": scholar_codename,
            "model": "mock-model",
            "response": json.dumps(mock_analysis, ensure_ascii=False),
            "trinity_score": {
                "trinity_score": trinity_score,
                "pillar_scores": trinity_scores,
                "reasoning": "Mock evaluation completed successfully",
            },
            "mock_mode": True,
        }

    async def call_scholar_via_ssot(
        self,
        query: str,
        scholar_key: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        SSOT 준수 학자 호출 (SSOT Compliant Scholar Call)

        API Wallet을 통한 집현전 학자 호출
        TRINITY_OS_PERSONAS.yaml 기반 아키텍처 준수

        Args:
            query: 사용자 쿼리
            scholar_key: 특정 학자 지정 (없으면 자동 선택)
            context: 추가 컨텍스트

        Returns:
            학자 응답 및 Trinity Score
        """
        # Check for mock mode in scholar calls too
        mock_mode = os.getenv("AFO_LLM_MOCK_MODE", "false").lower() in ("true", "1", "yes")
        if mock_mode:
            logger.info(f"🤖 Scholar Mock Mode: Bypassing {scholar_key or 'auto'} call")
            return self._generate_mock_scholar_response(query, scholar_key, context)

        logger.info(f"🎓 SSOT Scholar Call: {scholar_key or 'auto'} for query: {query[:50]}...")

        try:
            result = await self.ssot_router.call_scholar_via_wallet(
                scholar_key
                or self.ssot_router.get_scholar_for_task(self.ssot_router.classify_task(query)),
                query,
                context,
            )

            # 라우팅 히스토리 기록
            self.routing_history.append(
                {
                    "timestamp": json.dumps(None),  # 현재 시간 기록 방식에 맞춤
                    "provider": f"ssot-{result.get('scholar', 'unknown')}",
                    "model": result.get("model", "unknown"),
                    "query": query[:100],
                    "confidence": result.get("trinity_score", {}).get("trinity_score", 0.8),
                    "ssot_compliant": True,
                }
            )

            logger.info(
                f"✅ SSOT Scholar completed: {result.get('scholar_codename')} with Trinity Score {result.get('trinity_score', {}).get('trinity_score', 0):.3f}"
            )
            return result

        except Exception as e:
            logger.error(f"❌ SSOT Scholar call failed: {e}")
            # 폴백: 기존 라우팅 방식 사용
            logger.warning("🔄 Falling back to legacy routing...")
            return await self.execute_with_routing(query, context)

    async def execute_with_routing(
        self, query: str, context: dict[str, Any] | None = None, max_iterations: int = 3
    ) -> dict[str, Any]:
        """라우팅 및 실행 (Route and Execute with Caching and Tool Loop)"""
        ctx = context or {}

        # OPTIMIZATION: Check cache first (skip for tool-using queries)
        use_cache = ctx.get("enable_cache", True) and not ctx.get("require_tools", False)
        cache_key = self._cache_key(query, ctx) if use_cache else ""

        if use_cache and cache_key:
            cached = self._cache_get(cache_key)
            if cached:
                logger.info(f"🎯 Cache HIT: {cache_key[:8]}...")
                cached["cache_hit"] = True
                return cached

        # Check for mock mode (Dev environment LLM bypass)
        mock_mode = os.getenv("AFO_LLM_MOCK_MODE", "false").lower() in ("true", "1", "yes")
        if mock_mode:
            logger.info("🤖 LLM Mock Mode: Bypassing actual LLM calls")
            return self._generate_mock_response(query, ctx)

        iteration = 0
        current_query = query
        all_tool_results = []

        # 1. Routing Decision
        decision = self.route_request(current_query, ctx)

        while iteration < max_iterations:
            iteration += 1

            # 2. Enrich context with MCP (Context7 + Sequential Thinking + Skills)
            try:
                ctx = await enrich_query_context(current_query, ctx)
                ctx["available_skills"] = mcp_integration.get_available_skills()
            except Exception as e:
                logger.warning(f"MCP enrichment failed: {e}")

            # 3. Call LLM
            try:
                response = await call_llm(decision, current_query, ctx, self.llm_configs)

                # 4. Check for Tool Calls

                tool_calls = parse_llm_tool_calls(response)
                if not tool_calls:
                    # No tool calls, return the response
                    result = {
                        "success": True,
                        "response": response,
                        "routing": {
                            "provider": decision.selected_provider.value,
                            "model": decision.selected_model,
                            "reasoning": decision.reasoning,
                        },
                        "iterations": iteration,
                        "tool_results": all_tool_results,
                        "cache_hit": False,
                    }
                    # OPTIMIZATION: Store in cache (only for non-tool responses)
                    if use_cache and cache_key and not all_tool_results:
                        self._cache_set(cache_key, result)
                    return result

                # Handle Tool Calls
                logger.info(f"🛠️ Detected {len(tool_calls)} tool calls from LLM")
                iteration_results = []
                for call in tool_calls:
                    skill_id = call["skill_id"]
                    params = call["params"]
                    logger.info(f"🚀 Executing Skill: {skill_id} with {params}")

                    result = await mcp_integration.execute_skill(skill_id, params)
                    iteration_results.append({"skill_id": skill_id, "result": result})
                    all_tool_results.append({"skill_id": skill_id, "result": result})

                # Prepare next query with tool results
                current_query = f"{current_query}\n\n[도구 실행 결과]\n{json.dumps(iteration_results, ensure_ascii=False, indent=2)}"
                # Continue loop

            except Exception as e:
                logger.error(f"Execution failed at iteration {iteration}: {e}")
                return {"success": False, "error": str(e), "iterations": iteration}

        return {
            "success": True,
            "response": response,
            "error": "Max iterations reached",
            "iterations": iteration,
            "tool_results": all_tool_results,
        }

    def get_routing_stats(self) -> dict[str, Any]:
        """라우팅 통계 반환 (Get Routing Statistics)"""
        total_requests = len(self.routing_history)

        # Provider usage count
        provider_usage: dict[str, int] = {}
        total_confidence = 0.0
        ssot_compliant_count = 0

        for entry in self.routing_history:
            provider = entry.get("provider", "unknown")
            provider_usage[provider] = provider_usage.get(provider, 0) + 1
            total_confidence += entry.get("confidence", 0.0)
            if entry.get("ssot_compliant", False):
                ssot_compliant_count += 1

        # Calculate ratios
        ollama_count = provider_usage.get("ollama", 0)
        ollama_ratio = ollama_count / total_requests if total_requests > 0 else 0.0
        avg_confidence = total_confidence / total_requests if total_requests > 0 else 0.0
        ssot_compliance_ratio = ssot_compliant_count / total_requests if total_requests > 0 else 0.0

        # SSOT 라우터 통계 포함
        ssot_stats = self.ssot_router.get_routing_stats()

        # OPTIMIZATION: Cache statistics
        total_cache_ops = self._cache_hits + self._cache_misses
        cache_hit_rate = self._cache_hits / total_cache_ops if total_cache_ops > 0 else 0.0

        return {
            "total_requests": total_requests,
            "provider_usage": provider_usage,
            "average_confidence": avg_confidence,
            "ollama_preference_ratio": ollama_ratio,
            "ssot_compliance": {
                "compliant_requests": ssot_compliant_count,
                "compliance_ratio": ssot_compliance_ratio,
                "scholars_available": ssot_stats.get("scholars_available", []),
                "api_wallet_status": ssot_stats.get("api_wallet_status", "unknown"),
                "trinity_score_weighting": ssot_stats.get("trinity_score_weighting", "unknown"),
            },
            "cache": {
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate": cache_hit_rate,
                "size": len(self._response_cache),
                "max_size": self._cache_max_size,
                "ttl_seconds": self._cache_ttl,
            },
        }
