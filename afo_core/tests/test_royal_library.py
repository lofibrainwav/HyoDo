"""Royal Library 41선 Skill 테스트

4대 고전(손자병법/삼국지/군주론/전쟁론)의 원칙 검증
"""

import pytest

from AFO.skills.royal_library import Classic, PrincipleResult, RoyalLibrarySkill, skill_041


class TestRoyalLibraryModels:
    """모델 테스트"""

    def test_classic_enum_values(self) -> None:
        """4대 고전 enum 값 확인"""
        assert Classic.SUN_TZU.value == "손자병법"
        assert Classic.THREE_KINGDOMS.value == "삼국지"
        assert Classic.THE_PRINCE.value == "군주론"
        assert Classic.ON_WAR.value == "전쟁론"

    def test_principle_result_dataclass(self) -> None:
        """PrincipleResult 데이터클래스 테스트"""
        result = PrincipleResult(
            principle_id=1,
            principle_name="지피지기",
            classic=Classic.SUN_TZU,
            success=True,
            message="테스트 메시지",
            data={"key": "value"},
            trinity_impact={"眞": 0.70, "孝": 0.30},
        )
        assert result.principle_id == 1
        assert result.principle_name == "지피지기"
        assert result.classic == Classic.SUN_TZU
        assert result.success is True
        assert result.data == {"key": "value"}


class TestSunTzuPrinciples:
    """손자병법 12선 테스트"""

    @pytest.fixture
    def skill(self) -> RoyalLibrarySkill:
        return RoyalLibrarySkill()

    @pytest.mark.asyncio
    async def test_principle_01_preflight_check_success(self, skill: RoyalLibrarySkill) -> None:
        """[01] 지피지기 - 출처 2개 이상이면 성공"""
        result = await skill.principle_01_preflight_check(
            sources=["source1", "source2"],
            context={"loaded": True},
        )
        assert result.success is True
        assert result.principle_id == 1
        assert "眞 100% 확보" in result.message

    @pytest.mark.asyncio
    async def test_principle_01_preflight_check_fail(self, skill: RoyalLibrarySkill) -> None:
        """[01] 지피지기 - 출처 부족 시 실패"""
        result = await skill.principle_01_preflight_check(sources=["only_one"])
        assert result.success is False
        assert "Rule #0 위반" in result.message

    @pytest.mark.asyncio
    async def test_principle_03_dry_run_simulation(self, skill: RoyalLibrarySkill) -> None:
        """[03] 병자궤도야 - DRY_RUN 시뮬레이션"""
        result = await skill.principle_03_dry_run_simulation(lambda x: x * 2, 5, simulate=True)
        assert result.success is True
        assert "[DRY_RUN]" in result.message
        assert result.data["mode"] == "dry_run"

    @pytest.mark.asyncio
    async def test_principle_03_wet_run_execution(self, skill: RoyalLibrarySkill) -> None:
        """[03] 병자궤도야 - WET_RUN 실행"""
        result = await skill.principle_03_dry_run_simulation(lambda x: x * 2, 5, simulate=False)
        assert result.success is True
        assert "[WET_RUN]" in result.message
        assert result.data["mode"] == "wet_run"

    @pytest.mark.asyncio
    async def test_principle_05_trinity_alignment(self, skill: RoyalLibrarySkill) -> None:
        """[05] 도천지장법 - Trinity 정렬 확인"""
        result = await skill.principle_05_trinity_alignment(
            truth_score=0.9, goodness_score=0.8, beauty_score=0.7
        )
        assert result.success is True  # 0.35*0.9 + 0.35*0.8 + 0.20*0.7 = 0.735 >= 0.70

    @pytest.mark.asyncio
    async def test_principle_10_dangerous_action_gate(self, skill: RoyalLibrarySkill) -> None:
        """[10] 화공 - 위험 행동 승인 게이트"""
        result_pending = await skill.principle_10_dangerous_action_gate("삭제", confirmed=False)
        assert result_pending.success is False
        assert "승인 필요" in result_pending.message

        result_confirmed = await skill.principle_10_dangerous_action_gate("삭제", confirmed=True)
        assert result_confirmed.success is True


class TestThreeKingdomsPrinciples:
    """삼국지 12선 테스트"""

    @pytest.fixture
    def skill(self) -> RoyalLibrarySkill:
        return RoyalLibrarySkill()

    @pytest.mark.asyncio
    async def test_principle_14_retry_with_backoff_success(self, skill: RoyalLibrarySkill) -> None:
        """[14] 삼고초려 - 재시도 성공"""
        counter = {"count": 0}

        def succeed_on_second() -> str:
            counter["count"] += 1
            if counter["count"] < 2:
                raise ValueError("첫 시도 실패")
            return "성공"

        result = await skill.principle_14_retry_with_backoff(
            succeed_on_second, max_attempts=3, backoff_factor=0.1
        )
        assert result.success is True
        assert counter["count"] == 2

    @pytest.mark.asyncio
    async def test_principle_14_retry_with_backoff_fail(self, skill: RoyalLibrarySkill) -> None:
        """[14] 삼고초려 - 3번 시도 후 실패"""

        def always_fail() -> None:
            raise ValueError("항상 실패")

        result = await skill.principle_14_retry_with_backoff(
            always_fail, max_attempts=3, backoff_factor=0.1
        )
        assert result.success is False
        assert "3번 시도 후 실패" in result.message

    @pytest.mark.asyncio
    async def test_principle_21_circuit_breaker(self, skill: RoyalLibrarySkill) -> None:
        """[21] 고육지계 - Circuit Breaker 임계값"""
        result = await skill.principle_21_circuit_breaker(threshold=10)
        assert result.success is True
        assert result.data["threshold"] == 10


