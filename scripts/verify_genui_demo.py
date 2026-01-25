import os
import pathlib
import sys

sys.path.append(os.path.join(pathlib.Path.cwd(), "packages/afo-core"))
sys.path.append(os.path.join(pathlib.Path.cwd(), "packages/trinity-os"))

import pathlib

from AFO.genui.genui_orchestrator import GenUIOrchestrator


def verify_genui() -> None:
    print("🔹 Initializing GenUI Verification Protocol...")

    orchestrator = GenUIOrchestrator()

    # Simulate a user request
    prompt = "Create a calculator app in GenUI"
    project_id = "test_calc_v1"

    print(f"🔹 Requesting Project: {project_id}")
    print(f"   Prompt: {prompt}")

    try:
        result = orchestrator.create_project(project_id, prompt)

        print(f"✅ Project Created: {result['status']}")
        print(f"   Code Path: {result['code_path']}")

        # Check if file exists
        if pathlib.Path(result["code_path"]).exists():
            print("✅ File System Check: PASS")
            with pathlib.Path(result["code_path"]).open(encoding="utf-8") as f:
                content = f.read()
                if "calculator" in content.lower():
                    print("✅ Content Logic Check: PASS")
                else:
                    print("❌ Content Logic Check: FAIL (Calculator keywords missing)")
        else:
            print("❌ File System Check: FAIL")

        # Vision Result
        vis = result.get("vision_result", {})
        if vis.get("success"):
            print(f"✅ Vision Check: PASS (Screenshot taken at {vis.get('path')})")
        else:
            print(
                f"⚠️ Vision Check: SKIPPED (Playwright not active or mocked: {vis.get('message')})"
            )

    except Exception as e:
        print(f"❌ Verification Error: {e}")


if __name__ == "__main__":
    verify_genui()
