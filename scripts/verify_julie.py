import sys

import requests

BASE_URL = "http://localhost:8010/api/finance"


def verify_dashboard() -> None:
    print("running: verify_dashboard...")
    try:
        res = requests.get(f"{BASE_URL}/dashboard")
        if res.status_code != 200:
            print(f"FAILED: Dashboard returned {res.status_code}")
            return False

        data = res.json()
        print(
            f"Dashboard Data: Health={data.get('financial_health_score')}, Advice='{data.get('advice')[:30]}...'"
        )

        # Note: 'advice' might be the key, checking source.

        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def verify_dry_run() -> None:
    print("\nrunning: verify_dry_run...")
    payload = {
        "account_id": "KB-1234",
        "merchant": "Verification Bot",
        "amount": 50000,
        "category": "Test",
        "description": "Dry Run Test",
    }

    try:
        res = requests.post(f"{BASE_URL}/transaction/dry-run", json=payload)
        if res.status_code != 200:
            print(f"FAILED: Dry Run returned {res.status_code} - {res.text}")
            return False

        data = res.json()
        print(f"Dry Run Result: Success={data.get('success')}, Mode={data.get('mode')}")

        if data.get("mode") != "DRY_RUN":
            print("FAILED: Mode is not DRY_RUN")
            return False

        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


if __name__ == "__main__":
    print("🛡️  Julie CPA Verification Started")
    d_ok = verify_dashboard()
    t_ok = verify_dry_run()

    if d_ok and t_ok:
        print("\n✅ All Checks Passed: Julie is guarding the ledger.")
        sys.exit(0)
    else:
        print("\n❌ Verification Failed.")
        sys.exit(1)
