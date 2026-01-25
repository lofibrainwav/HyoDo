import asyncio
import os
import pathlib
import sys

# Add package root to path
sys.path.append(os.path.join(pathlib.Path.cwd(), "packages/afo-core"))

from AFO.guardians.critic_agent import CriticAgent
from AFO.julie_cpa.services.julie_service import JulieService
from AFO.start.serenity.genui_orchestrator import GenUIOrchestrator
from AFO.start.serenity.vision_verifier import VisionVerifier


async def main():
    print("⚡ Initialize Nervous System (Dry Run)...")
    results = {"truth": False, "goodness": False, "beauty": False, "serenity": False}

    # 1. Truth & Strategy (CriticAgent)
    try:
        critic = CriticAgent()
        # Test Goodness Gate
        code = "import subprocess\nsubprocess.run(['echo','hi'], check=False)"
        review = await critic.critique_code(code)
        if not review.passed and "Goodness" in review.feedback[0]:
            print("✅ [Truth] CriticAgent active (Caught unsafe code).")
            results["truth"] = True
    except Exception as e:
        print(f"❌ [Truth] CriticAgent Failed: {e}")

    # 2. Goodness & Finance (JulieService)
    try:
        julie = JulieService()
        status = await julie.get_royal_status()
        if status["status"] == "Social Strategy Active (Royal Edition)":
            print(f"✅ [Goodness] JulieService active (Status: {status['status']}).")
            results["goodness"] = True
    except Exception as e:
        print(f"❌ [Goodness] JulieService Failed: {e}")

    # 3. Beauty (GenUIOrchestrator)
    try:
        genui = GenUIOrchestrator()
        # Mock generation
        comp = await genui.generate_component("RoyalAnalyticsWidget")
        if comp["success"]:
            print("✅ [Beauty] GenUIOrchestrator active (Mock Generation Success).")
            results["beauty"] = True
    except Exception as e:
        print(f"❌ [Beauty] GenUIOrchestrator Failed: {e}")

    # 4. Serenity (VisionVerifier)
    try:
        vision = VisionVerifier()
        print(
            f"✅ [Serenity] VisionVerifier instantiated (Screenshot Dir: {vision.screenshot_dir})."
        )
        results["serenity"] = True
    except Exception as e:
        print(f"❌ [Serenity] VisionVerifier Failed: {e}")

    if all(results.values()):
        print("\n🏰 CRITICAL: NERVOUS SYSTEM INITIALIZED SUCCESSFULLY (100%)")
        sys.exit(0)
    else:
        print("\n⚠️ SYSTEM FAILURE: CHECK LOGS")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
