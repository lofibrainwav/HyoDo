import socket
import subprocess
import sys
import time
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

REQUIRED_CONTAINERS = {"afo-postgres": {"port": 15432}, "afo-redis": {"port": 6379}}


def check_docker_running() -> None:
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def check_port(host, port, timeout=2) -> None:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (TimeoutError, ConnectionRefusedError):
        return False


def main() -> None:
    print(f"{YELLOW}🐳 Checking Container Health (Phase 45)...{RESET}")

    # 1. Check Docker Daemon
    if not check_docker_running():
        print(f"{RED}❌ Docker is not running! Please start Docker Desktop.{RESET}")
        sys.exit(1)

    print(f"{GREEN}✔ Docker is running.{RESET}")

    # 2. Check Container Status
    all_healthy = True

    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}|{{.Status}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        running_containers = {}
        for line in result.stdout.strip().split("\n"):
            if line:
                name, status = line.split("|")
                running_containers[name] = status

        for name, config in REQUIRED_CONTAINERS.items():
            if name in running_containers:
                status = running_containers[name]
                print(f"{GREEN}✔ Container '{name}' is running ({status}).{RESET}")

                # 3. Check Port Connectivity
                port = config["port"]
                if check_port("localhost", port):
                    print(f"{GREEN}  ✔ Port {port} is accessible.{RESET}")
                else:
                    print(f"{RED}  ❌ Port {port} is NOT accessible!{RESET}")
                    all_healthy = False
            else:
                print(f"{RED}❌ Container '{name}' is NOT running.{RESET}")
                all_healthy = False

    except Exception as e:
        print(f"{RED}❌ Error checking containers: {e}{RESET}")
        all_healthy = False

    if all_healthy:
        print(f"\n{GREEN}✨ All Core Infrastructure is Healthy! (善){RESET}")
        sys.exit(0)
    else:
        print(f"\n{RED}⚠️ Some services are missing or unhealthy.{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
