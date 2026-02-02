import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent / "packages" / "afo-core"))

from AFO.api.chancellor_v2.graph.nodes.goodness_node import goodness_node
from AFO.api.chancellor_v2.graph.nodes.serenity_node import serenity_node
from AFO.api.chancellor_v2.graph.nodes.truth_node import truth_node
from AFO.health.organs_truth import build_organs_final


class MockState:
    def __init__(self) -> None:
        self.plan = {"skill_id": "test_skill", "query": "Check system health"}
        self.input = {"command": "audit"}
        self.outputs = {}
        self.errors = []


async def test_organs():
    print("\n=== STEP 1: Visceral Health Audit (Ojang-yukbu) ===")
    try:
        organs = build_organs_final()
        print(f"Timestamp: {organs['ts']}")
        for name, data in organs["organs"].items():
            status_icon = "✅" if data["status"] == "healthy" else "❌"
            print(
                f"{status_icon} {name}: {data['output']} (Score: {data['score']}, Latency: {data['latency_ms']}ms)"
            )

        sec = organs["security"]
        print(f"🛡️ Security: {sec['output']} (Score: {sec['score']})")
    except Exception as e:
        print(f"❌ Organ Audit Failed: {e}")


async def test_seven_faces():
    print("\n=== STEP 2: Seven Faces Meta-Cognition Audit ===")
    state = MockState()

    # 1. Truth
    print("Evaluating Face 1: TRUTH (眞)...")
    await truth_node(state)
    t = state.outputs.get("TRUTH", {})
    print(
        f"   Score: {t.get('score')} | Verification: {t.get('metadata', {}).get('physical_verification')}"
    )
    print(f"   Reasoning: {t.get('reasoning')}")

    # 2. Goodness
    print("\nEvaluating Face 2: GOODNESS (善)...")
    await goodness_node(state)
    g = state.outputs.get("GOODNESS", {})
    print(
        f"   Score: {g.get('score')} | Compliance: {g.get('metadata', {}).get('constitution_compliance')}"
    )
    print(f"   Reasoning: {g.get('reasoning')}")

    # 3. Serenity
    print("\nEvaluating Face 3: SERENITY (孝)...")
    await serenity_node(state)
    s = state.outputs.get("SERENITY", {})
    print(
        f"   Score: {s.get('score')} | Friction: {s.get('metadata', {}).get('real_time_friction')}"
    )
    print(f"   Reasoning: {s.get('reasoning')}")


async def main():
    print("🚀 STARTING DEEP VISCERAL & SEVEN-SIDED META-VERIFICATION")
    await test_organs()
    await test_seven_faces()
    print("\n✅ AUDIT COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
