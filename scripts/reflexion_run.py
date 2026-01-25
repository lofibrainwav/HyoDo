#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add package root to sys.path if needed
sys.path.append(str(Path(__file__).resolve().parent.parent / "packages" / "afo-core"))

from AFO.self_expansion.contracts import load_reflexion_contract
from AFO.self_expansion.reflexion_runner import run_reflexion


def main() -> int:
    ap = argparse.ArgumentParser(description="AFO Reflection Runner CLI")
    ap.add_argument(
        "--contract",
        default="packages/afo-core/config/reflexion.yml",
        help="Path to contract YAML",
    )
    ap.add_argument("--input", required=True, help="Input prompt for reflection")
    ap.add_argument("--dry-run", action="store_true", help="Force dry-run mode")
    args = ap.parse_args()

    # SSOT: Load contract
    try:
        contract_path = Path(args.contract)
        contract = load_reflexion_contract(contract_path)
    except Exception as e:
        print(f"❌ Error loading contract: {e}", file=sys.stderr)
        return 1

    # Safety: Use contract default for dry-run if not provided
    dry = True if args.dry_run else bool(contract.dry_run_default)

    # Execute
    try:
        out = run_reflexion(args.input, contract, dry_run=dry)
        # Indisputable evidence output (JSON)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"❌ Execution failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
