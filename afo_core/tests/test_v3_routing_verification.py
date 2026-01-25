# Trinity Score: 95.0 (眞 - V3 Routing Verification)
"""V3 라우팅 동작 검증 테스트.

KeyTriggerRouter와 CostAwareRouter의 동작을 검증합니다.
"""

from __future__ import annotations

import pytest
from api.chancellor_v2.orchestrator.chancellor_orchestrator import (
    ChancellorOrchestrator,
    get_orchestrator,
)
from api.chancellor_v2.orchestrator.cost_aware_router import (
    CostAwareRouter,
    CostTier,
    get_cost_aware_router,
)
from api.chancellor_v2.orchestrator.key_trigger_router import (
    KeyTriggerRouter,
    get_key_trigger_router,
)


class TestKeyTriggerRouter:
    """KeyTriggerRouter V3 검증."""

    def setup_method(self) -> None:
        """각 테스트 전 새 라우터 인스턴스 생성."""
        self.router = KeyTriggerRouter()

    # === 眞 (Truth) Pillar 트리거 테스트 ===

    def test_truth_pillar_type_check(self) -> None:
        """타입 체크 명령은 truth pillar를 선택해야 함."""
        result = self.router.analyze_command("run type check on the codebase")
        assert "truth" in result.pillars
        assert result.scores["truth"] > 0
        assert "타입 체크" in result.matched_triggers["truth"]

    def test_truth_pillar_implement(self) -> None:
        """구현 명령은 truth pillar 필수."""
        result = self.router.analyze_command("implement a new API endpoint")
        assert "truth" in result.pillars
        assert "구현" in result.matched_triggers["truth"]
        assert "API" in result.matched_triggers["truth"]

    def test_truth_pillar_refactor(self) -> None:
        """리팩터링은 truth pillar 고우선."""
        result = self.router.analyze_command("refactor the authentication module")
        assert "truth" in result.pillars
        assert result.scores["truth"] >= 1.5  # refactor weight

    # === 善 (Goodness) Pillar 트리거 테스트 ===

    def test_goodness_pillar_delete(self) -> None:
        """삭제 명령은 goodness pillar 필수 (높은 가중치)."""
        result = self.router.analyze_command("delete the old user data")
        assert "goodness" in result.pillars
        assert result.scores["goodness"] >= 2.0  # delete weight = 2.0
        assert "삭제" in result.matched_triggers["goodness"]

    def test_goodness_pillar_production_deploy(self) -> None:
        """프로덕션 배포는 goodness pillar 최우선."""
        result = self.router.analyze_command("deploy to production")
        assert "goodness" in result.pillars
        assert result.scores["goodness"] >= 3.5  # prod + deploy
        assert "프로덕션" in result.matched_triggers["goodness"]
        assert "배포" in result.matched_triggers["goodness"]

    def test_goodness_pillar_secret_handling(self) -> None:
        """시크릿 관련 명령은 goodness 필수."""
        result = self.router.analyze_command("update the API secret keys")
        assert "goodness" in result.pillars
        assert "시크릿" in result.matched_triggers["goodness"]

    def test_goodness_pillar_rm_rf_danger(self) -> None:
        """rm -rf 명령은 최고 위험 (2.5 weight)."""
        result = self.router.analyze_command("execute rm -rf /tmp/data")
        assert "goodness" in result.pillars
        assert result.scores["goodness"] >= 2.5
        assert "rm -rf 명령" in result.matched_triggers["goodness"]

    # === 美 (Beauty) Pillar 트리거 테스트 ===

    def test_beauty_pillar_ui_design(self) -> None:
        """UI 디자인 명령은 beauty pillar 선택."""
        result = self.router.analyze_command("improve the UI design of the dashboard")
        assert "beauty" in result.pillars
        assert result.scores["beauty"] >= 2.5  # ui + design
        assert "UI" in result.matched_triggers["beauty"]

    def test_beauty_pillar_documentation(self) -> None:
        """문서 작성은 beauty pillar."""
        result = self.router.analyze_command("update the README documentation")
        assert "beauty" in result.pillars
        assert "README" in result.matched_triggers["beauty"]
        assert "문서" in result.matched_triggers["beauty"]

    def test_beauty_pillar_css_tailwind(self) -> None:
        """CSS/Tailwind 작업은 beauty pillar."""
        result = self.router.analyze_command("fix the CSS styles using Tailwind")
        assert "beauty" in result.pillars
        assert result.scores["beauty"] >= 2.5  # css + tailwind + style

    # === 복합 시나리오 테스트 ===

    def test_combined_truth_goodness(self) -> None:
        """기술 + 보안 복합 명령은 truth + goodness."""
        result = self.router.analyze_command("implement authentication system")
        assert "truth" in result.pillars
        assert "goodness" in result.pillars

    def test_all_three_pillars(self) -> None:
        """모든 pillar가 필요한 복합 명령."""
        result = self.router.analyze_command(
            "implement a new UI component with secure authentication"
        )
        assert set(result.pillars) >= {"truth", "goodness", "beauty"}

    def test_minimum_pillars_guarantee(self) -> None:
        """최소 2개 pillar 보장 (min_pillars=2)."""
        # 매칭되는 키워드가 없는 간단한 명령
        result = self.router.analyze_command("hello world")
        assert len(result.pillars) >= 2

    def test_empty_command_all_pillars(self) -> None:
        """빈 명령어는 전체 pillar 선택."""
        result = self.router.analyze_command("")
        # 매칭 없으면 전체 선택
        assert len(result.pillars) >= 2  # min_pillars 보장

    # === 신뢰도(Confidence) 테스트 ===

    def test_high_confidence_with_many_triggers(self) -> None:
        """많은 트리거 매칭 시 높은 신뢰도."""
        result = self.router.analyze_command(
            "implement API endpoint with type check and test coverage"
        )
        assert result.confidence > 0.6

    def test_low_confidence_with_few_triggers(self) -> None:
        """적은 트리거 매칭 시 낮은 신뢰도."""
        result = self.router.analyze_command("do something")
        assert result.confidence <= 0.6

    # === Priority Order 테스트 ===

    def test_priority_order_truth_first(self) -> None:
        """기술 명령은 truth가 우선순위 1위."""
        priority = self.router.get_priority_order("implement new function")
        assert priority[0] == "truth"

    def test_priority_order_goodness_first(self) -> None:
        """보안 명령은 goodness가 우선순위 1위."""
        priority = self.router.get_priority_order("delete production secrets")
        assert priority[0] == "goodness"


