# Trinity Score: 95.0 (眞 - Test Coverage)
"""Tests for Chancellor V3 Routers.

CostAwareRouter와 KeyTriggerRouter의 핵심 기능을 검증합니다.
"""

import pytest
from api.chancellor_v2.orchestrator.cost_aware_router import (
    CostAwareRouter,
    CostTier,
    get_cost_aware_router,
)
from api.chancellor_v2.orchestrator.key_trigger_router import (
    KeyTriggerRouter,
    get_key_trigger_router,
)


class TestCostAwareRouter:
    """CostAwareRouter 테스트."""

    @pytest.fixture
    def router(self) -> CostAwareRouter:
        return CostAwareRouter()

    def test_simple_command_returns_free_tier(self, router: CostAwareRouter) -> None:
        """간단한 명령은 FREE 티어."""
        tier = router.estimate_complexity("list files")
        assert tier == CostTier.FREE

    def test_production_keyword_returns_expensive_tier(self, router: CostAwareRouter) -> None:
        """프로덕션 관련 명령은 EXPENSIVE 티어."""
        tier = router.estimate_complexity("deploy to production")
        assert tier == CostTier.EXPENSIVE

    def test_delete_keyword_increases_complexity(self, router: CostAwareRouter) -> None:
        """delete 키워드는 복잡도 증가."""
        tier = router.estimate_complexity("delete all user data from database")
        assert tier in (CostTier.CHEAP, CostTier.EXPENSIVE)

    def test_implement_keyword_returns_cheap_or_free_tier(self, router: CostAwareRouter) -> None:
        """implement 키워드는 복잡도에 따라 FREE 또는 CHEAP 티어."""
        # 간단한 implement는 FREE 가능
        tier_simple = router.estimate_complexity("implement a simple function")
        assert tier_simple in (CostTier.FREE, CostTier.CHEAP)

        # 복잡한 implement는 CHEAP 이상
        tier_complex = router.estimate_complexity("implement authentication and authorization")
        assert tier_complex in (CostTier.CHEAP, CostTier.EXPENSIVE)

    def test_long_command_increases_complexity(self, router: CostAwareRouter) -> None:
        """긴 명령어는 복잡도 증가."""
        long_command = "a " * 300  # 600 characters
        tier = router.estimate_complexity(long_command)
        assert tier in (CostTier.CHEAP, CostTier.EXPENSIVE)

    def test_get_model_returns_valid_config(self, router: CostAwareRouter) -> None:
        """get_model은 유효한 ModelConfig 반환."""
        for tier in CostTier:
            model = router.get_model(tier)
            assert model.model_id is not None
            assert model.provider in ("ollama", "anthropic", "openai")
            assert 0.0 <= model.quality_score <= 1.0

    def test_estimate_cost_returns_cost_estimate(self, router: CostAwareRouter) -> None:
        """estimate_cost는 CostEstimate 객체 반환."""
        result = router.estimate_cost("test command")
        assert hasattr(result, "tier")
        assert hasattr(result, "model")
        assert hasattr(result, "estimated_cost_usd")
        assert result.estimated_cost_usd >= 0

    def test_force_tier_overrides_estimation(self, router: CostAwareRouter) -> None:
        """force_tier 설정은 추정을 오버라이드."""
        router.force_tier = CostTier.EXPENSIVE
        tier = router.estimate_complexity("simple read command")
        assert tier == CostTier.EXPENSIVE

    def test_singleton_returns_same_instance(self) -> None:
        """싱글톤은 동일 인스턴스 반환."""
        router1 = get_cost_aware_router()
        router2 = get_cost_aware_router()
        assert router1 is router2


