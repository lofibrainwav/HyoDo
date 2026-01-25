import requests


def check() -> None:
    print("🏰 AFO Final Audit")

    # Check Soul Engine
    try:
        r = requests.get("http://127.0.0.1:8010/health")
        print(f"✅ Soul Engine: {r.status_code}")
    except:
        print("❌ Soul Engine: Down")

    # Check Debugging Status
    try:
        r = requests.get("http://127.0.0.1:8010/api/debugging/status")
        print(f"✅ Debugging API: {r.json().get('status')}")
    except:
        print("❌ Debugging API: Down")


check()
