#!/usr/bin/env python3
import pathlib
import sys

from langchain_core.messages import AIMessage

# Add package root to path
sys.path.append(pathlib.Path("packages/afo-core").resolve())

try:
    from chancellor_graph import chancellor_router_node

    print("✅ Chancellor Graph Logic imported.")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)


def test_routing(trinity: float, risk: float, dry_run: bool) -> None:
    print(f"\n🧪 Testing Scenario: Trinity={trinity}, Risk={risk}, DryRun={dry_run}")

    # Mock State
    state = {
        "messages": [AIMessage(content="Test Query")],
        "trinity_score": trinity,
        "risk_score": risk,
        "auto_run_eligible": False,  # Initial state
        "kingdom_context": {"antigravity": {"DRY_RUN_DEFAULT": dry_run}},
        "analysis_results": {},
    }

    # Run Node Logic
    chancellor_router_node(state)

    # Check Result (Logic modifies state in-place in current implementation or returns next step)
    # Note: Our implementation modifies state["auto_run_eligible"] in place inside the function before returning
    is_auto = state.get("auto_run_eligible")

    print(f"   -> Result Auto-Run: {is_auto}")

    # Validation
    if dry_run and is_auto:
        print("   ❌ FAIL: Auto-Run should be FALSE in Dry Run")
        return False

    if not dry_run:
        should_be_auto = trinity >= 90 and risk <= 10
        if is_auto == should_be_auto:
            print("   ✅ PASS: Logic matches expectation")
            return True
        print(f"   ❌ FAIL: Expected {should_be_auto}, got {is_auto}")
        return False

    print("   ✅ PASS: Dry Run safety check passed")
    return True


def main() -> None:
    print("==========================================")
    print(" ⚖️  Chancellor Logic Verification")
    print("==========================================")

    # Case 1: Perfect Score, No Dry Run -> Should be True
    t1 = test_routing(95.0, 5.0, False)

    # Case 2: Risk High -> Should be False
    t2 = test_routing(95.0, 20.0, False)

    # Case 3: Trinity Low -> Should be False
    t3 = test_routing(80.0, 5.0, False)

    # Case 4: Perfect Score but Dry Run -> Should be False
    t4 = test_routing(95.0, 5.0, True)

    if all([t1, t2, t3, t4]):
        print("\n🏆 All Routing Logic Tests Passed!")
    else:
        print("\n⚠️ Some Tests Failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
