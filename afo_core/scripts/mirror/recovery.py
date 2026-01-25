# Trinity Score: 90.0 (Established by Chancellor)
"""
Mirror Recovery - Auto-recovery engine for Chancellor Mirror

Handles:
- System diagnostics collection
- Auto-recovery attempts (cache clear, health check, config reload)
"""

import logging

import aiohttp
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RecoveryEngine:
    """Auto-recovery engine for Trinity Score emergencies"""

    def __init__(
        self, api_base: str, redis: Redis | None = None, publish_thought_callback=None
    ) -> None:
        self.api_base = api_base
        self.redis = redis
        self._publish_thought = publish_thought_callback

    def set_redis(self, redis: Redis | None) -> None:
        """Update Redis connection"""
        self.redis = redis

    async def collect_system_diagnostics(self) -> None:
        """Collect system diagnostic information"""
        logger.info("🔍 시스템 진단 정보 수집 중...")

        try:
            async with aiohttp.ClientSession() as session:
                # Health check
                async with session.get(f"{self.api_base}/health") as response:
                    health_data = await response.json()
                    logger.info(f"📊 Health Status: {health_data}")

                # System metrics
                async with session.get(f"{self.api_base}/api/system/metrics") as response:
                    if response.status == 200:
                        metrics_data = await response.json()
                        logger.info(f"📊 System Metrics: {metrics_data}")

        except Exception as e:
            logger.error(f"❌ 진단 정보 수집 실패: {e}")

    async def attempt_auto_recovery(self) -> None:
        """
        Attempt auto-recovery

        Steps:
        1. Clear Redis cache (Trinity Score related)
        2. Check service health
        3. Request config reload
        """
        logger.info("🔧 자동 복구 시도 중...")
        recovery_steps: list[dict[str, str | bool]] = []

        # Step 1: Redis cache clear
        recovery_steps.append(await self._clear_cache())

        # Step 2: Service health check
        recovery_steps.append(await self._check_health())

        # Step 3: Config reload
        recovery_steps.append(await self._reload_config())

        # Summary
        successful_steps = sum(1 for step in recovery_steps if step.get("success"))
        total_steps = len(recovery_steps)
        logger.info(f"🔧 자동 복구 완료: {successful_steps}/{total_steps} 단계 성공")

        if self._publish_thought:
            await self._publish_thought(
                f"Auto-recovery completed: {successful_steps}/{total_steps} steps successful",
                level="info" if successful_steps == total_steps else "warning",
            )

    async def _clear_cache(self) -> dict[str, str | bool]:
        """Clear Trinity Score related Redis cache"""
        try:
            if self.redis:
                keys_cleared = 0
                async for key in self.redis.scan_iter(match="afo:trinity:*"):
                    await self.redis.delete(key)
                    keys_cleared += 1

                logger.info(f"✅ Redis 캐시 클리어 완료: {keys_cleared} keys")
                return {"step": "cache_clear", "success": True, "detail": f"{keys_cleared} keys"}
            else:
                logger.warning("⚠️ Redis 연결 없음, 캐시 클리어 건너뜀")
                return {"step": "cache_clear", "success": False, "detail": "No Redis connection"}
        except Exception as e:
            logger.error(f"❌ 캐시 클리어 실패: {e}")
            return {"step": "cache_clear", "success": False, "detail": str(e)}

    async def _check_health(self) -> dict[str, str | bool]:
        """Check service health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/health",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.info("✅ 서비스 상태 정상")
                        return {
                            "step": "health_check",
                            "success": True,
                            "detail": "Service healthy",
                        }
                    else:
                        logger.warning(f"⚠️ 서비스 상태 비정상: HTTP {response.status}")
                        return {
                            "step": "health_check",
                            "success": False,
                            "detail": f"HTTP {response.status}",
                        }
        except Exception as e:
            logger.error(f"❌ 서비스 상태 확인 실패: {e}")
            return {"step": "health_check", "success": False, "detail": str(e)}

    async def _reload_config(self) -> dict[str, str | bool]:
        """Request config reload"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/api/system/reload",
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    if response.status in (200, 204):
                        logger.info("✅ 설정 리로드 완료")
                        return {
                            "step": "config_reload",
                            "success": True,
                            "detail": "Config reloaded",
                        }
                    elif response.status == 404:
                        logger.debug("ℹ️ 설정 리로드 엔드포인트 없음 (건너뜀)")
                        return {
                            "step": "config_reload",
                            "success": True,
                            "detail": "Endpoint not available (skipped)",
                        }
                    else:
                        logger.warning(f"⚠️ 설정 리로드 실패: HTTP {response.status}")
                        return {
                            "step": "config_reload",
                            "success": False,
                            "detail": f"HTTP {response.status}",
                        }
        except Exception as e:
            logger.error(f"❌ 설정 리로드 실패: {e}")
            return {"step": "config_reload", "success": False, "detail": str(e)}
