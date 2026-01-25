# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
#!/usr/bin/env python3
import subprocess

import requests


def check_port(port, service_name) -> None:
    # Quick socket check or lsof
    try:
        result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
        if result.stdout and "LISTEN" in result.stdout:
            print(f"✅ [PORT {port}] {service_name} is LISTENING.")
            return True
        else:
            print(
                f"❌ [PORT {port}] {service_name} is NOT listening (Output: {result.stdout.strip()[:50]}...)."
            )
            return False
    except Exception as e:
        print(f"⚠️  Port check error: {e}")
        return False


def check_endpoint(url, expected_code=200) -> None:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_code:
            print(f"✅ [API] {url} returned {response.status_code}.")
            # Print preview
            try:
                data = response.json()
                print(f"   Preview: {str(data)[:100]}...")
            except Exception:
                pass
            return True
        else:
            print(f"❌ [API] {url} returned {response.status_code}. Expected {expected_code}.")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ [API] Connection refused to {url}.")
        return False
    except Exception as e:
        print(f"❌ [API] Error checking {url}: {e}")
        return False


def main() -> None:
    print("=== 🛡️ AFO Kingdom / 3-Scholar Verification (Perfect Check) ===")

    # 1. Frontend (Julie)
    frontend_ok = check_port(3005, "AICPA Core (Frontend)")

    # 2. Backend (Soul Engine)
    backend_ok = check_port(8010, "AFO Soul Engine (Backend)")

    # 3. Backend Logic (5 Pillars)
    logic_ok = False
    if backend_ok:
        # Phase 2-4: settings 사용
        try:
            import os
            import sys

            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config.settings import get_settings

            settings = get_settings()
            soul_engine_port = settings.SOUL_ENGINE_PORT
        except Exception:
            try:
                from AFO.config.settings import get_settings

                settings = get_settings()
                soul_engine_port = settings.SOUL_ENGINE_PORT
            except Exception:
                soul_engine_port = int(os.getenv("SOUL_ENGINE_PORT", "8010"))

        logic_ok = check_endpoint(f"http://localhost:{soul_engine_port}/api/5pillars/current")
        hub_ok = check_endpoint(f"http://localhost:{soul_engine_port}/api/5pillars/family/hub")
        logic_ok = logic_ok and hub_ok

    # 4. Critical File Exist Check
    agent_path = os.path.join(os.getcwd(), "afo_soul_engine/agents/five_pillars_agent.py")
    if os.path.exists(agent_path):
        print(f"✅ [FILE] Agent file exists: {agent_path}")
    else:
        print(f"❌ [FILE] MISSING Agent file: {agent_path}")

    # Summary
    print("\n=== 🏁 Final Verdict ===")
    if frontend_ok and backend_ok and logic_ok:
        print("✨ PERFECT STATUS: logical and structural integrity confirmed.")
        sys.exit(0)
    else:
        print("⚠️  WARNING: Some checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
