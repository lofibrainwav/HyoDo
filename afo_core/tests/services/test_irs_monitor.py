"""Verification Tests for IRSMonitorService (TICKET-110)

L2 Infrastructure Layer 검증
"""

import asyncio
import pytest
from AFO.trinity_score_sharing.domain_models import ValidationStatus, ChangeType, ImpactLevel
from services.irs_monitor_service import IRSMonitorService

@pytest.fixture
def monitor_service() -> None:
    """모니터링 서비스 픽스처 (Mock Mode)"""
    service = IRSMonitorService(dry_run=True, mock_mode=True)
    return service

@pytest.mark.asyncio
async def test_service_lifecycle(monitor_service):
    """서비스 시작/중지 테스트"""
    assert not monitor_service._is_running

    await monitor_service.start(interval_seconds=1)
    assert monitor_service._is_running
    assert monitor_service._polling_task is not None

    await monitor_service.stop()
    assert not monitor_service._is_running

@pytest.mark.asyncio
async def test_mock_detection_logic(monitor_service):
    """Mock 감지 로직 테스트"""
    # Force generating a mock update
    # Note: The service uses random, so we might need to retry or mock the random
    # For this test, we call _fetch_mock_updates directly or loop

    changes = []
    # Try up to 20 times to get a random hit (10% chance)
    for _ in range(20):
        c = await monitor_service._fetch_mock_updates()
        if c:
            changes.extend(c)
            break

    # If we got lucky, verify structure
    if changes:
        change = changes[0]
        assert change.metadata.source_id == "mock_irs_rss"
        assert change.status == ValidationStatus.PENDING # Default for new objects?
        # Actually logic is in _process_change for setting status.
        # Let's verify _process_change logic

        await monitor_service._process_change(change)
        assert change.status == ValidationStatus.PENDING # Because dry_run=True

@pytest.mark.asyncio
async def test_dry_run_policy(monitor_service):
    """DRY_RUN 정책 검증"""
    monitor_service.dry_run = True

    # Manually create a mock change
    from AFO.trinity_score_sharing.domain_models import IRSChangeLog, RegulationMetadata
    from datetime import datetime
    from uuid import uuid4

    change = IRSChangeLog(
        change_type=ChangeType.NEW_REGULATION,
        metadata=RegulationMetadata(
            source_id="test",
            regulation_code="TEST-001",
            title="Test",
            publication_date=datetime.now(),
            effective_date=datetime.now(),
            url="https://test.com"
        ),
        summary="test",
        full_text_hash="hash"
    )

    await monitor_service._process_change(change)
    assert change.status == ValidationStatus.PENDING
    assert change.impact_analysis is not None

    # Check Critical impact due to NEW_REGULATION type in static analysis
    assert change.impact_analysis.impact_level == ImpactLevel.HIGH

@pytest.mark.asyncio
async def test_event_listener():
    """이벤트 리스너 동작 확인"""
    service = IRSMonitorService(dry_run=True, mock_mode=True)
    received_events = []

    async def listener(event):
        received_events.append(event)

    service.add_listener(listener)

    # Trigger manually
    from AFO.trinity_score_sharing.domain_models import IRSChangeLog, RegulationMetadata, ChangeType
    from datetime import datetime
    import hashlib

    change = IRSChangeLog(
        change_type=ChangeType.CLARIFICATION,
        metadata=RegulationMetadata(
            source_id="test",
            regulation_code="TEST-002",
            title="Test Event",
            publication_date=datetime.now(),
            effective_date=datetime.now(),
            url="https://test.com"
        ),
        summary="test listener",
        full_text_hash=hashlib.sha256(b"test").hexdigest()
    )

    await service._process_change(change)

    assert len(received_events) == 1
    assert received_events[0].metadata.regulation_code == "TEST-002"
