# scripts/verify_chancellor_trinity_routing.py
"""
Verification script for Trinity-Driven Routing in Chancellor Graph.
Tests AUTO_RUN and ASK_COMMANDER scenarios.
"""

import asyncio
import os
import pathlib
import sys

# Ensure AFO package is importable
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

from langchain_core.messages import HumanMessage


async def verify_trinity_routing():
    """Test Trinity-Driven Routing logic."""
    print("=== Trinity-Driven Routing Verification ===")

    try:
        from AFO.chancellor_graph import chancellor_graph
        from AFO.config.antigravity import antigravity
        from AFO.domain.metrics.trinity_manager import trinity_manager
    except ImportError as e:
        print(f"❌ Import Failed: {e}")
        return

    # Test 1: High Trinity Score (AUTO_RUN)
    print("\n[Test 1] High Trinity Score (AUTO_RUN expected)")

    # Reset deltas to ensure high scores
    trinity_manager.deltas = {
        "truth": 0,
        "goodness": 0,
        "beauty": 0,
        "filial_serenity": 0,
        "eternity": 0,
    }

    # Get current metrics to verify high score
    metrics = trinity_manager.get_current_metrics()
    print(f"  Initial Trinity Score: {metrics.trinity_score:.2f}")
    print(f"  Initial Goodness: {metrics.goodness:.2f}")
    print(f"  Risk Score: {1.0 - metrics.goodness:.2f}")

    # Create initial state with all required fields
    # IMPORTANT: Set DRY_RUN_DEFAULT=False for testing AUTO_RUN
    initial_state = {
        "messages": [HumanMessage(content="Simple status check")],
        "trinity_score": 0.0,  # Will be calculated by trinity_decision_gate
        "risk_score": 0.0,  # Will be calculated by trinity_decision_gate
        "auto_run_eligible": False,  # Will be set by trinity_decision_gate
        "kingdom_context": {
            "llm_context": {"quality_tier": "STANDARD"},
            # Override DRY_RUN_DEFAULT for testing
            "antigravity": {
                "AUTO_DEPLOY": antigravity.AUTO_DEPLOY,
                "DRY_RUN_DEFAULT": False,  # ⚠️ 테스트를 위해 False로 설정
                "ENVIRONMENT": antigravity.ENVIRONMENT,
            },
        },
        "analysis_results": {},
        "persistent_memory": {},
        "current_speaker": "user",
        "next_step": "chancellor",
        "steps_taken": 0,
        "complexity": "Low",
    }

    config = {"configurable": {"thread_id": "test_auto_run"}}

    try:
        result = await chancellor_graph.ainvoke(initial_state, config=config)

        auto_run = result.get("auto_run_eligible", False)
        trinity_score = result.get("trinity_score", 0.0)
        risk_score = result.get("risk_score", 0.0)

        print(f"  auto_run_eligible: {auto_run}")
        print(f"  trinity_score: {trinity_score:.2f}")
        print(f"  risk_score: {risk_score:.2f}")

        # Check conditions
        trinity_ok = trinity_score >= 0.9
        risk_ok = risk_score <= 0.1
        dry_run = (
            result.get("kingdom_context", {}).get("antigravity", {}).get("DRY_RUN_DEFAULT", True)
        )

        print(f"  Trinity >= 0.9: {trinity_ok}")
        print(f"  Risk <= 0.1: {risk_ok}")
        print(f"  DRY_RUN_DEFAULT: {dry_run}")

        if auto_run and trinity_ok and risk_ok and not dry_run:
            print("  ✅ AUTO_RUN correctly triggered")
        elif dry_run:
            print("  ⚠️ DRY_RUN 모드 활성화 - auto_run_eligible이 False로 강제됨 (善: 안전 우선)")
        elif not trinity_ok:
            print(f"  ⚠️ Trinity Score {trinity_score:.2f} < 0.9 - ASK_COMMANDER")
        elif not risk_ok:
            print(f"  ⚠️ Risk Score {risk_score:.2f} > 0.1 - ASK_COMMANDER")
        else:
            print("  ⚠️ ASK_COMMANDER (기타 이유)")
    except Exception as e:
        print(f"  ❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()

    # Test 2: Low Trinity Score (ASK_COMMANDER)
    print("\n[Test 2] Low Trinity Score (ASK_COMMANDER expected)")

    # Apply multiple negative triggers to lower score significantly
    for _ in range(5):
        trinity_manager.apply_trigger("VERIFICATION_FAIL")  # -10 Truth each
        trinity_manager.apply_trigger("MANUAL_INTERVENTION")  # -5 Serenity each

    # Get updated metrics
    metrics2 = trinity_manager.get_current_metrics()
    print(f"  Updated Trinity Score: {metrics2.trinity_score:.2f}")
    print(f"  Updated Goodness: {metrics2.goodness:.2f}")
    print(f"  Updated Risk Score: {1.0 - metrics2.goodness:.2f}")

    # Use same initial_state but with updated trinity_manager
    initial_state2 = initial_state.copy()
    config2 = {"configurable": {"thread_id": "test_ask_commander"}}

    try:
        result2 = await chancellor_graph.ainvoke(initial_state2, config=config2)

        auto_run2 = result2.get("auto_run_eligible", False)
        trinity_score2 = result2.get("trinity_score", 0.0)
        risk_score2 = result2.get("risk_score", 0.0)

        print(f"  auto_run_eligible: {auto_run2}")
        print(f"  trinity_score: {trinity_score2:.2f}")
        print(f"  risk_score: {risk_score2:.2f}")

        # Check conditions
        trinity_ok2 = trinity_score2 >= 0.9
        risk_ok2 = risk_score2 <= 0.1

        print(f"  Trinity >= 0.9: {trinity_ok2}")
        print(f"  Risk <= 0.1: {risk_ok2}")

        if not auto_run2 and (not trinity_ok2 or not risk_ok2):
            print("  ✅ ASK_COMMANDER correctly triggered")
        elif auto_run2:
            print("  ❌ AUTO_RUN triggered unexpectedly (Trinity Score가 여전히 높음)")
        else:
            print("  ⚠️ 예상과 다른 결과")
    except Exception as e:
        print(f"  ❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()

    print("\n=== Verification Complete ===")


if __name__ == "__main__":
    asyncio.run(verify_trinity_routing())
