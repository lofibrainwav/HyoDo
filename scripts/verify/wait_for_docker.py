import os
import sys
import time

# Possible socket paths on macOS
SOCKET_PATHS = ["/var/run/docker.sock", os.path.expanduser("~/.docker/run/docker.sock")]


def check_socket() -> None:
    for path in SOCKET_PATHS:
        if os.path.exists(path):
            return path
    return None


def main() -> None:
    print("⏳ Waiting for Docker Engine to initialize...")
    timeout = 60  # Wait up to 60 seconds
    start_time = time.time()

    while time.time() - start_time < timeout:
        socket_path = check_socket()
        if socket_path:
            print(f"✅ Docker Socket found at: {socket_path}")
            sys.exit(0)

        # Spinning visual
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(2)

    print("\n❌ Timed out waiting for Docker Engine.")
    print("Analysis: Docker Desktop App is running, but the Engine failed to create the socket.")
    print("Action: Please check the Docker icon in your menu bar. Access may need approval.")
    sys.exit(1)


if __name__ == "__main__":
    main()
