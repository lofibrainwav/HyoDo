"""
Unit tests for Trinity Score calculation

Trinity Score: 眞 (Truth) - Mathematical accuracy
"""

import pytest
from hyodo import calculate_trinity_score, TRINITY_WEIGHTS, should_auto_approve


class TestTrinityScoreCalculation:
    """Trinity Score 계산 테스트"""
    
    def test_perfect_score(self):
        """완벽한 점수 (100점)"""
        score = calculate_trinity_score(
            truth=1.0,
            goodness=1.0,
            beauty=1.0,
            serenity=1.0,
            eternity=1.0
        )
        assert score == 100.0
    
    def test_zero_score(self):
        """최저 점수 (0점)"""
        score = calculate_trinity_score(
            truth=0.0,
            goodness=0.0,
            beauty=0.0,
            serenity=0.0,
            eternity=0.0
        )
        assert score == 0.0
    
    def test_half_score(self):
        """중간 점수 (50점)"""
        score = calculate_trinity_score(
            truth=0.5,
            goodness=0.5,
            beauty=0.5,
            serenity=0.5,
            eternity=0.5
        )
        assert score == 50.0
    
    def test_weight_calculation(self):
        """가중치 계산 검증"""
        # 眞 (35%)만 1.0, 나머지 0.0
        score = calculate_trinity_score(
            truth=1.0,
            goodness=0.0,
            beauty=0.0,
            serenity=0.0,
            eternity=0.0
        )
        expected = 0.35 * 100  # 35.0
        assert score == expected
    
    def test_individual_weights(self):
        """개별 가중치 검증"""
        assert TRINITY_WEIGHTS["truth"] == 0.35
        assert TRINITY_WEIGHTS["goodness"] == 0.35
        assert TRINITY_WEIGHTS["beauty"] == 0.20
        assert TRINITY_WEIGHTS["serenity"] == 0.08
        assert TRINITY_WEIGHTS["eternity"] == 0.02
        
        # 가중치 합 = 1.0
        assert sum(TRINITY_WEIGHTS.values()) == 1.0


class TestAutoApproveDecision:
    """자동 승인 결정 테스트"""
    
    def test_auto_approve_high_score_low_risk(self):
        """고점수 + 저위험 = 자동 승인"""
        assert should_auto_approve(trinity_score=95, risk_score=5) is True
        assert should_auto_approve(trinity_score=90, risk_score=10) is True
    
    def test_auto_approve_boundary(self):
        """경계값 테스트"""
        # 90점 미만
        assert should_auto_approve(trinity_score=89, risk_score=5) is False
        # 위험 10 초과
        assert should_auto_approve(trinity_score=95, risk_score=11) is False
    
    def test_auto_approve_low_score(self):
        """저점수 = 승인 불가"""
        assert should_auto_approve(trinity_score=70, risk_score=5) is False
        assert should_auto_approve(trinity_score=50, risk_score=0) is False
    
    def test_auto_approve_high_risk(self):
        """고위험 = 승인 불가"""
        assert should_auto_approve(trinity_score=100, risk_score=50) is False


class TestTrinityScoreEdgeCases:
    """경계 케이스 테스트"""
    
    def test_default_values(self):
        """기본값 테스트 (serenity, eternity)"""
        score = calculate_trinity_score(
            truth=1.0,
            goodness=1.0,
            beauty=1.0
            # serenity, eternity default to 1.0
        )
        assert score == 100.0
    
    def test_decimal_scores(self):
        """소수점 점수"""
        score = calculate_trinity_score(
            truth=0.95,
            goodness=0.87,
            beauty=0.92,
            serenity=0.88,
            eternity=0.90
        )
        # (0.95*0.35 + 0.87*0.35 + 0.92*0.20 + 0.88*0.08 + 0.90*0.02) * 100
        expected = round((0.3325 + 0.3045 + 0.184 + 0.0704 + 0.018) * 100, 2)
        assert score == expected
    
    def test_rounding(self):
        """반올림 테스트"""
        score = calculate_trinity_score(
            truth=0.333,
            goodness=0.333,
            beauty=0.333,
            serenity=0.333,
            eternity=0.333
        )
        # 소수점 2자리까지 반올림
        assert len(str(score).split('.')[1]) <= 2


@pytest.mark.unit
class TestTrinityScoreWithMarkers:
    """마커가 있는 테스트 예시"""
    
    def test_basic_calculation(self):
        """기본 계산"""
        score = calculate_trinity_score(1.0, 1.0, 1.0, 1.0, 1.0)
        assert score == 100.0