class TestCostAwareRouter:
    """CostAwareRouter V3 검증."""

    def setup_method(self) -> None:
        """각 테스트 전 새 라우터 인스턴스 생성."""
        self.router = CostAwareRouter()

    # === 저복잡도 (FREE tier) 테스트 ===

    def test_free_tier_read_command(self) -> None:
        """읽기 명령은 FREE tier."""
        tier = self.router.estimate_complexity("read the file contents")
        assert tier == CostTier.FREE

    def test_free_tier_simple_help(self) -> None:
        """도움말 요청은 FREE tier."""
        tier = self.router.estimate_complexity("help me understand this")
        assert tier == CostTier.FREE

    def test_free_tier_search(self) -> None:
        """검색 명령은 FREE tier."""
        tier = self.router.estimate_complexity("search for user functions")
        assert tier == CostTier.FREE

    # === 중복잡도 (CHEAP tier) 테스트 ===
    # NOTE: CHEAP tier = score >= 2, MEDIUM keywords add +1 each

    def test_cheap_tier_implement_multiple(self) -> None:
        """복합 구현 명령은 CHEAP tier (여러 MEDIUM 키워드)."""
        tier = self.router.estimate_complexity("implement and create a new module with tests")
        assert tier == CostTier.CHEAP  # implement(+1) + create(+1) + test(+1) = 3

    def test_cheap_tier_fix_and_debug(self) -> None:
        """복합 수정 명령은 CHEAP tier."""
        tier = self.router.estimate_complexity("debug and fix the login bug")
        assert tier == CostTier.CHEAP  # debug(+1) + fix(+1) = 2

    def test_cheap_tier_multiple_actions(self) -> None:
        """여러 동작 명령은 CHEAP tier."""
        tier = self.router.estimate_complexity("add, update and modify the button")
        assert tier == CostTier.CHEAP  # add(+1) + update(+1) + modify(+1) = 3

    # === 고복잡도 (EXPENSIVE tier) 테스트 ===

    def test_expensive_tier_production_deploy(self) -> None:
        """프로덕션 배포는 EXPENSIVE tier."""
        tier = self.router.estimate_complexity("deploy to production")
        assert tier == CostTier.EXPENSIVE

    def test_expensive_tier_delete_production(self) -> None:
        """프로덕션 삭제는 EXPENSIVE tier (2개 HIGH 키워드)."""
        tier = self.router.estimate_complexity("delete production database")
        assert tier == CostTier.EXPENSIVE  # delete(+3) + prod(+3) = 6

    def test_expensive_tier_migration_with_auth(self) -> None:
        """인증 마이그레이션은 EXPENSIVE tier (2개 HIGH 키워드)."""
        tier = self.router.estimate_complexity("run authentication database migration")
        assert tier == CostTier.EXPENSIVE  # migration(+3) + auth(+3) = 6

    def test_expensive_tier_auth_refactor(self) -> None:
        """인증 시스템 리팩터링은 EXPENSIVE tier."""
        tier = self.router.estimate_complexity("refactor the authentication system")
        assert tier == CostTier.EXPENSIVE

    def test_expensive_tier_long_command(self) -> None:
        """긴 명령어는 복잡도 증가."""
        long_command = "implement a comprehensive user management system with " + "x " * 100
        tier = self.router.estimate_complexity(long_command)
        # 길이만으로도 CHEAP 이상
        assert tier in (CostTier.CHEAP, CostTier.EXPENSIVE)

    # === Plan 기반 복잡도 테스트 ===

    def test_plan_with_many_steps(self) -> None:
        """단계가 많은 계획은 복잡도 증가."""
        tier = self.router.estimate_complexity(
            "execute task",
            plan={"steps": ["step1", "step2", "step3", "step4", "step5", "step6"]},
        )
        assert tier in (CostTier.CHEAP, CostTier.EXPENSIVE)

    def test_plan_requires_approval(self) -> None:
        """승인 필요 플래그는 복잡도 증가."""
        tier = self.router.estimate_complexity(
            "update config",
            plan={"requires_approval": True, "steps": []},
        )
        assert tier in (CostTier.CHEAP, CostTier.EXPENSIVE)

    def test_plan_dry_run_reduces_complexity(self) -> None:
        """DRY_RUN 플래그는 복잡도 감소."""
        tier_normal = self.router.estimate_complexity(
            "implement feature",
            plan={"steps": ["step1"]},
        )
        tier_dry = self.router.estimate_complexity(
            "implement feature",
            plan={"dry_run": True, "steps": ["step1"]},
        )
        # dry_run이 있으면 복잡도가 같거나 낮음
        tier_order = {CostTier.FREE: 0, CostTier.CHEAP: 1, CostTier.EXPENSIVE: 2}
        assert tier_order[tier_dry] <= tier_order[tier_normal]

    # === 비용 추정 테스트 ===

    def test_cost_estimation_free(self) -> None:
        """FREE tier 비용 추정은 $0."""
        cost_info = self.router.estimate_cost("show help")
        assert cost_info.tier == "free"
        assert cost_info.estimated_cost_usd == 0.0

    def test_cost_estimation_cheap(self) -> None:
        """CHEAP tier 비용 추정."""
        # implement + create + test = 3 → CHEAP tier
        cost_info = self.router.estimate_cost(
            "implement and create a module with tests", estimated_tokens=2000
        )
        assert cost_info.tier == "cheap"
        # 2000 tokens * 0.00025 / 1000 = 0.0005 USD
        assert cost_info.estimated_cost_usd == pytest.approx(0.0005, rel=0.01)

    def test_cost_estimation_expensive(self) -> None:
        """EXPENSIVE tier 비용 추정."""
        cost_info = self.router.estimate_cost("deploy to production", estimated_tokens=2000)
        assert cost_info.tier == "expensive"
        # 2000 tokens * 0.015 / 1000 = 0.03 USD
        assert cost_info.estimated_cost_usd == pytest.approx(0.03, rel=0.01)

    # === Model Selection 테스트 ===

    def test_model_selection_free(self) -> None:
        """FREE tier는 Ollama 모델 선택."""
        model = self.router.select_model("list files")
        assert model.provider == "ollama"
        assert model.cost_tier == CostTier.FREE

    def test_model_selection_expensive(self) -> None:
        """EXPENSIVE tier는 Anthropic Opus 선택."""
        model = self.router.select_model("deploy to production")
        assert model.provider == "anthropic"
        assert "opus" in model.model_id.lower()

    # === Force Tier 테스트 ===

    def test_force_tier_override(self) -> None:
        """force_tier 설정 시 강제 적용."""
        self.router.force_tier = CostTier.EXPENSIVE
        tier = self.router.estimate_complexity("simple help")
        assert tier == CostTier.EXPENSIVE


