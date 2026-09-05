#!/usr/bin/env python3
"""Summarize mutmut mutation metadata without importing mutmut internals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TypedDict

KILLED_EXIT_CODES = {1, 3, -24}


class MutationRow(TypedDict):
    source: str
    tested: int
    killed: int
    survived: int


TARGETS = (
    "hyodo/__init__.py",
    "hyodo/safety.py",
    "hyodo/events.py",
    "hyodo/exceptions.py",
)


def summarize(mutants_dir: Path) -> tuple[list[MutationRow], int]:
    rows: list[MutationRow] = []
    for source in TARGETS:
        meta_path = mutants_dir / f"{source}.meta"
        if not meta_path.exists():
            rows.append({"source": source, "tested": 0, "killed": 0, "survived": 0})
            continue
        payload = json.loads(meta_path.read_text())
        exit_codes = payload.get("exit_code_by_key", {})
        killed = sum(code in KILLED_EXIT_CODES for code in exit_codes.values())
        survived = sum(code == 0 for code in exit_codes.values())
        rows.append(
            {
                "source": source,
                "tested": killed + survived,
                "killed": killed,
                "survived": survived,
            }
        )

    total_tested = sum(int(row["tested"]) for row in rows)
    return rows, total_tested


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutants-dir", type=Path, default=Path("mutants"))
    parser.add_argument(
        "--generated",
        type=int,
        required=True,
        help="Total mutations reported by the mutmut run.",
    )
    args = parser.parse_args()

    rows, tested = summarize(args.mutants_dir)
    killed = sum(int(row["killed"]) for row in rows)
    survived = sum(int(row["survived"]) for row in rows)
    no_tests = args.generated - tested
    if no_tests < 0:
        raise SystemExit("--generated is smaller than the mutation metadata total")

    print("source,tested,killed,survived")
    for row in rows:
        print(f"{row['source']},{row['tested']},{row['killed']},{row['survived']}")
    print(f"TOTAL,{tested},{killed},{survived}")
    print(f"GENERATED,{args.generated},,,")
    print(f"NO_TESTS,{no_tests},,,")
    print(f"KILL_RATE_TESTED,{killed / tested * 100:.2f}%" if tested else "KILL_RATE_TESTED,N/A")
    print(
        f"KILL_RATE_ALL,{killed / args.generated * 100:.2f}%"
        if args.generated
        else "KILL_RATE_ALL,N/A"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
