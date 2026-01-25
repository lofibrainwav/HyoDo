"""
Trinity Gate 테스트

pytest -v packages/afo-core/tests/irs/test_trinity_gate.py
"""

import pytest

from AFO.irs.auto_updater import UpdateStatus
from AFO.irs.evidence_bundle_extended import TrinityScore
from AFO.irs.trinity_gate import (
    GateDecision,
    GateResult,
    TrinityGate,
)


@pytest.fixture
def trinity_gate() -> TrinityGate:
    """Trinity Gate fixture"""
    return TrinityGate(
        min_auto_run_score=0.90,
        min_ask_score=0.70,
        max_risk_score=0.10,
    )


@pytest.fixture
def high_trinity_score() -> TrinityScore:
    """높은 Trinity Score fixture"""
    return TrinityScore(
        truth=0.95,
        goodness=0.95,
        beauty=0.90,
        serenity=0.95,
        eternity=1.0,
        total=0.94,
        calculated_at="2026-01-18T00:00:00",
    )


@pytest.fixture
def medium_trinity_score() -> TrinityScore:
    """중간 Trinity Score fixture"""
    return TrinityScore(
        truth=0.85,
        goodness=0.92,  # Risk가 0.08이 되도록 (< 0.10)
        beauty=0.80,
        serenity=0.85,
        eternity=1.0,
        total=0.85,
        calculated_at="2026-01-18T00:00:00",
    )


@pytest.fixture
def low_trinity_score() -> TrinityScore:
    """낮은 Trinity Score fixture"""
    return TrinityScore(
        truth=0.60,
        goodness=0.60,
        beauty=0.50,
        serenity=0.60,
        eternity=0.90,
        total=0.62,
        calculated_at="2026-01-18T00:00:00",
    )


@pytest.fixture
def low_goodness_score() -> TrinityScore:
    """낮은 Goodness 점수 fixture (높은 리스크)"""
    return TrinityScore(
        truth=0.95,
        goodness=0.70,  # 낮음
        beauty=0.90,
        serenity=0.95,
        eternity=1.0,
        total=0.87,
        calculated_at="2026-01-18T00:00:00",
    )


