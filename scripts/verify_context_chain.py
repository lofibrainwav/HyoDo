import requests
import sys
import json

BASE_URL = "https://notebook-bridge.vercel.app/api"
API_KEY = "julie-cpa-2025"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def run_step(name, url_suffix, payload, id_key=None) -> None:
    print(f"\n🧠 [Step: {name}] Requesting...")
    try:
        resp = requests.post(f"{BASE_URL}{url_suffix}", json=payload, headers=HEADERS)
        if resp.status_code != 200:
            print(f"❌ Failed: {resp.status_code} - {resp.text}")
            sys.exit(1)

        data = resp.json()
        print(f"✅ Status: {data.get('status')}")
        print(f"📄 Next Step: {data.get('nextStep')}")

        # Check prompt existence
        prompt = data.get("payload", {}).get("suggestedPrompt")
        if prompt:
            print(f"🗣️  Suggested Prompt (First 50 chars): {prompt[:50]}...")
        else:
            print("⚠️  No suggestedPrompt found!")

        if id_key:
            return data.get(id_key)
        return data

    except Exception as e:
        print(f"❌ Exception: {e}")
        sys.exit(1)


def main() -> None:
    print("🚀 Starting CPA Context Chain Verification...")

    # 1. Analyze
    analysis_id = run_step(
        "Analyze",
        "/cpa/analyze",
        {"clientData": "Verify full chain sync test.", "year": 2025, "focusArea": "General"},
        "analysisId",
    )
    print(f"🔑 Analysis ID: {analysis_id}")

    # 2. Review
    review_id = run_step(
        "Review",
        "/cpa/review",
        {"analysisId": analysis_id, "strategyFocus": "Balanced"},
        "reviewId",
    )
    print(f"🔑 Review ID: {review_id}")

    # 3. Audit
    cert_data = run_step("Audit", "/cpa/audit", {"reviewId": review_id}, "certificateId")
    print(f"🏆 Certificate ID: {cert_data}")

    print("\n✅ CHAIN VERIFICATION COMPLETE!")


if __name__ == "__main__":
    main()