class TestKeyTriggerRouter:
    """KeyTriggerRouter 테스트."""

    @pytest.fixture
    def router(self) -> KeyTriggerRouter:
        return KeyTriggerRouter()

    def test_code_related_selects_truth(self, router: KeyTriggerRouter) -> None:
        """코드 관련 명령은 truth 선택."""
        pillars = router.select_pillars("implement a function to calculate sum")
        assert "truth" in pillars

    def test_security_related_selects_goodness(self, router: KeyTriggerRouter) -> None:
        """보안 관련 명령은 goodness 선택."""
        pillars = router.select_pillars("update user password authentication")
        assert "goodness" in pillars

    def test_ui_related_selects_beauty(self, router: KeyTriggerRouter) -> None:
        """UI 관련 명령은 beauty 선택."""
        pillars = router.select_pillars("design a new UI component")
        assert "beauty" in pillars

    def test_delete_command_selects_goodness(self, router: KeyTriggerRouter) -> None:
        """delete 명령은 반드시 goodness 선택."""
        pillars = router.select_pillars("delete all records from database")
        assert "goodness" in pillars

    def test_minimum_pillars_guaranteed(self, router: KeyTriggerRouter) -> None:
        """최소 pillar 수 보장."""
        pillars = router.select_pillars("random unrelated command xyz")
        assert len(pillars) >= router.min_pillars

    def test_analyze_command_returns_full_info(self, router: KeyTriggerRouter) -> None:
        """analyze_command는 전체 정보 반환."""
        result = router.analyze_command("implement secure authentication")
        assert hasattr(result, "pillars")
        assert hasattr(result, "matched_triggers")
        assert hasattr(result, "confidence")
        assert hasattr(result, "scores")
        assert 0.0 <= result.confidence <= 1.0

    def test_high_confidence_for_clear_triggers(self, router: KeyTriggerRouter) -> None:
        """명확한 트리거는 높은 신뢰도."""
        result = router.analyze_command("delete production database drop tables")
        assert result.confidence > 0.5
        assert result.total_triggers_matched > 0

    def test_should_skip_pillar_works(self, router: KeyTriggerRouter) -> None:
        """should_skip_pillar 정상 동작."""
        # UI 명령은 truth를 건너뛸 수 있음 (일반적으로)
        can_skip = router.should_skip_pillar("beauty", "implement algorithm")
        # beauty가 선택 안됐으면 True
        pillars = router.select_pillars("implement algorithm")
        assert can_skip == ("beauty" not in pillars)

    def test_get_priority_order_returns_sorted(self, router: KeyTriggerRouter) -> None:
        """get_priority_order는 점수순 정렬."""
        order = router.get_priority_order("delete secret credentials from production")
        assert len(order) == 3
        # goodness가 최우선 (delete, secret, production 트리거)
        assert order[0] == "goodness"

    def test_singleton_returns_same_instance(self) -> None:
        """싱글톤은 동일 인스턴스 반환."""
        router1 = get_key_trigger_router()
        router2 = get_key_trigger_router()
        assert router1 is router2


class TestRouterIntegration:
    """라우터 통합 테스트."""

    def test_both_routers_consistent(self) -> None:
        """두 라우터가 일관된 결과."""
        command = "deploy authentication service to production"

        cost_router = CostAwareRouter()
        key_router = KeyTriggerRouter()

        # 비용 라우터: 복잡한 작업
        tier = cost_router.estimate_complexity(command)
        assert tier in (CostTier.CHEAP, CostTier.EXPENSIVE)

        # 키 라우터: goodness 필수 (production, auth)
        pillars = key_router.select_pillars(command)
        assert "goodness" in pillars

    def test_readme_command_selects_beauty_cheap(self) -> None:
        """README 작성은 beauty + cheap."""
        command = "write a README documentation"

        cost_router = CostAwareRouter()
        key_router = KeyTriggerRouter()

        tier = cost_router.estimate_complexity(command)
        pillars = key_router.select_pillars(command)

        # 문서 작업은 저비용
        assert tier in (CostTier.FREE, CostTier.CHEAP)
        # beauty가 선택되어야 함
        assert "beauty" in pillars


@pytest.mark.smoke
class TestRouterSmoke:
    """스모크 테스트 (빠른 기본 검증)."""

    def test_cost_router_instantiates(self) -> None:
        """CostAwareRouter 인스턴스화."""
        router = CostAwareRouter()
        assert router is not None

    def test_key_router_instantiates(self) -> None:
        """KeyTriggerRouter 인스턴스화."""
        router = KeyTriggerRouter()
        assert router is not None

    def test_cost_router_basic_flow(self) -> None:
        """CostAwareRouter 기본 흐름."""
        router = CostAwareRouter()
        tier = router.estimate_complexity("test")
        model = router.get_model(tier)
        assert model is not None

    def test_key_router_basic_flow(self) -> None:
        """KeyTriggerRouter 기본 흐름."""
        router = KeyTriggerRouter()
        pillars = router.select_pillars("test")
        assert len(pillars) >= 2
