import pathlib
import sys
import time

import requests

API_URL = "http://localhost:8013/api/system/antigravity/config"
ENV_FILE = "packages/afo-core/.env.antigravity"


def check_config(expected_dry_run) -> None:
    try:
        resp = requests.get(API_URL)
        data = resp.json()
        print(f"Server Config: {data}")
        is_correct = data["dry_run_default"] == expected_dry_run
        if is_correct:
            print(f"✅ Verified: dry_run_default is {expected_dry_run}")
        else:
            print(f"❌ Failed: Expected {expected_dry_run}, got {data['dry_run_default']}")
        return is_correct
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False


# 1. Check Initial State (Should be True)
print("--- Check 1: Initial State ---")
time.sleep(2)  # Wait for server startup
if not check_config(True):
    sys.exit(1)

# 2. Modify File (Set False)
print("\n--- Check 2: Modifying .env.antigravity ---")
pathlib.Path(ENV_FILE).write_text(
    "ENVIRONMENT=dev\nAUTO_DEPLOY=true\nDRY_RUN_DEFAULT=false\nCENTRAL_CONFIG_SYNC=true\nAUTO_SYNC=true\nSELF_EXPANDING_MODE=true\n",
    encoding="utf-8",
)

print("Waiting for Watchdog/AutoSync...")
time.sleep(5)  # Wait for file watcher

# 3. Check Updated State (Should be False)
if not check_config(False):
    print(
        "⚠️ Hot reload didn't trigger automatically (expected on some envs sans watchdog). Manual trigger check?"
    )
    sys.exit(1)

# 4. Restore Default (Set True)
print("\n--- Check 3: Restoring Safe Default ---")
pathlib.Path(ENV_FILE).write_text(
    "ENVIRONMENT=dev\nAUTO_DEPLOY=true\nDRY_RUN_DEFAULT=true\nCENTRAL_CONFIG_SYNC=true\nAUTO_SYNC=true\nSELF_EXPANDING_MODE=true\n",
    encoding="utf-8",
)
time.sleep(2)
check_config(True)
