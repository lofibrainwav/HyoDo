#!/usr/bin/env python3
"""
🌐 AFO Kingdom Docker Network Migration Script
Phase 47: Network Security Hardening (TICKET-065)

This script migrates AFO containers from the default 'bridge' network
to a secure, user-defined 'afo-network'.
"""

import json
import subprocess
import sys
from typing import List

NETWORK_NAME = "afo-network"
CONTAINERS = {
    "afo-postgres": "postgres",
    "afo-redis": "redis",
    "afo-ollama": "ollama",  # Future proofing
}


def run_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"   Error: {e.stderr.strip()}")
        if check:
            sys.exit(1)
        return e


def check_network_exists() -> bool:
    print(f"🔍 Checking for network '{NETWORK_NAME}'...")
    cmd = ["docker", "network", "inspect", NETWORK_NAME]
    result = run_command(cmd, check=False)
    return result.returncode == 0


def create_network() -> None:
    print(f"🛠️ Creating network '{NETWORK_NAME}'...")
    cmd = ["docker", "network", "create", "--driver", "bridge", NETWORK_NAME]
    run_command(cmd)
    print(f"✅ Network '{NETWORK_NAME}' created.")


def get_connected_networks(container_name: str) -> List[str]:
    cmd = ["docker", "inspect", container_name]
    result = run_command(cmd, check=False)
    if result.returncode != 0:
        return []

    data = json.loads(result.stdout)
    if not data:
        return []

    networks = data[0]["NetworkSettings"]["Networks"].keys()
    return list(networks)


def migrate_container(container_name: str, alias: str) -> None:
    print(f"\n🐳 Processing container: {container_name}")

    # Check if container is running
    cmd = ["docker", "ps", "-q", "-f", f"name={container_name}"]
    if not run_command(cmd).stdout.strip():
        print(f"⚠️  Container {container_name} is not running. Skipping.")
        return

    current_networks = get_connected_networks(container_name)

    # Connect if not connected
    if NETWORK_NAME not in current_networks:
        print(f"🔗 Connecting {container_name} to {NETWORK_NAME} (alias: {alias})...")
        cmd = [
            "docker",
            "network",
            "connect",
            "--alias",
            alias,
            NETWORK_NAME,
            container_name,
        ]
        run_command(cmd)
        print("   Connected.")
    else:
        print(f"   Already connected to {NETWORK_NAME}.")

    # Disconnect from default bridge if connected
    if "bridge" in current_networks:
        print(f"✂️  Disconnecting {container_name} from default 'bridge'...")
        cmd = ["docker", "network", "disconnect", "bridge", container_name]
        run_command(cmd)
        print("   Disconnected from bridge.")


def verify_migration() -> None:
    print("\n🕵️ Verifying Network Status...")
    cmd = ["docker", "network", "inspect", NETWORK_NAME]
    result = run_command(cmd)
    data = json.loads(result.stdout)

    connected_containers = data[0]["Containers"]
    if not connected_containers:
        print("⚠️  No containers found in network.")
        return

    print(f"✅ Found {len(connected_containers)} containers in {NETWORK_NAME}:")
    for cid, info in connected_containers.items():
        print(f"   - {info['Name']} ({info['IPv4Address']})")


def main() -> None:
    print("🚀 Starting Phase 47 Network Migration...")

    if not check_network_exists():
        create_network()
    else:
        print(f"✅ Network '{NETWORK_NAME}' already exists.")

    for name, alias in CONTAINERS.items():
        migrate_container(name, alias)

    verify_migration()
    print("\n✅ Migration Complete.")


if __name__ == "__main__":
    main()
