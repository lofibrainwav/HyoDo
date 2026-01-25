import os
import sys
from pathlib import Path

# Add python path setup similar to api_server.py
current_dir = Path(__file__).resolve().parent  # scripts/
package_root = current_dir.parent  # packages/afo-core/
monorepo_root = package_root.parent  # packages/
trinity_os_path = monorepo_root / "trinity-os"
sys.path.insert(0, str(package_root))
if str(trinity_os_path) not in sys.path:
    sys.path.insert(0, str(trinity_os_path))

print(f"Checking imports with sys.path: {sys.path[:3]}...")

modules_to_test = [
    "AFO.api.routers.got",
    "AFO.api.routers.modal_data",
    "AFO.api.routers.multi_agent",
    "AFO.api.routers.n8n",
    "AFO.api.routes.trinity_policy",
    "AFO.api.routes.trinity_sbt",
]

for mod_name in modules_to_test:
    print(f"\nTesting import: {mod_name}")
    try:
        __import__(mod_name)
        print(f"✅ Application import successful: {mod_name}")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback

        traceback.print_exc()
