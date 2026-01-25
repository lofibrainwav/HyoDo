import os
import sys
import traceback

# Add package root to path
sys.path.append(os.path.abspath("packages/afo-core"))

try:
    print("Attempting to import build_organs_v2...")
    from AFO.health.organs_v2 import build_organs_v2

    print("Import successful.")

    print("Running build_organs_v2()...")
    result = build_organs_v2()
    print("Execution successful!")
    print(result)

except Exception as e:
    print(f"\n[CRITICAL FAILURE] {e}")
    traceback.print_exc()