class TestChancellorOrchestratorV3Routing:
    """ChancellorOrchestrator V3 라우팅 통합 테스트."""

    def setup_method(self) -> None:
        """각 테스트 전 새 오케스트레이터 인스턴스 생성."""
        self.orchestrator = ChancellorOrchestrator()

    def test_routing_info_structure(self) -> None:
        """get_routing_info 반환 구조 검증."""
        info = self.orchestrator.get_routing_info("implement new feature")

        # 버전 확인
        assert info.version == "V3"

        # key_trigger 섹션
        assert hasattr(info, "key_trigger")
        assert hasattr(info.key_trigger, "pillars")
        assert hasattr(info.key_trigger, "confidence")
        assert hasattr(info.key_trigger, "matched_triggers")
        assert hasattr(info.key_trigger, "scores")

        # cost_aware 섹션
        assert hasattr(info, "cost_aware")
        assert hasattr(info.cost_aware, "tier")
        assert hasattr(info.cost_aware, "model")
        assert hasattr(info.cost_aware, "estimated_cost_usd")

        # optimization 섹션
        assert hasattr(info, "optimization")
        assert "pillars_reduced" in info.optimization
        assert "estimated_savings_percent" in info.optimization

    def test_routing_info_truth_command(self) -> None:
        """기술 명령의 라우팅 정보."""
        info = self.orchestrator.get_routing_info("implement API endpoint")
        assert "truth" in info.key_trigger.pillars

    def test_routing_info_goodness_command(self) -> None:
        """보안 명령의 라우팅 정보."""
        info = self.orchestrator.get_routing_info("delete production secrets")
        assert "goodness" in info.key_trigger.pillars
        assert info.cost_aware.tier == "expensive"

    def test_routing_info_savings_calculation(self) -> None:
        """Pillar 절감률 계산 검증."""
        info = self.orchestrator.get_routing_info("simple read task")
        pillars_count = len(info.key_trigger.pillars)
        expected_reduction = 3 - pillars_count
        expected_savings = round((1 - pillars_count / 3) * 100, 1)

        assert info.optimization["pillars_reduced"] == expected_reduction
        assert info.optimization["estimated_savings_percent"] == expected_savings


