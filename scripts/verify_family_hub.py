"""
Family Hub OS Verification Script
眞 (Truth): 실제 API 호출을 통한 기능 검증
"""

import json
import time

import requests

BASE_URL = "http://localhost:8010"


def print_step(msg) -> None:
    print(f"\n🔹 {msg}")


def verify_family_hub() -> None:
    print("🚀 Starting Family Hub Verification...")

    # 1. Health Check
    print_step("Checking Family Hub Health...")
    try:
        res = requests.get(f"{BASE_URL}/family/health")
        print(f"Status: {res.status_code}")
        print(json.dumps(res.json(), indent=2, ensure_ascii=False))
        assert res.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return

    # 2. List Members
    print_step("Listing Family Members...")
    res = requests.get(f"{BASE_URL}/family/members")
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))

    # 3. Add Member
    print_step("Adding New Member (Mireu)...")
    new_member = {
        "id": "mireu",
        "name": "Mireu (Baby Dragon)",
        "role": "Pet",
        "status": "Playing",
        "current_location": "Garden",
    }
    res = requests.post(f"{BASE_URL}/family/members", json=new_member)
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    assert res.status_code == 200

    # 4. Log Activity
    print_step("Logging Activity (Playing)...")
    activity = {
        "member_id": "mireu",
        "type": "Play",
        "description": "Playing with fireballs",
    }
    res = requests.post(f"{BASE_URL}/family/activity", json=activity)
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    assert res.status_code == 200

    # 5. Check Happiness Impact
    print_step("Checking Happiness Score...")
    res = requests.get(f"{BASE_URL}/family/happiness")
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    assert res.json()["happiness_score"] > 50.0  # Should increase from default 50

    # 6. Verify Persona Switch Integration
    print_step("Switching Persona (Juyu) & Checking Log...")
    switch_req = {"persona_id": "juyu"}
    res = requests.post(f"{BASE_URL}/api/personas/switch", json=switch_req)
    print(f"Switch Status: {res.status_code}")

    # Check timeline for switch event
    time.sleep(1)  # Allow async write
    res = requests.get(f"{BASE_URL}/family/timeline")
    data = res.json()
    last_activity = data["activities"][-1]
    print("Last Activity:", json.dumps(last_activity, indent=2, ensure_ascii=False))

    if last_activity["type"] == "PersonaSwitch" and "주유" in last_activity["description"]:
        print("✅ Persona Switch Logging Verified!")
    else:
        print("⚠️ Persona Switch Logging NOT found in last activity.")

    print("\n🎉 Verification Complete!")


if __name__ == "__main__":
    verify_family_hub()
