#!/usr/bin/env python3
"""
🛡️ AFO Kingdom Container Security Audit Script
Phase 47: Network Security Hardening (TICKET-066)

Checks containers against security best practices (CIS Benchmark subsets):
- Root user execution
- Use of privileged mode
- Read-only root filesystem
- Resource limits (Memory/CPU)
"""

import json
import subprocess
import sys
from typing import Any, Dict, List

CONTAINERS = ["afo-postgres", "afo-redis", "afo-ollama"]


def run_command(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def inspect_container(container_name: str) -> Dict[str, Any]:
    cmd = ["docker", "inspect", container_name]
    result = run_command(cmd)
    if result.returncode != 0:
        return {}
    data = json.loads(result.stdout)
    return data[0] if data else {}


def audit_container(name: str) -> Dict[str, Any]:
    print(f"\n🔍 Auditing {name}...")
    info = inspect_container(name)
    if not info:
        print(f"⚠️  Container {name} not found or not running.")
        return {"score": 0, "checks": []}

    config = info.get("Config", {})
    host_config = info.get("HostConfig", {})

    checks = []
    score = 0
    max_score = 4

    # 1. User Check (Should not be root/0)
    user = config.get("User", "")
    if user and user not in ["0", "root"]:
        checks.append("✅ Running as non-root user")
        score += 1
    else:
        checks.append("❌ Running as root (Risk: High)")

    # 2. Privileged Mode
    privileged = host_config.get("Privileged", False)
    if not privileged:
        checks.append("✅ Privileged mode disabled")
        score += 1
    else:
        checks.append("❌ Privileged mode enabled (Risk: Critical)")

    # 3. Read-Only Root Filesystem
    readonly = host_config.get("ReadonlyRootfs", False)
    if readonly:
        checks.append("✅ Root filesystem is read-only")
        score += 1
    else:
        checks.append("⚠️  Root filesystem is writable (Risk: Medium)")

    # 4. Resource Limits (Memory)
    memory = host_config.get("Memory", 0)
    if memory > 0:
        checks.append("✅ Memory limit set")
        score += 1
    else:
        checks.append("⚠️  No memory limit set (Risk: Low)")

    print("\n".join(checks))
    return {"score": score, "max_score": max_score, "checks": checks}


def main() -> None:
    print("🛡️ Starting Phase 47 Container Security Audit...")

    total_score = 0
    total_max = 0

    for container in CONTAINERS:
        result = audit_container(container)
        if result.get("max_score"):
            total_score += result["score"]
            total_max += result["max_score"]

    if total_max > 0:
        final_percentage = (total_score / total_max) * 100
        print(
            f"\n📊 Audit Complete. Security Score: {total_score}/{total_max} ({final_percentage:.1f}%)"
        )

        if final_percentage < 80:
            print("❌ Security Score below 80%. Hardening required.")
            sys.exit(1)
        else:
            print("✅ Security Score Acceptable.")
    else:
        print("\n⚠️  No containers audited.")


if __name__ == "__main__":
    main()
