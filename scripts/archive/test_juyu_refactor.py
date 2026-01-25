import asyncio
import os
import pathlib
import sys

# Set path
sys.path.append(
    pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
)

import pathlib

from AFO.agents.juyu_core import juyu


async def main():
    print("🎨 Awakening Juyu...")

    # 1. Setup: Create a "Rough" Widget (Low Beauty Score)
    target_path = "packages/dashboard/src/components/genui/SamahwiGeneratedWidget.tsx"

    # Read existing
    if pathlib.Path(target_path).exists():
        original = pathlib.Path(target_path).read_text(encoding="utf-8")

    # Sabotage it (Remove Glassmorphism) to test Juyu
    rough_code = original.replace("glass-card", "bg-gray-500")
    pathlib.Path(target_path).write_text(rough_code, encoding="utf-8")
    print("\n[Setup] Sabotaged Widget (Removed 'glass-card' token)")

    # 2. Run Juyu
    print("\n[Action] Juyu Refactoring...")
    result = await juyu.run("Refactor genui/SamahwiGeneratedWidget.tsx")
    print(f"Result: {result}")

    # 3. Verify
    final_code = pathlib.Path(target_path).read_text(encoding="utf-8")

    if "glass-card" in final_code:
        print("\n✅ Phase 16-3 COMPLETE: Juyu successfully injected 'glass-card' token.")
    else:
        print("\n❌ PHASE 16-3 FAILED: 'glass-card' token missing.")


if __name__ == "__main__":
    asyncio.run(main())
