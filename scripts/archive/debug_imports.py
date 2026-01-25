import sys
from pathlib import Path

# Add packages/afo-core to path just like api_server.py
_AFO_ROOT = str(Path(__file__).resolve().parent.parent / "packages" / "afo-core")
if _AFO_ROOT not in sys.path:
    sys.path.insert(0, _AFO_ROOT)

print(f"Path: {_AFO_ROOT}")

try:
    print("Attempting: import config")
    import config

    print(f"Success: config ({config})")
except ImportError as e:
    print(f"Failed: import config ({e})")

try:
    print("Attempting: from config import antigravity")
    from config import antigravity

    print(f"Success: from config import antigravity ({antigravity})")
except ImportError as e:
    print(f"Failed: from config import antigravity ({e})")

try:
    print("Attempting: import AFO")
    import AFO

    print(f"Success: AFO ({AFO})")
except ImportError as e:
    print(f"Failed: import AFO ({e})")

try:
    print("Attempting: from AFO.config import antigravity")
    from AFO.config import antigravity as ag2

    print(f"Success: from AFO.config import antigravity ({ag2})")
except ImportError as e:
    print(f"Failed: from AFO.config import antigravity ({e})")

try:
    print("Attempting: from AFO.services.gen_ui import gen_ui_service")
    from AFO.services.gen_ui import gen_ui_service

    print(f"Success: gen_ui_service ({gen_ui_service})")
except ImportError as e:
    print(f"Failed: gen_ui_service ({e})")
except Exception as e:
    print(f"Exception during gen_ui_service import: {e}")
