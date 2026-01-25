import os
import secrets
import signal
import subprocess
import sys
import time

import requests

# Configuration
PORT = 8040
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"
PROCESS = None


def start_server() -> None:
    global PROCESS
    print(f"🚀 Starting API Server on port {PORT}...")
    env = os.environ.copy()
    # Assuming script is run from project root, add packages/afo-core to path
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "packages/afo-core")
    env["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))

    # Run uvicorn as subprocess
    log_file = open("server_output.txt", "w")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "AFO.api_server:app",
        "--host",
        HOST,
        "--port",
        str(PORT),
        "--log-level",
        "debug",
    ]

    PROCESS = subprocess.Popen(cmd, env=env, stdout=log_file, stderr=subprocess.STDOUT)

    # Wait for startup
    attempts = 0
    max_attempts = 30
    while attempts < max_attempts:
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=1)
            if resp.status_code == 200:
                print("\n✅ Server is UP and healthy!")
                # Wait a bit more for background tasks to settle
                time.sleep(2)
                return True
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            print(f"Error connecting: {e}")

        # Check if process is still alive
        if PROCESS.poll() is not None:
            print("\n❌ Server process died unexpectedly")
            break

        time.sleep(1)
        print(".", end="", flush=True)
        attempts += 1

    print("\n❌ Server failed to start within timeout")
    kill_server()
    # Print stderr for debugging
    print("Server Error Output:")
    try:
        with open("server_output.txt") as f:
            print(f.read())
    except:
        print("Could not read server_output.txt")
    return False


def check_endpoint(name, path, expected_status=200) -> None:
    try:
        url = f"{BASE_URL}{path}"
        print(f"\n📡 Probing {name} ({path})...")
        resp = requests.get(url, timeout=2)
        if resp.status_code == expected_status:
            print(f"   ✅ {name}: OK ({resp.status_code})")
            return True
        else:
            print(f"   ❌ {name}: Failed ({resp.status_code})")
            print(f"      Response: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ {name}: Error {e}")
        return False


def check_post_endpoint(name, path, json_data, expected_status=200) -> None:
    try:
        url = f"{BASE_URL}{path}"
        print(f"\n📡 Probing POST {name} ({path})...")
        resp = requests.post(url, json=json_data, timeout=2)
        # Accept 200 OK or 201 Created
        if resp.status_code == expected_status or resp.status_code == 201:
            print(f"   ✅ {name}: OK ({resp.status_code})")
            return True
        else:
            print(f"   ❌ {name}: Failed ({resp.status_code})")
            print(f"      Response: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ {name}: Error {e}")
        return False


def kill_server() -> None:
    if PROCESS:
        print("\n🛑 Stopping Server...")
        PROCESS.terminate()
        try:
            PROCESS.wait(timeout=5)
        except:
            PROCESS.kill()


if __name__ == "__main__":
    try:
        if start_server():
            # Test Critical Routers (GET)
            checks = [
                ("Chancellor (5 Pillars)", "/api/5pillars/current"),
                ("Skills Registry", "/api/skills/health"),
                ("Graph of Thought", "/api/got/health"),
                ("Modal Data", "/api/modal/health"),
                ("Multi-Agent", "/api/multi-agent/health"),
                ("N8N Integration", "/api/n8n/health"),
                ("Trinity Policy", "/api/trinity/policy/health"),
                ("Trinity SBT", "/api/trinity/sbt/health"),
                ("Evolution History", "/api/evolution/history"),
            ]

            success_count = 0
            total_checks = len(checks)

            for name, path in checks:
                if check_endpoint(name, path):
                    success_count += 1

            # Test POST Operations (Critical for 405 Check)
            post_checks = [
                (
                    "Create GoT Graph",
                    "/api/got/graph",
                    {"title": "E2E Test", "initial_thought": "Test"},
                ),
                (
                    "Create Modal",
                    "/api/modal/",
                    {"id": "e2e_test", "title": "Test", "content": "Test Content"},
                ),
            ]

            total_checks += len(post_checks)

            for name, path, data in post_checks:
                if check_post_endpoint(name, path, data):
                    success_count += 1

            print("\n" + "=" * 60)
            print(f"🏁 E2E VERIFICATION RESULT: {success_count}/{total_checks} Endpoints Active")
            if success_count == total_checks:
                print("🏆 ALL SYSTEMS GO - HARDENED AND BATTLE-TESTED")

                # Double Check DGM Engine
                try:
                    r = requests.get(f"{BASE_URL}/api/evolution/history", timeout=2)
                    if r.status_code == 200:
                        print("   ✅ Evolution Router is FULLY ONLINE & RESTORED")
                except:
                    pass

            else:
                print("⚠️  SOME SYSTEMS UNRESPONSIVE")
            print("=" * 60)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        kill_server()
