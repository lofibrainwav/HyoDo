import sys

import requests

API_BASE = "http://localhost:8012"


def test_kingdom_status() -> None:
    print(f"Testing {API_BASE}/api/system/kingdom-status...")
    try:
        res = requests.get(f"{API_BASE}/api/system/kingdom-status")
        res.raise_for_status()
        data = res.json()

        print("\n[Kingdom Status Result]")
        print(f"Heartbeat: {data.get('heartbeat')}")
        print(f"Dependency Count: {data.get('dependency_count')}")

        pillars = data.get("pillars", [])
        print("Pillars:")
        for p in pillars:
            print(f"  - {p['name']}: {p['score']}")

        scholars = data.get("scholars", [])
        print("Scholars:")
        for s in scholars:
            print(f"  - {s['name']}: {s['status']}")

        trinity_score = data.get("trinity_score")
        print(f"Trinity Score: {trinity_score}")

        if not pillars or not scholars:
            print("❌ Failed: Pillars or Scholars missing")
            return False

        if trinity_score is None:
            print("❌ Failed: Trinity Score missing")
            return False

        print("✅ Kingdom Status Verified")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_dry_run() -> None:
    skill_id = "test_skill_001"
    print(f"\nTesting {API_BASE}/api/skills/execute/{skill_id}/dry-run...")
    try:
        res = requests.post(f"{API_BASE}/api/skills/execute/{skill_id}/dry-run")
        res.raise_for_status()
        data = res.json()

        print("\n[Dry Run Result]")
        print(f"Status: {data.get('status')}")
        print(f"Projected Impact: {data.get('predicted_impact')}")
        print(f"Projected Score: {data.get('projected_score')}")

        if data.get("dry_run") is not True:
            print("❌ Failed: dry_run flag missing")
            return False

        print("✅ Dry Run Verified")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


if __name__ == "__main__":
    status_ok = test_kingdom_status()
    dry_run_ok = test_dry_run()

    if status_ok and dry_run_ok:
        sys.exit(0)
    else:
        sys.exit(1)
