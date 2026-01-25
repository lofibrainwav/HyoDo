import asyncio
import logging
import os
import pathlib
import sys

# Setup Logger
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("AFO.GrandInspection")

# Setup path
sys.path.append(pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages")).resolve())
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

# Import Verification Modules
try:
    from scripts.verify_constitutional_ai import verify_constitution
    from scripts.verify_diplomatic_protocol import verify_protocol
    from scripts.verify_financial_precision import verify_financial_precision
    from scripts.verify_full_pillars_metrics import verify_full_pillars
    from scripts.verify_sejong_research import verify_sejong_system
except ImportError as e:
    logger.exception("❌ Metacognition Fail: Could not import verification modules. %s", e)
    sys.exit(1)


async def grand_inspection():
    print("\n🏰 [AFO Kingdom] Grand Inspection (Ji-Pi-Ji-Gi) Starting...\n")

    score_card = {
        "CPA_Precision": "PENDING",
        "Sejong_Research": "PENDING",
        "5_Pillars_Metrics": "PENDING",
        "Constitution": "PENDING",
        "Diplomatic_Protocol": "PENDING",
    }

    print("==================================================")

    # 1. Financial Precision (Julie CPA)
    try:
        print("\n💰 [1. Julie CPA Resource Check]")
        await verify_financial_precision()
        score_card["CPA_Precision"] = "✅ PASS"
    except Exception as e:
        print(f"❌ CPA Check Failed: {e}")
        score_card["CPA_Precision"] = "❌ FAIL"

    print("\n--------------------------------------------------")

    # 2. Sejong Research (Self-Improvement)
    try:
        print("\n🔭 [2. Sejong Institute Knowledge Check]")
        await verify_sejong_system()
        score_card["Sejong_Research"] = "✅ PASS"
    except Exception as e:
        print(f"❌ Sejong Check Failed: {e}")
        score_card["Sejong_Research"] = "❌ FAIL"

    print("\n--------------------------------------------------")

    # 3. 5-Pillar Metrics (Measurement)
    try:
        print("\n📊 [3. 5-Pillars Metrics Calibration]")
        await verify_full_pillars()
        score_card["5_Pillars_Metrics"] = "✅ PASS"
    except Exception as e:
        print(f"❌ Metrics Check Failed: {e}")
        score_card["5_Pillars_Metrics"] = "❌ FAIL"

    print("\n--------------------------------------------------")

    # 4. Constitution (Ethics)
    try:
        print("\n📜 [4. Constitutional AI Integrity]")
        await verify_constitution()
        score_card["Constitution"] = "✅ PASS"
    except Exception as e:
        print(f"❌ Constitution Check Failed: {e}")
        score_card["Constitution"] = "❌ FAIL"

    print("\n--------------------------------------------------")

    # 5. Protocol (Manners)
    try:
        print("\n🎩 [5. Diplomatic Protocol Dignity]")
        await verify_protocol()
        score_card["Diplomatic_Protocol"] = "✅ PASS"
    except Exception as e:
        print(f"❌ Protocol Check Failed: {e}")
        score_card["Diplomatic_Protocol"] = "❌ FAIL"

    print("\n==================================================")
    print("🏆 [Grand Inspection Report]")
    all_pass = True
    for module, status in score_card.items():
        print(f"   - {module.ljust(20)}: {status}")
        if "FAIL" in status:
            all_pass = False

    if all_pass:
        print("\n✨ CONCLUSION: The Kingdom is in Perfect Harmony (Metacognition Confirmed).")
    else:
        print("\n⚠️ CONCLUSION: Maintenance Required in some sectors.")


if __name__ == "__main__":
    # Suppress internal prints of imported modules slightly if possible,
    # but for now we let them print to show full logs.
    asyncio.run(grand_inspection())
