import subprocess
import sys
import time


def check_image(image_ref) -> None:
    print(f"🔍 Checking for image: {image_ref}...")
    try:
        # Docker manifest inspect is the lightest way
        result = subprocess.run(
            ["docker", "manifest", "inspect", image_ref],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking image: {e}")
        return False


def deploy(host, image_ref) -> None:
    print(f"🚀 Deploying to {host} via SCP...")

    # 1. Clean and Prepare Remote Dir
    setup_cmd = (
        "docker rm -f afo-core-soul-engine afo-soul-engine >/dev/null 2>&1 || true; "
        "docker system prune -f >/dev/null 2>&1 || true; "
        "rm -rf ~/AFO_Kingdom_Clean; "
        "mkdir -p ~/AFO_Kingdom_Clean"
    )
    subprocess.run(["ssh", host, setup_cmd], check=True)

    # 2. SCP Scripts
    print("📦 Uploading scripts...")
    subprocess.run(["scp", "-r", "scripts", f"{host}:~/AFO_Kingdom_Clean/"], check=True)

    # 3. Execute
    print("▶️ Executing verification...")
    remote_cmd = (
        "set -euo pipefail; "
        "cd ~/AFO_Kingdom_Clean; "
        f"AFO_IMAGE_REF='{image_ref}' bash scripts/remote_pull_run_verify.sh"
    )

    cmd = ["ssh", host, remote_cmd]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        print(line, end="")

    process.wait()
    return process.returncode == 0


def main() -> None:
    host = "bb-ai-mcp"
    owner = "lofibrainwav"

    # Get SHA from origin/main
    try:
        subprocess.run(["git", "fetch", "origin", "main"], check=True, capture_output=True)
        sha_proc = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            check=True,
            capture_output=True,
            text=True,
        )
        sha = sha_proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        sys.exit(1)

    image_ref = f"ghcr.io/{owner}/afo-core-soul-engine:{sha}"

    print(f"🎯 Target Image: {image_ref}")

    # Poll for 10 minutes max
    start_time = time.time()
    found = False
    while time.time() - start_time < 600:
        if check_image(image_ref):
            found = True
            break
        print("⏳ Image not found yet. Retrying in 10s...")
        time.sleep(10)

    if not found:
        print("❌ Timeout waiting for image.")
        sys.exit(1)

    print("✅ Image found! Starting deployment.")
    if deploy(host, image_ref):
        print("✅ PHASE 5 ACTION 2 COMPLETE: Double Green!")
        sys.exit(0)
    else:
        print("❌ Deployment Failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
