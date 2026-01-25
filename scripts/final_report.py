import json
import os
from datetime import datetime


def show() -> None:
    print("=" * 50)
    print("🏰 AFO KINGDOM DEBUGGING SYSTEM: FINAL REPORT")
    print("=" * 50)

    log_file = f"logs/debug_tracking_{datetime.now().strftime('%Y%m%d')}.json"
    if os.path.exists(log_file):
        with open(log_file) as f:
            data = json.load(f)
            latest = data[-1]
            print(f"✅ Report ID: {latest['report_id']}")
            print(f"✅ Trinity Score: {latest['trinity_score']}")
            print(f"✅ Issues Found: {latest['total_errors']}")
            print(f"✅ Execution Time: {latest['execution_time']:.2f}s")
            print(f"✅ Path Verified: {os.path.abspath('.')}")
    else:
        print("❌ No report found on disk.")
    print("=" * 50)


if __name__ == "__main__":
    show()