class TestTrinityGate:
    """Trinity Gate 테스트"""

    def test_init_default_values(self) -> None:
        """기본 값 초기화 테스트"""
        gate = TrinityGate()

        assert gate.min_auto_run_score == 0.90
        assert gate.min_ask_score == 0.70
        assert gate.max_risk_score == 0.10

    def test_evaluate_auto_run_high_score_low_risk(
        self, trinity_gate: TrinityGate, high_trinity_score: TrinityScore
    ) -> None:
        """
        높은 Trinity Score + 낮은 Risk Score → AUTO_RUN 테스트
        """
        result = trinity_gate.evaluate(high_trinity_score, risk_score=0.05)

        assert result.decision == GateDecision.AUTO_RUN
        assert result.trinity_score == high_trinity_score.total
        assert result.risk_score == pytest.approx(0.05)
        assert "자동 실행 가능" in result.reason

    def test_evaluate_ask_commander_medium_score(
        self, trinity_gate: TrinityGate, medium_trinity_score: TrinityScore
    ) -> None:
        """
        중간 Trinity Score + 낮은 Risk Score → ASK_COMMANDER 테스트
        """
        result = trinity_gate.evaluate(medium_trinity_score, risk_score=0.05)

        assert result.decision == GateDecision.ASK_COMMANDER
        assert "사령관 승인 필요" in result.reason

    def test_evaluate_block_low_score(
        self, trinity_gate: TrinityGate, low_trinity_score: TrinityScore
    ) -> None:
        """
        낮은 Trinity Score → BLOCK 테스트
        """
        result = trinity_gate.evaluate(low_trinity_score, risk_score=0.05)

        assert result.decision == GateDecision.BLOCK
        assert "Trinity Score 부족" in result.reason

    def test_evaluate_block_high_risk(
        self, trinity_gate: TrinityGate, high_trinity_score: TrinityScore
    ) -> None:
        """
        높은 Trinity Score + 높은 Risk Score → BLOCK 테스트
        """
        result = trinity_gate.evaluate(high_trinity_score, risk_score=0.15)

        assert result.decision == GateDecision.BLOCK
        assert "Risk Score 초과" in result.reason

    def test_evaluate_float_score(self, trinity_gate: TrinityGate) -> None:
        """float score 입력 테스트"""
        result = trinity_gate.evaluate(trinity_score=0.92, risk_score=0.05)

        assert result.decision == GateDecision.AUTO_RUN
        assert result.trinity_score == 0.92

    def test_calculate_risk_score_with_trinity_score_object(
        self, trinity_gate: TrinityGate, low_goodness_score: TrinityScore
    ) -> None:
        """
        Trinity Score 객체로 리스크 점수 계산 테스트
        낮은 Goodness = 높은 Risk
        """
        calculated_risk = trinity_gate._calculate_risk_score(
            low_goodness_score, manual_risk_score=0.05
        )

        # Goodness 리스크 (1.0 - 0.70 = 0.30)가 더 높음
        assert calculated_risk == pytest.approx(0.30)

    def test_calculate_risk_score_with_float(self, trinity_gate: TrinityGate) -> None:
        """float score로 리스크 점수 계산 테스트"""
        calculated_risk = trinity_gate._calculate_risk_score(
            trinity_score=0.90, manual_risk_score=0.08
        )

        assert calculated_risk == 0.08

    def test_validate_pillars_all_pass(
        self, trinity_gate: TrinityGate, high_trinity_score: TrinityScore
    ) -> None:
        """모든 기둥 PASS 테스트"""
        validation = trinity_gate.validate_pillars(high_trinity_score)

        assert all(validation.values()) is True

    def test_validate_pillars_mixed_results(self, trinity_gate: TrinityGate) -> None:
        """기둥별 혼합 결과 테스트"""
        # 혼합 결과를 위한 로컬 TrinityScore
        mixed_score = TrinityScore(
            truth=0.85,  # < 0.90 → FAIL
            goodness=0.84,  # < 0.85 → FAIL
            beauty=0.80,  # >= 0.80 → PASS
            serenity=0.85,
            eternity=1.0,
            total=0.85,
            calculated_at="2026-01-18T00:00:00",
        )
        validation = trinity_gate.validate_pillars(mixed_score)

        # Truth < 0.90 이므로 FAIL
        assert validation["眞 (Truth)"] is False
        # Goodness < 0.85 이므로 FAIL
        assert validation["善 (Goodness)"] is False

    def test_get_pillar_details(
        self, trinity_gate: TrinityGate, high_trinity_score: TrinityScore
    ) -> None:
        """기둥별 상세 정보 조회 테스트"""
        details = trinity_gate.get_pillar_details(high_trinity_score)

        assert "眞 (Truth)" in details
        assert "善 (Goodness)" in details
        assert "美 (Beauty)" in details
        assert "孝 (Serenity)" in details
        assert "永 (Eternity)" in details

        # Truth 기둥 상세
        truth_details = details["眞 (Truth)"]
        assert truth_details["score"] == high_trinity_score.truth
        assert truth_details["weight"] == 0.35
        assert "기술적 확실성" in truth_details["description"]
        assert truth_details["status"] == "PASS"

    def test_explain_decision(
        self, trinity_gate: TrinityGate, high_trinity_score: TrinityScore
    ) -> None:
        """결정 설명 테스트 (evidence_bundle 없을 때)"""
        result = trinity_gate.evaluate(high_trinity_score, risk_score=0.05)

        explanation = trinity_gate.explain_decision(result)

        # evidence_bundle이 None이면 간소화된 설명
        assert "Trinity Gate 결정" in explanation
        assert "AUTO_RUN" in explanation
        assert "사유" in explanation  # reason이 포함됨

    def test_explain_decision_without_evidence_bundle(self, trinity_gate: TrinityGate) -> None:
        """Evidence Bundle 없이 결정 설명 테스트"""
        result = GateResult(
            decision=GateDecision.ASK_COMMANDER,
            trinity_score=0.85,
            risk_score=0.08,
            reason="Test reason",
            evidence_bundle=None,
        )

        explanation = trinity_gate.explain_decision(result)

        assert "ASK_COMMANDER" in explanation
        assert "Test reason" in explanation

    def test_make_decision_all_conditions(self, trinity_gate: TrinityGate) -> None:
        """모든 결정 조건 테스트"""
        # AUTO_RUN 조건
        decision, reason = trinity_gate._make_decision(0.95, 0.05)
        assert decision == GateDecision.AUTO_RUN
        assert "자동 실행 가능" in reason

        # ASK_COMMANDER 조건
        decision, reason = trinity_gate._make_decision(0.80, 0.05)
        assert decision == GateDecision.ASK_COMMANDER
        assert "사령관 승인 필요" in reason

        # BLOCK 조건 (Trinity Score 부족)
        decision, reason = trinity_gate._make_decision(0.60, 0.05)
        assert decision == GateDecision.BLOCK
        assert "Trinity Score 부족" in reason

        # BLOCK 조건 (Risk Score 초과)
        decision, reason = trinity_gate._make_decision(0.95, 0.15)
        assert decision == GateDecision.BLOCK
        assert "Risk Score 초과" in reason


class TestGateResult:
    """Gate Result 테스트"""

    def test_to_dict(self) -> None:
        """딕셔너리 변환 테스트"""
        result = GateResult(
            decision=GateDecision.AUTO_RUN,
            trinity_score=0.95,
            risk_score=0.05,
            reason="Test reason",
            evidence_bundle=None,
        )

        result_dict = result.to_dict()

        assert result_dict["decision"] == "auto_run"
        assert result_dict["trinity_score"] == 0.95
        assert result_dict["risk_score"] == 0.05
        assert result_dict["reason"] == "Test reason"
        assert result_dict["evidence_bundle"] is None

    def test_timestamp_auto_generation(self) -> None:
        """타임스탬프 자동 생성 테스트"""
        result = GateResult(
            decision=GateDecision.ASK_COMMANDER,
            trinity_score=0.85,
            risk_score=0.08,
            reason="Test",
        )

        assert result.timestamp is not None
        assert len(result.timestamp) > 0


class TestGateDecision:
    """Gate Decision 테스트"""

    def test_enum_values(self) -> None:
        """Enum 값 테스트"""
        assert GateDecision.AUTO_RUN.value == "auto_run"
        assert GateDecision.ASK_COMMANDER.value == "ask_commander"
        assert GateDecision.BLOCK.value == "block"