class TestSingletonInstances:
    """싱글톤 인스턴스 테스트."""

    def test_key_trigger_router_singleton(self) -> None:
        """KeyTriggerRouter 싱글톤 동일성."""
        r1 = get_key_trigger_router()
        r2 = get_key_trigger_router()
        assert r1 is r2

    def test_cost_aware_router_singleton(self) -> None:
        """CostAwareRouter 싱글톤 동일성."""
        r1 = get_cost_aware_router()
        r2 = get_cost_aware_router()
        assert r1 is r2

    def test_orchestrator_singleton(self) -> None:
        """ChancellorOrchestrator 싱글톤 동일성."""
        o1 = get_orchestrator()
        o2 = get_orchestrator()
        assert o1 is o2


# === 실행용 검증 스크립트 ===


def run_v3_routing_verification() -> None:
    """V3 라우팅 검증 실행 (pytest 없이)."""
    print("=" * 60)
    print("V3 Routing Verification")
    print("=" * 60)

    orchestrator = ChancellorOrchestrator()

    test_commands = [
        ("implement new API endpoint", "기술 구현"),
        ("delete production database", "위험 작업"),
        ("update UI design with Tailwind CSS", "UI 작업"),
        ("refactor authentication system", "보안 리팩터링"),
        ("read the README file", "간단한 읽기"),
        ("deploy to production with secret rotation", "복합 고위험"),
    ]

    for command, description in test_commands:
        print(f"\n[{description}]")
        print(f"Command: {command}")

        info = orchestrator.get_routing_info(command)

        print(f"  Pillars: {info.key_trigger.pillars}")
        print(f"  Confidence: {info.key_trigger.confidence:.2f}")
        print(f"  Cost Tier: {info.cost_aware.tier}")
        print(f"  Model: {info.cost_aware.model}")
        print(f"  Est. Cost: ${info.cost_aware.estimated_cost_usd:.6f}")
        print(f"  Savings: {info.optimization['estimated_savings_percent']}%")

        # 매칭된 트리거 출력
        triggers = info.key_trigger.matched_triggers
        for pillar, matched in triggers.items():
            if matched:
                print(f"    {pillar}: {', '.join(matched)}")

    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_v3_routing_verification()
