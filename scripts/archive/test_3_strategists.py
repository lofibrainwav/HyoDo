# scripts/test_3_strategists.py (Phase 2 Verification)
import asyncio
import pathlib
import sys

# Ensure packages/afo-core is in python path
sys.path.append(pathlib.Path("packages/afo-core").resolve())

try:
    # Dynamic import to handle the module name starting with a number if needed,
    # but python allows importing alphanumeric files if they are in path.
    # However, '3_strategists.py' is not a valid module name for standard import (starts with number).
    # We should have named it 'three_strategists.py' but user requested '3_strategists.py'.
    # We will use importlib.util to load it.
    importlib.util

    file_path = "packages/afo-core/3_strategists.py"
    module_name = "three_strategists"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    ThreeStrategists = module.ThreeStrategists
    print("✅ Successfully imported ThreeStrategists from packages/afo-core/3_strategists.py")

except Exception as e:
    print(f"❌ FAIL: Could not import ThreeStrategists: {e}")
    sys.exit(1)


async def test_3_strategists():
    print("\n[Testing 3 Strategists Parallel Reasoning]")

    # Test Case 1: Ideal Scenario
    test_query_ideal = {
        "query": "Ideal Feature",
        "context": {"valid_structure": True},
        "risk_level": 0.05,
        "narrative": "glassmorphism coherent narrative that is concise",
        "ethics_pass": True,
        "coherent": True,
        "validation_level": 10,
    }

    score = await ThreeStrategists.parallel_strategist_thinking(test_query_ideal)
    print(f"Test Case 1 (Ideal): Score = {score}")

    if score >= 90.0:
        print("✅ Test Case 1 PASS: High score as expected.")
    else:
        print(f"❌ Test Case 1 FAIL: Score {score} too low.")

    # Test Case 2: Risk Failure (Sima Yi Block)
    test_query_risk = {
        "query": "Risky Feature",
        "context": {"valid_structure": True},
        "risk_level": 0.8,  # Very High Risk
        "narrative": "glassmorphism",
        "validation_level": 5,
    }

    score_risk = await ThreeStrategists.parallel_strategist_thinking(test_query_risk)
    print(f"Test Case 2 (High Risk): Score = {score_risk}")

    # Should be low because Goodness will return 0.0 due to high risk
    if score_risk < 70.0:
        print("✅ Test Case 2 PASS: Low score due to risk block.")
    else:
        print(f"❌ Test Case 2 FAIL: Score {score_risk} should be lower.")

    print("\n🎉 Phase 2 Verification Complete!")


if __name__ == "__main__":
    asyncio.run(test_3_strategists())
