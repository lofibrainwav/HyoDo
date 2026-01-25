import asyncio
import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

from AFO.irs.monitor.analyzer import IRSAnalyzer
from AFO.irs.monitor.crawler import IRSCrawler
from AFO.irs.monitor.notifier import IRSNotifier

if TYPE_CHECKING:
    from AFO.irs.monitor.types import IRSChangeEvent

logger = logging.getLogger(__name__)


class IRSRealtimeMonitor:
    """IRS 실시간 모니터링 시스템 (Orchestrator)"""

    def __init__(self) -> None:
        # 모니터링 대상 URL들
        self.monitoring_urls = {
            "publications": "https://www.irs.gov/publications",
            "revenue_procedures": "https://www.federalregister.gov/agencies/internal-revenue-service",
            "notices": "https://www.irs.gov/newsroom/notices",
            "tax_code": "https://www.irs.gov/taxtopics",
            "forms_instructions": "https://www.irs.gov/instructions",
        }

        # 컴포넌트 초기화
        self.crawler = IRSCrawler(self.monitoring_urls)
        self.analyzer = IRSAnalyzer()
        self.notifier = IRSNotifier()

        # 감지된 변경 이벤트들
        self.detected_changes: list[IRSChangeEvent] = []

        # 모니터링 설정
        self.check_interval = 300  # 5분마다 확인
        self.monitoring_task = None

        # 통계 및 모니터링
        self.monitoring_stats = {
            "total_checks": 0,
            "changes_detected": 0,
            "false_positives": 0,
            "agents_notified": 0,
            "last_monitoring_cycle": None,
            "uptime_seconds": 0,
        }

        logger.info("IRS Realtime Monitor initialized (Modularized)")

    async def start_monitoring(self) -> None:
        """모니터링 시작"""
        logger.info("Starting IRS Realtime Monitoring...")

        # 세션 관리는 Crawler 내부 혹은 Service에서 관리
        # 효율성을 위해 Loop 내에서 세션 생성/해제
        # 초기 베이스라인 수집을 위해 임시 세션 생성
        async with asyncio.Lock():  # 동시 실행 방지 등? 굳이?
            pass

        await self._collect_baseline_hashes()

        # 모니터링 태스크 시작
        monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.monitoring_task = monitoring_task

        logger.info("IRS Realtime Monitoring started")

    async def stop_monitoring(self) -> None:
        """모니터링 중지"""
        logger.info("Stopping IRS Realtime Monitoring...")

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None

        logger.info("IRS Realtime Monitoring stopped")

    async def _collect_baseline_hashes(self) -> None:
        """초기 베이스라인 해시 수집"""
        import aiohttp

        # Crawler에게 위임
        async with aiohttp.ClientSession() as session:
            await self.crawler.collect_baseline_hashes(session)

    async def _monitoring_loop(self) -> None:
        """메인 모니터링 루프"""
        import aiohttp

        start_time = time.time()

        try:
            while True:
                cycle_start = datetime.now()

                try:
                    async with aiohttp.ClientSession() as session:
                        # 모든 모니터링 대상 확인
                        await self._check_all_sources(session)

                        # 통계 업데이트
                        self.monitoring_stats["last_monitoring_cycle"] = cycle_start.isoformat()
                        self.monitoring_stats["total_checks"] += len(self.monitoring_urls)
                        self.monitoring_stats["uptime_seconds"] = time.time() - start_time

                except Exception as e:
                    logger.error(f"Error in monitoring cycle: {e}")

                # 다음 확인까지 대기
                await asyncio.sleep(self.check_interval)

        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Critical error in monitoring loop: {e}")

    async def _check_all_sources(self, session: Any) -> None:
        """모든 모니터링 대상 소스 확인"""
        for source_name, url in self.monitoring_urls.items():
            try:
                # Crawler를 통해 변경 감지
                change_detected, change_details = await self.crawler.detect_changes(session, url)

                if change_detected:
                    # Analyzer를 통해 이벤트 생성
                    change_event = self.analyzer.create_change_event(
                        source_name, url, change_details
                    )

                    if change_event:
                        self.detected_changes.append(change_event)
                        self.monitoring_stats["changes_detected"] += 1
                        logger.info(f"Change detected: {change_event.title}")

                        # Notifier를 통해 알림
                        await self.notifier.notify_agents(change_event)
                        self.monitoring_stats["agents_notified"] += 1

                        # 처리된 이벤트 제거 (오래된 것만 제거하거나, 여기서는 처리 즉시 제거하지 않고 로그용으로 남길수도 있지만
                        # 원본 코드에서는 처리 후 cleared 했음)
                        # 여기서는 일단 리스트에 담아두고 조회용으로 사용.
                        # 원본 코드는 _process_detected_changes에서 clear() 했음.
                        # 조회용(get_recent_changes)을 위해 일부 남겨두는 게 좋음 (Rolling buffer).
                        if len(self.detected_changes) > 100:
                            self.detected_changes.pop(0)

            except Exception as e:
                logger.warning(f"Error checking {source_name}: {e}")

            # 요청 간격 조절
            await asyncio.sleep(0.5)

    def get_monitoring_stats(self) -> dict[str, Any]:
        """모니터링 통계 조회"""
        return {
            "total_checks": self.monitoring_stats["total_checks"],
            "changes_detected": self.monitoring_stats["changes_detected"],
            "false_positives": self.monitoring_stats["false_positives"],
            "agents_notified": self.monitoring_stats["agents_notified"],
            "last_monitoring_cycle": self.monitoring_stats["last_monitoring_cycle"],
            "uptime_seconds": self.monitoring_stats["uptime_seconds"],
            "monitoring_urls": len(self.monitoring_urls),
            "active_hashes": len(self.crawler.content_hashes),
        }

    def get_recent_changes(self, limit: int = 10) -> list[dict[str, Any]]:
        """최근 변경 이벤트 조회"""
        recent_changes = [event.to_dict() for event in self.detected_changes[-limit:]]
        return recent_changes

    def force_check_now(self) -> None:
        """즉시 수동 확인 실행 (테스트용)"""
        import aiohttp

        async def run_check():
            async with aiohttp.ClientSession() as session:
                await self._check_all_sources(session)

        asyncio.create_task(run_check())
