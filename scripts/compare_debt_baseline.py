#!/usr/bin/env python3
"""Debt Gate: Compare current ruff errors against baseline."""

import json
import os
import pathlib
import re
import sys


def main() -> int:
    baseline_path = pathlib.Path("configs/debt_gate/baseline.json")
    if not baseline_path.exists():
        print("❌ Missing baseline.json at configs/debt_gate/baseline.json")
        return 1

    baseline = json.loads(baseline_path.read_text())
    baseline_count = int(baseline.get("ruff_errors", 0))

    txt = pathlib.Path("ruff_stats.txt").read_text(errors="ignore")
    m = re.search(r"Found\s+(\d+)\s+error", txt)

    if not m:
        current_count = 0
    else:
        current_count = int(m.group(1))

    print(f"📊 Baseline ruff_errors: {baseline_count}")
    print(f"📊 Current  ruff_errors: {current_count}")

    # Write to GITHUB_STEP_SUMMARY if available
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write("### Debt Gate Report (Ruff)\n")
            f.write(f"- **Baseline**: {baseline_count}\n")
            f.write(f"- **Current**: {current_count}\n")
            if current_count > baseline_count:
                f.write(f"❌ **FAILED**: Debt increased by {current_count - baseline_count}\n")
            else:
                f.write(
                    f"✅ **PASSED**: Debt reduced or stable (Δ={current_count - baseline_count})\n"
                )

    if current_count > baseline_count:
        print(
            f"❌ FAILED: legacy debt increased (baseline={baseline_count}, current={current_count})"
        )
        return 1
    else:
        print("✅ PASS: legacy debt did not increase.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
