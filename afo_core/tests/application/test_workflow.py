"""Verification Tests for Multimodal Collaboration Workflow (TICKET-111)

L3 Application Layer 검증
"""

import pytest
import asyncio
from AFO.trinity_score_sharing.domain_models import IRSChangeLog, RegulationMetadata, ChangeType, ImpactLevel
from AFO.multimodal_collaboration_workflow import MultimodalCollaborationWorkflow, WorkflowState
from datetime import datetime

@pytest.fixture
def workflow() -> None:
    return MultimodalCollaborationWorkflow()

@pytest.fixture
def sample_change_log() -> None:
    return IRSChangeLog(
        change_type=ChangeType.NEW_REGULATION,
        metadata=RegulationMetadata(
            source_id="test_src",
            regulation_code="TEST-111",
            title="Workflow Test Regulation",
            publication_date=datetime.now(),
            effective_date=datetime.now(),
            url="http://test.com"
        ),
        summary="Test Summary",
        full_text_hash="hash123"
    )

@pytest.mark.asyncio
async def test_workflow_initialization(workflow):
    """엔진 초기화 테스트"""
    assert workflow.state == WorkflowState.IDLE
    assert workflow.workflow_id is not None
    assert "associate" in workflow.julie_agents

@pytest.mark.asyncio
async def test_process_irs_change(workflow, sample_change_log):
    """IRS 변경 처리 전체 흐름 테스트"""

    # Run the workflow
    analysis = await workflow.process_irs_change(sample_change_log)

    # Check results
    assert analysis is not None
    assert analysis.jang_yeong_sil_opinion is not None
    assert analysis.yi_sun_sin_opinion is not None
    assert analysis.shin_saimdang_opinion is not None

    # Check if impact level was correctly set by mock logic (NEW_REGULATION -> HIGH/MEDIUM)
    # Our mock implementation sets it to HIGH for NEW_REGULATION
    assert analysis.impact_level == ImpactLevel.HIGH

    # Check final state (Planning Adaptation because it was HIGH impact)
    assert workflow.state == WorkflowState.PLANNING_ADAPTATION

@pytest.mark.asyncio
async def test_parallel_execution(workflow, sample_change_log):
    """병렬 실행 확인 (Timing test is tricky in unit test, focusing on result aggregation)"""

    analysis = await workflow._analyze_impact_parallel(sample_change_log)

    assert "Technical impact" in analysis.jang_yeong_sil_opinion
    assert "Risk assessment" in analysis.yi_sun_sin_opinion
    assert "User Dashboard" in analysis.shin_saimdang_opinion
