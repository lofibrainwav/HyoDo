import asyncio
import os
import pathlib
import sys

# Add package root to path
sys.path.append(os.path.join(pathlib.Path.cwd(), "packages/afo-core"))

from AFO.start.serenity.vision_verifier import VisionVerifier


async def main():
    verifier = VisionVerifier()
    print("👁️ Connecting Vision Bridge to Royal Dashboard (Port 3000)...")

    # Verify Dashboard Layout
    result = await verifier.verify_url("http://localhost:3000", "dashboard_layout_restoration")

    if result.passed:
        print(f"✅ Vision Check Passed! Screenshot saved to: {result.screenshot_path}")
        print("System looks healthy. Confirmed 401k/HSA Advice Cards.")
    else:
        print(f"⚠️ Vision Check Failed! Errors: {result.errors}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
