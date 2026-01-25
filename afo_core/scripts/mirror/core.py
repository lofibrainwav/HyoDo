# Trinity Score: 90.0 (Established by Chancellor)
"""
Mirror Core - Chancellor Mirror main class

Contains the ChancellorMirror class which orchestrates:
- Redis connection
- WebSocket/HTTP monitoring
- Verdict analysis
- Pillar data analysis
"""

import asyncio
import json
import logging
import os
from datetime import datetime

import aiohttp
import websockets
from redis.asyncio import Redis
from scripts.mirror.alerts import AlertManager
from scripts.mirror.models import MirrorConfig
from scripts.mirror.recovery import RecoveryEngine

# AFO Kingdom imports
try:
    from AFO.services.trinity_calculator import trinity_calculator
except ImportError:
    trinity_calculator = None

logger = logging.getLogger(__name__)


class ChancellorMirror:
    """
    승상의 거울 (Mirror of Chancellor)

    Trinity Score 실시간 모니터링 및 자동 알람 시스템.
    眞善美孝永 각 기둥의 점수를 지속적으로 모니터링하여
    시스템 건강 상태를 유지합니다.
    """

    def __init__(
        self, api_base: str = "http://localhost:8010", config: MirrorConfig | None = None
    ) -> None:
        self.config = config or MirrorConfig(api_base=api_base)
        self.api_base = self.config.api_base
        self.calculator = trinity_calculator
        self.alert_threshold = self.config.alert_threshold
        self.pillar_thresholds = self.config.pillar_thresholds
        self.redis: Redis | None = None
        self.stream_channel = self.config.stream_channel

        # Initialize components
        self.alert_manager = AlertManager(publish_thought_callback=self._publish_thought)
        self.recovery_engine = RecoveryEngine(
            api_base=self.api_base,
            redis=None,
            publish_thought_callback=self._publish_thought,
        )
        self.alert_manager.set_recovery_engine(self.recovery_engine)

    async def _init_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            host = os.environ.get("REDIS_HOST", "127.0.0.1")
            port = int(os.environ.get("REDIS_PORT", "6379"))
            self.redis = Redis(host=host, port=port, decode_responses=True)
            await self.redis.ping()
            self.recovery_engine.set_redis(self.redis)
        except Exception as e:
            logger.warning(f"Redis connection failed (Observability disabled): {e}")
            self.redis = None

    async def _publish_thought(self, content: str, level: str = "info") -> None:
        """Publish thought/status to Matrix Stream"""
        if not self.redis:
            return

        try:
            payload = {
                "type": "thought",
                "source": "Mirror",
                "content": content,
                "level": level,
                "timestamp": datetime.now().isoformat(),
            }
            await self.redis.publish(self.stream_channel, json.dumps(payload))
        except Exception as e:
            logger.error(f"Failed to publish thought: {e}")

    async def monitor_trinity_score(self) -> None:
        """
        Trinity Score 실시간 모니터링

        SSE 스트림을 통해 Chancellor Graph의 판결을 실시간으로 모니터링합니다.
        """
        await self._init_redis()
        logger.info("🔍 승상의 거울 가동: Trinity Score 실시간 모니터링 시작")
        await self._publish_thought("Chancellor Mirror initialized (Perpetual Surveillance Active)")

        try:
            async with websockets.connect(
                f"ws://{self.api_base.replace('http://', '')}/api/stream/chancellor"
            ) as websocket:
                logger.info("✅ Chancellor WebSocket 연결 성공")

                while True:
                    try:
                        verdict_data = await websocket.recv()
                        verdict = json.loads(verdict_data)
                        await self.analyze_verdict(verdict)

                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("⚠️ WebSocket 연결 끊김, 재연결 시도...")
                        await asyncio.sleep(5)
                        break

                    except json.JSONDecodeError as e:
                        logger.error(f"❌ 판결 데이터 파싱 실패: {e}")
                        continue

        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {e}")
            logger.info("📡 HTTP 폴링 모드로 전환")
            await self.monitor_via_http()

    async def monitor_via_http(self) -> None:
        """
        HTTP 폴링을 통한 모니터링 (WebSocket 실패 시 대체)

        주기적으로 /api/5pillars/current 엔드포인트를 호출하여
        Trinity Score를 모니터링합니다.
        """
        logger.info("🔄 HTTP 폴링 모드로 Trinity Score 모니터링 시작")

        while True:
            try:
                await self.check_current_trinity_score()
                await self._publish_thought("System Pulse: All pillars monitored and stable.")
                await asyncio.sleep(self.config.polling_interval_seconds)

            except Exception as e:
                logger.error(f"❌ Trinity Score 체크 실패: {e}")
                await asyncio.sleep(self.config.error_retry_seconds)

    async def check_current_trinity_score(self) -> None:
        """현재 Trinity Score 조회 및 분석"""
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(f"{self.api_base}/api/5pillars/current") as response,
            ):
                if response.status == 200:
                    data = await response.json()
                    overall = data.get("scores", {}).get("overall", 0) * 100
                    logger.info(f"📊 [Mirror] Current Trinity Score: {overall:.2f}")
                    await self.analyze_pillars_data(data)
                else:
                    logger.warning(f"⚠️ Trinity Score 조회 실패: HTTP {response.status}")

        except Exception as e:
            logger.error(f"❌ HTTP 요청 실패: {e}")

    async def analyze_verdict(self, verdict: dict) -> None:
        """
        Chancellor 판결 분석

        Args:
            verdict: Chancellor 판결 데이터
        """
        trinity_score = verdict.get("trinity_score", 0)
        risk_score = verdict.get("risk_score", 0)

        logger.info(f"📊 Trinity Score: {trinity_score:.1f}, Risk Score: {risk_score}")

        # Total Trinity Score alert check
        if trinity_score < self.alert_threshold:
            await self.alert_manager.raise_alert(
                "total",
                trinity_score,
                self.alert_threshold,
                f"🚨 긴급: 전체 Trinity Score {trinity_score:.1f}점으로 {self.alert_threshold}점 미만!",
            )

        # Risk Score alert check
        if risk_score > 10:
            await self.alert_manager.raise_alert(
                "risk",
                risk_score,
                10,
                f"⚠️ 위험: Risk Score {risk_score}점으로 위험 수준!",
            )

    async def analyze_pillars_data(self, data: dict) -> None:
        """
        5기둥 데이터 분석

        Args:
            data: 5기둥 점수 데이터
        """
        pillars = data.get("scores", {})
        if not pillars:
            pillars = data.get("pillars", {})

        for pillar, score in pillars.items():
            if pillar == "overall":
                continue

            # Scale up to 100 if it's 0-1 range
            normalized_score = score * 100 if score <= 1.0 else score
            threshold = self.pillar_thresholds.get(pillar, 90.0)

            if normalized_score < threshold:
                await self.alert_manager.raise_alert(
                    pillar,
                    normalized_score,
                    threshold,
                    f"⚠️ {pillar.upper()}: {normalized_score:.1f}점으로 기준치 {threshold}점 미만!",
                )

    # Delegated methods to alert_manager for backward compatibility
    @property
    def active_alerts(self) -> None:
        return self.alert_manager.active_alerts

    def get_active_alerts(self) -> None:
        return self.alert_manager.get_active_alerts()

    def clear_resolved_alerts(self) -> None:
        return self.alert_manager.clear_resolved_alerts()
