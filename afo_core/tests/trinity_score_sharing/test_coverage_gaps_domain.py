"""Trinity Score Sharing Coverage Gap Tests - Domain Models

L1 도메인 레이어 커버리지 갭 해소 테스트.
SSOT: TRINITY_OS_PERSONAS.yaml, domain/metrics/trinity_ssot.py

Split from test_coverage_gaps.py for 500-line rule compliance.
"""

from datetime import datetime
from math import isclose

import pytest

from AFO.trinity_score_sharing.domain_models import (
    ChangeImpactAnalysis,
    ImpactLevel,
    IRSChangeLog,
    PillarScores,
    RegulationMetadata,
    TrinityScoreUpdateEvent,
)


class TestDomainModelsCoverageGaps:
    """Domain Models 커버리지 갭 테스트"""

    def test_irs_change_log_is_critical_true(self) -> None:
        """IRSChangeLog.is_critical == True 테스트 (line 176-179)"""
        metadata = RegulationMetadata(
            source_id="test-source",
            regulation_code="IRC-174",
            title="Test Regulation",
            publication_date=datetime.now(),
            effective_date=datetime.now(),
            url="https://example.com",
        )
        impact_analysis = ChangeImpactAnalysis(
            impact_level=ImpactLevel.CRITICAL,
            affected_components=["tax_engine"],
            pillar_impacts={},
            estimated_adaptation_effort=10.0,
        )
        change_log = IRSChangeLog(
            change_type="new_regulation",  # lowercase enum value
            metadata=metadata,
            summary="Test change",
            full_text_hash="abc123",
            impact_analysis=impact_analysis,
        )

        # Critical impact level → is_critical = True
        assert change_log.is_critical() is True

    def test_irs_change_log_is_critical_false(self) -> None:
        """IRSChangeLog.is_critical == False 테스트"""
        metadata = RegulationMetadata(
            source_id="test-source",
            regulation_code="IRC-174",
            title="Test Regulation",
            publication_date=datetime.now(),
            effective_date=datetime.now(),
            url="https://example.com",
        )
        impact_analysis = ChangeImpactAnalysis(
            impact_level=ImpactLevel.HIGH,  # CRITICAL가 아님
            affected_components=["tax_engine"],
            pillar_impacts={},
            estimated_adaptation_effort=10.0,
        )
        change_log = IRSChangeLog(
            change_type="new_regulation",  # lowercase enum value
            metadata=metadata,
            summary="Test change",
            full_text_hash="abc123",
            impact_analysis=impact_analysis,
        )

        # Non-critical impact level → is_critical = False
        assert change_log.is_critical() is False

    def test_irs_change_log_is_critical_no_analysis(self) -> None:
        """IRSChangeLog.is_critical == False (impact_analysis=None) 테스트"""
        metadata = RegulationMetadata(
            source_id="test-source",
            regulation_code="IRC-174",
            title="Test Regulation",
            publication_date=datetime.now(),
            effective_date=datetime.now(),
            url="https://example.com",
        )
        change_log = IRSChangeLog(
            change_type="new_regulation",  # lowercase enum value
            metadata=metadata,
            summary="Test change",
            full_text_hash="abc123",
            impact_analysis=None,  # 분석 없음
        )

        # No analysis → is_critical = False
        assert change_log.is_critical() is False

    def test_pillar_scores_to_weights_dict(self) -> None:
        """PillarScores.to_weights_dict() 테스트 (line 223-)"""
        scores = PillarScores(truth=0.9, goodness=0.8, beauty=0.7, serenity=0.6, eternity=0.5)
        weights = scores.to_weights_dict()

        assert "truth" in weights
        assert "goodness" in weights
        assert "beauty" in weights
        assert "serenity" in weights
        assert "eternity" in weights
        assert isclose(weights["truth"], 0.35, rel_tol=1e-9)
        assert isclose(weights["goodness"], 0.35, rel_tol=1e-9)
        assert isclose(weights["beauty"], 0.20, rel_tol=1e-9)
        assert isclose(weights["serenity"], 0.08, rel_tol=1e-9)
        assert isclose(weights["eternity"], 0.02, rel_tol=1e-9)

    def test_trinity_score_update_event_creation(self) -> None:
        """TrinityScoreUpdateEvent 생성 테스트"""
        scores = PillarScores(truth=0.85, goodness=0.80, beauty=0.75, serenity=0.70, eternity=0.65)
        event = TrinityScoreUpdateEvent(
            session_id="test-session",
            agent_id="jang_yeong_sil",
            new_scores=scores,
            reason="Improved documentation",
        )

        assert event.session_id == "test-session"
        assert event.agent_id == "jang_yeong_sil"
        assert event.reason == "Improved documentation"
        assert event.new_scores.truth == 0.85

    def test_trinity_score_update_event_timestamp(self) -> None:
        """TrinityScoreUpdateEvent 타임스탬프 테스트"""
        from datetime import datetime

        before = datetime.now()
        event = TrinityScoreUpdateEvent(
            session_id="test-session",
            agent_id="sima_yi",
            new_scores=PillarScores(
                truth=0.75, goodness=0.70, beauty=0.65, serenity=0.60, eternity=0.55
            ),
            reason="Security issue found",
        )
        after = datetime.now()

        assert before <= event.timestamp <= after

    def test_collaboration_metrics_snapshot_creation(self) -> None:
        """CollaborationMetricsSnapshot 생성 테스트"""
        from AFO.trinity_score_sharing.models.trinity_models import CollaborationMetricsSnapshot

        snapshot = CollaborationMetricsSnapshot(
            session_id="test-session",
            average_trinity_score=0.85,
            consensus_level=0.90,
            active_agents=["jang_yeong_sil", "sima_yi", "zhou_yu"],
        )

        assert snapshot.session_id == "test-session"
        assert snapshot.average_trinity_score == 0.85
        assert snapshot.consensus_level == 0.90
        assert len(snapshot.active_agents) == 3
        assert "jang_yeong_sil" in snapshot.active_agents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