class TestThePrincePrinciples:
    """군주론 9선 테스트"""

    @pytest.fixture
    def skill(self) -> RoyalLibrarySkill:
        return RoyalLibrarySkill()

    @pytest.mark.asyncio
    async def test_principle_25_strict_typing_pass(self, skill: RoyalLibrarySkill) -> None:
        """[25] 사랑보다두려움 - 타입 검증 통과"""
        result = await skill.principle_25_strict_typing("hello", str)
        assert result.success is True
        assert "타입 검증 통과" in result.message

    @pytest.mark.asyncio
    async def test_principle_25_strict_typing_fail(self, skill: RoyalLibrarySkill) -> None:
        """[25] 사랑보다두려움 - 타입 불일치"""
        result = await skill.principle_25_strict_typing("hello", int)
        assert result.success is False
        assert "타입 불일치" in result.message

    @pytest.mark.asyncio
    async def test_principle_28_ux_friction_check(self, skill: RoyalLibrarySkill) -> None:
        """[28] 증오피하기 - UX Friction 체크"""
        result_safe = await skill.principle_28_ux_friction_check(friction_score=20)
        assert result_safe.success is True

        result_danger = await skill.principle_28_ux_friction_check(friction_score=50)
        assert result_danger.success is False

    @pytest.mark.asyncio
    async def test_principle_33_creative_solution(self, skill: RoyalLibrarySkill) -> None:
        """[33] 결과정당화 - Trinity > 90 파격 허용"""
        result_allowed = await skill.principle_33_creative_solution(trinity_score=0.95)
        assert result_allowed.success is True
        assert "파격 허용" in result_allowed.message

        result_standard = await skill.principle_33_creative_solution(trinity_score=0.85)
        assert result_standard.success is False
        assert "정석 유지" in result_standard.message


class TestOnWarPrinciples:
    """전쟁론 8선 테스트"""

    @pytest.fixture
    def skill(self) -> RoyalLibrarySkill:
        return RoyalLibrarySkill()

    @pytest.mark.asyncio
    async def test_principle_34_null_check_success(self, skill: RoyalLibrarySkill) -> None:
        """[34] 전장의안개 - 데이터 검증 통과"""
        result = await skill.principle_34_null_check_validation(
            data={"name": "test", "value": 42},
            required_fields=["name", "value"],
        )
        assert result.success is True
        assert "진군 허가" in result.message

    @pytest.mark.asyncio
    async def test_principle_34_null_check_fail(self, skill: RoyalLibrarySkill) -> None:
        """[34] 전장의안개 - 데이터 누락 BLOCK"""
        result = await skill.principle_34_null_check_validation(data=None)
        assert result.success is False
        assert "[BLOCK]" in result.message

    @pytest.mark.asyncio
    async def test_principle_36_root_cause_analysis(self, skill: RoyalLibrarySkill) -> None:
        """[36] 중심 - Root Cause 분석"""
        result = await skill.principle_36_root_cause_analysis(
            symptoms=["timeout error", "connection timeout", "request timeout"]
        )
        assert result.success is True
        assert "핵심 원인 식별" in result.message

    @pytest.mark.asyncio
    async def test_principle_40_auto_run_gate(self, skill: RoyalLibrarySkill) -> None:
        """[40] 대담함 - AUTO_RUN 게이트"""
        result_auto = await skill.principle_40_auto_run_gate(confidence=0.95)
        assert result_auto.success is True
        assert "AUTO_RUN" in result_auto.message

        result_manual = await skill.principle_40_auto_run_gate(confidence=0.60)
        assert result_manual.success is False
        assert "수동 확인" in result_manual.message


class TestRoyalLibrarySkill:
    """RoyalLibrarySkill 통합 테스트"""

    def test_singleton_export(self) -> None:
        """skill_041 싱글톤 확인"""
        assert skill_041 is not None
        assert isinstance(skill_041, RoyalLibrarySkill)
        assert skill_041.principles_count == 41

    def test_get_principle_info(self) -> None:
        """원칙 정보 조회"""
        info = skill_041.get_principle_info(1)
        assert info["name"] == "지피지기"
        assert info["classic"] == "손자병법"

        info_unknown = skill_041.get_principle_info(999)
        assert info_unknown["name"] == "미구현"

    def test_list_implemented_principles(self) -> None:
        """구현된 원칙 목록 (핵심 6개)"""
        principles = skill_041.list_implemented_principles()
        assert 1 in principles  # 지피지기
        assert 14 in principles  # 삼고초려
        assert 34 in principles  # 전장의안개
