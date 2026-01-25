import json
import sys

import requests


def verify_dashboard_integration() -> None:
    url = "http://localhost:8010/chancellor/invoke"
    payload = {"query": "Status Report", "trinity_score": 0.85, "risk_score": 0.1}
    headers = {"Content-Type": "application/json"}

    print(f"Testing Dashboard API: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")

            # Verify Schema
            required_keys = ["response", "speaker", "full_history"]
            missing = [k for k in required_keys if k not in data]

            if missing:
                print(f"❌ Verification Failed: Missing keys {missing}")
                sys.exit(1)
            else:
                print("✅ Verification Passed: Schema matches Dashboard expectations")
                sys.exit(0)
        else:
            print(f"❌ Verification Failed: HTTP {response.status_code}")
            print(response.text)
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("❌ Verification Failed: Connection Refused. Is the backend running on port 8000?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Verification Failed: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    verify_dashboard_integration()
