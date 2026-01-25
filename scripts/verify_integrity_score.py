import asyncio
import json
import sys
from pathlib import Path

# Add package root to sys.path
sys.path.append(str(Path.cwd() / "packages" / "afo-core"))

from AFO.api.routes.integrity_check import IntegrityCheckRequest, check_integrity


async def verify():
    print("🔍 [Verification] Running Real Integrity Check...")
    request = IntegrityCheckRequest()
    try:
        result = await check_integrity(request)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        score = result["total_score"]
        print(f"\n🏆 REAL TOTAL SCORE: {score}")

        if score == 100:
            print("✨ Perfect Score! (Verified True)")
        else:
            print("📉 Score reflects current reality (Not Hardcoded)")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(verify())
