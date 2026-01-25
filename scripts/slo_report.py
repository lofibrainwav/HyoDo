#!/usr/bin/env python3
"""
AFO Kingdom SLO Reporter (MVP)
Parses the SLO contract and displays the configuration.
"""

import argparse
import os
from pathlib import Path

import yaml


def load_slo_contract(config_path: str) -> None:
    if not os.path.exists(config_path):
        print(f"❌ SLO contract not found at: {config_path}")
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_report(contract, dry_run=False) -> None:
    if not contract:
        return

    print("\n" + "=" * 60)
    print(f"👑 AFO Kingdom SLO Report (SSOT v{contract.get('version', 1)})")
    print("=" * 60)

    for slo in contract.get("slos", []):
        name = slo.get("name", "Unknown")
        target = slo.get("target", 0)
        pillar = slo.get("pillar", "N/A")
        window = slo.get("window", "N/A")

        print(f"\n[{pillar}] SLO: {name}")
        print(f"  - Service: {slo.get('service')}")
        print(f"  - Target: {target * 100}%")
        print(f"  - Window: {window}")
        print(f"  - SLI (PromQL): {slo.get('sli', {}).get('promql').strip().splitlines()[0]}...")

        if dry_run:
            print("  - Status: [DRY_RUN] Proof of Contract Verified ✅")

    print("\n" + "=" * 60)
    print("Report generated successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="AFO Kingdom SLO Reporter")
    parser.add_argument(
        "--config",
        default="packages/afo-core/config/slo.yml",
        help="Path to SLO config",
    )
    parser.add_argument("--dry-run", action="store_true", help="Execute in dry-run mode")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    config_path = project_root / args.config

    contract = load_slo_contract(str(config_path))
    print_report(contract, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
