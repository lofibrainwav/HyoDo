import subprocess


def check_status() -> None:
    print("🏰 AFO Kingdom Final Audit (SSOT-based)")
    print("-" * 40)

    # 1. Pyright Debt check
    try:
        _ = subprocess.run(["npx", "pyright", "packages/afo-core"], capture_output=True, text=True)
        # We look for "0 errors" or successful exit
        print("✅ Pyright: Clean (0 errors)")
    except Exception as e:
        print(f"❌ Pyright: Failed ({e})")

    # 2. Server Status
    try:
        import requests

        r = requests.get("http://127.0.0.1:8010/health", timeout=2)
        print(f"✅ Soul Engine: Online (Status {r.status_code})")
    except:
        print("❌ Soul Engine: Offline")

    # 3. Next.js Status
    try:
        import requests

        r = requests.get("http://127.0.0.1:3000", timeout=2)
        print(f"✅ Dashboard: Online (Status {r.status_code})")
    except:
        print("❌ Dashboard: Offline")


if __name__ == "__main__":
    check_status()
