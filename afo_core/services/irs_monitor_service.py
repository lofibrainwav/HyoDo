"""IRS Monitor Service (TICKET-110)

L2 Infrastructure Layer - IRS 및 법령 변경 감지 서비스
SSOT: TRINITY_OS_PERSONAS.yaml (Yi Sun-sin - Goodness/Safety)

외부 소스(API/RSS)를 모니터링하여 변경 사항을 감지하고,
L1 Domain Model로 변환하여 Collaboration Hub로 전파.

주요 기능:
1. 폴링 및 변경 감지 (Mock 모드 지원)
2. DRY_RUN 모드 지원 (자동 적용 방지)
3. 3책사 영향도 분석 요청
"""

import asyncio
import hashlib
import logging
import random
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx

from AFO.config.settings import settings
from AFO.trinity_score_sharing.domain_models import (
    ChangeImpactAnalysis,
    ChangeType,
    ImpactLevel,
    IRSChangeLog,
    RegulationMetadata,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


class IRSMonitorService:
    """IRS 변경 감지 및 모니터링 서비스"""

    def __init__(self, dry_run: bool = True, mock_mode: bool = False) -> None:
        self.dry_run = dry_run
        self.mock_mode = mock_mode
        self._is_running = False
        self._polling_task: asyncio.Task | None = None

        # 감지된 변경 사항 저장소 (메모리)
        self.detected_changes: list[IRSChangeLog] = []

        # 리스너 (Collaboration Hub 등)
        self.listeners = []

    async def start(self, interval_seconds: int = 300):
        """모니터링 시작"""
        if self._is_running:
            logger.warning("IRSMonitorService is already running.")
            return

        self._is_running = True
        logger.info(f"Starting IRSMonitorService (DRY_RUN={self.dry_run}, MOCK={self.mock_mode})")

        self._polling_task = asyncio.create_task(self._poll_loop(interval_seconds))

    async def stop(self):
        """모니터링 중지"""
        if not self._is_running:
            return

        self._is_running = False
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass

        logger.info("IRSMonitorService stopped.")

    def add_listener(self, callback: Any) -> None:
        """변경 감지 이벤트 리스너 등록"""
        self.listeners.append(callback)

    async def _poll_loop(self, interval: int):
        """주기적 폴링 루프"""
        while self._is_running:
            try:
                await self.check_for_updates()
            except Exception as e:
                logger.error(f"Error during IRS update check: {e}")

            await asyncio.sleep(interval)

    async def check_for_updates(self) -> list[IRSChangeLog]:
        """업데이트 확인 및 처리"""
        try:
            changes = []

            if self.mock_mode:
                changes = await self._fetch_mock_updates()
            else:
                # 실제 IRS RSS Feed 연동
                changes = await self._fetch_real_rss_updates()

            if changes:
                logger.info(f"Detected {len(changes)} IRS updates.")
                for change in changes:
                    await self._process_change(change)

            return changes
        except Exception as e:
            logger.error(
                f"Failed to check for IRS updates: {e}", exc_info=True, extra={"pillar": "善"}
            )
            return []

    async def _process_change(self, change: IRSChangeLog):
        """변경 사항 처리 파이프라인"""
        try:
            # 1. 중복 확인 (Hash 기반)
            if any(c.full_text_hash == change.full_text_hash for c in self.detected_changes):
                return

            # 2. 영향도 분석 (1차 - 정적 분석)
            analysis = self._perform_static_analysis(change)
            change.impact_analysis = analysis

            # 3. 상태 설정 (DRY_RUN 정책)
            if self.dry_run:
                change.status = ValidationStatus.PENDING
                logger.info(f"Change {change.change_id} set to PENDING (DRY_RUN active)")
            else:
                # 리스크가 낮으면 자동 적용 고려 (Yi Sun-sin 정책)
                if analysis.impact_level in [ImpactLevel.LOW, ImpactLevel.NONE]:
                    change.status = ValidationStatus.APPROVED
                else:
                    change.status = ValidationStatus.IN_REVIEW

            # 4. 저장
            self.detected_changes.append(change)

            # 5. 이벤트 전파
            for listener in self.listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(change)
                    else:
                        listener(change)
                except Exception as e:
                    logger.error(f"Error notifying listener: {e}", extra={"pillar": "善"})

        except Exception as e:
            logger.error(
                f"Critical error processing IRS change {change.change_id}: {e}",
                exc_info=True,
                extra={"pillar": "善"},
            )

    async def _fetch_real_rss_updates(self) -> list[IRSChangeLog]:
        """실제 IRS RSS Feed 조회 및 파싱"""
        # RSS URL Updated: Attempting main newsroom feed
        rss_url = settings.IRS_RSS_URL
        changes = []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.get(rss_url)
                    response.raise_for_status()

                    root = ET.fromstring(response.content)  # noqa: S314
                except (httpx.RequestError, ET.ParseError) as e:
                    logger.warning(f"IRS RSS Fetch/Parse failed: {e}")
                    return []

                # Parse Channel -> Item
                for item in root.findall(".//item"):
                    try:
                        title = item.findtext("title") or "No Title"
                        link = item.findtext("link") or ""
                        description = item.findtext("description") or ""
                        # pub_date_str = item.findtext("pubDate") # Unused

                        # 간단한 파싱 (실제론 dateutil 사용 권장)
                        pub_date = datetime.now(UTC)  # Fallback

                        # 고유 해시 생성
                        content_hash = hashlib.sha256(f"{title}{link}".encode()).hexdigest()

                        change = IRSChangeLog(
                            change_id=uuid4(),
                            timestamp=datetime.now(UTC),
                            change_type=ChangeType.MODIFICATION,  # Default for news
                            metadata=RegulationMetadata(
                                source_id="irs_rss_real",
                                regulation_code="IRC-UPDATE",
                                title=title,
                                publication_date=pub_date,
                                effective_date=pub_date,  # Assume immediate
                                url=link,
                                tags=["irs", "rss", "realtime"],
                            ),
                            summary=description[:200] + "..."
                            if len(description) > 200
                            else description,
                            full_text_hash=content_hash,
                            detected_by="IRSMonitorService(RSS)",
                        )
                        changes.append(change)
                    except Exception as parse_error:
                        logger.warning(f"Failed to parse RSS item: {parse_error}")
                        continue

        except httpx.RequestError as e:
            logger.warning(f"IRS RSS Fetch failed (Network): {e}")
        except ET.ParseError as e:
            logger.warning(f"IRS RSS Parse failed (XML): {e}")
        except Exception as e:
            logger.error(f"IRS RSS Unexpected error: {e}")

        return changes

    async def _fetch_mock_updates(self) -> list[IRSChangeLog]:
        """Mock 데이터 생성 (테스트용)"""
        # 10% 확률로 업데이트 발생
        if random.random() > 0.1:
            return []

        mock_change = IRSChangeLog(
            change_id=uuid4(),
            timestamp=datetime.now(),
            change_type=random.choice(list(ChangeType)),
            metadata=RegulationMetadata(
                source_id="mock_irs_rss",
                regulation_code=f"IRC-{random.randint(100, 999)}",
                title=f"Mock Regulation Update {datetime.now().isoformat()}",
                publication_date=datetime.now(),
                effective_date=datetime.now() + timedelta(days=30),
                url="https://irs.gov/mock/update",
                tags=["tax", "compliance", "mock"],
            ),
            summary="This is a generated mock update for testing purposes.",
            full_text_hash=hashlib.sha256(str(datetime.now()).encode()).hexdigest(),
            detected_by="IRSMonitorService(Mock)",
        )
        return [mock_change]

    def _perform_static_analysis(self, change: IRSChangeLog) -> ChangeImpactAnalysis:
        """정적 영향도 분석"""
        # Mock 분석 로직
        level = ImpactLevel.LOW
        if change.change_type in [ChangeType.NEW_REGULATION, ChangeType.REPEAL]:
            level = ImpactLevel.HIGH

        return ChangeImpactAnalysis(
            impact_level=level,
            affected_components=["tax_calculator", "compliance_checker"],
            pillar_impacts={"truth": -0.1, "goodness": 0.05},
            estimated_adaptation_effort=10.0 if level == ImpactLevel.HIGH else 1.0,
            requires_manual_intervention=level != ImpactLevel.LOW,
        )


# 싱글톤 인스턴스
irs_monitor = IRSMonitorService(dry_run=True, mock_mode=settings.IRS_MOCK_MODE)
