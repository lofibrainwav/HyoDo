import pathlib
import sys
from typing import Type

# packages/afo-core를 경로에 추가
core_path = pathlib.Path("packages/afo-core").resolve()
if core_path not in sys.path:
    sys.path.insert(0, core_path)

print(f"Checking path: {core_path}")

try:
    # 1. 5 Tigers Verification
    import tigers

    print("✅ Tigers package found")
    from tigers import guan_yu

    print("✅ Guan Yu found")

    # 2. Chancellor Graph Verification
    from chancellor_graph import chancellor_graph

    print("✅ Chancellor Graph imported successfully")
    print(f"   - Type: {type(chancellor_graph)}")

    # Check if compiled
    if hasattr(chancellor_graph, "invoke"):
        print("✅ Graph is compiled (Runnable)")
    else:
        print("⚠️ Graph is NOT compiled")

except ImportError as e:
    print(f"❌ Failed to import: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
