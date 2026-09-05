#!/usr/bin/env python3
"""Summarize mutmut 3.7.x metadata without importing mutmut internals.

The status map mirrors mutmut 3.7.0. Mutation-tool versions are pinned in the
`mutation` extra so a receipt cannot silently change meaning after an upgrade.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import TypeAlias

ExitCode: TypeAlias = int | None

TARGETS = (
    "hyodo/__init__.py",
    "hyodo/safety.py",
    "hyodo/events.py",
    "hyodo/exceptions.py",
)

STATUS_ORDER = (
    "killed",
    "survived",
    "no_tests",
    "not_checked",
    "timeout",
    "skipped",
    "caught_by_type_check",
    "segfault",
    "interrupted",
    "suspicious",
)

# Mirrors mutmut 3.7.0 status_by_exit_code. Note that -24 is timeout: mutmut's
# source contains an earlier duplicate -24 entry, but the later dict key wins.
STATUS_BY_EXIT_CODE: dict[ExitCode, str] = {
    1: "killed",
    3: "killed",
    0: "survived",
    5: "no_tests",
    33: "no_tests",
    None: "not_checked",
    -24: "timeout",
    24: "timeout",
    36: "timeout",
    152: "timeout",
    255: "timeout",
    34: "skipped",
    37: "caught_by_type_check",
    -11: "segfault",
    -9: "segfault",
    2: "interrupted",
    35: "suspicious",
}


def classify_exit_code(code: ExitCode) -> str:
    """Return the explicit mutmut status; unknown codes are suspicious."""
    return STATUS_BY_EXIT_CODE.get(code, "suspicious")


def _read_exit_codes(meta_path: Path) -> dict[str, ExitCode]:
    if not meta_path.is_file():
        raise FileNotFoundError(f"missing mutmut metadata: {meta_path}")
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    exit_codes = payload.get("exit_code_by_key")
    if not isinstance(exit_codes, dict):
        raise ValueError(f"invalid mutmut metadata: {meta_path} has no exit_code_by_key mapping")
    return exit_codes


def summarize(mutants_dir: Path) -> tuple[list[tuple[str, Counter[str]]], Counter[str]]:
    """Return per-source and aggregate status counts for every generated mutant."""
    rows: list[tuple[str, Counter[str]]] = []
    total: Counter[str] = Counter()
    for source in TARGETS:
        exit_codes = _read_exit_codes(mutants_dir / f"{source}.meta")
        counts: Counter[str] = Counter(classify_exit_code(code) for code in exit_codes.values())
        counts["generated"] = len(exit_codes)
        rows.append((source, counts))
        total.update(counts)
    return rows, total


def _rate(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator * 100:.2f}%" if denominator else "N/A"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutants-dir", type=Path, default=Path("mutants"))
    parser.add_argument(
        "--generated",
        type=int,
        help="Optional expected generated count; mismatch is an error, not a correction.",
    )
    args = parser.parse_args()

    try:
        rows, total = summarize(args.mutants_dir)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    generated = total["generated"]
    if args.generated is not None and args.generated != generated:
        raise SystemExit(
            f"--generated={args.generated} disagrees with metadata-generated count {generated}"
        )

    columns = ("generated", *STATUS_ORDER)
    print("source," + ",".join(columns))
    for source, counts in rows:
        print(source + "," + ",".join(str(counts[column]) for column in columns))
    print("TOTAL," + ",".join(str(total[column]) for column in columns))

    tested = total["killed"] + total["survived"]
    indeterminate = generated - tested
    print(f"TESTED,{tested}")
    print(f"INDETERMINATE_OR_OTHER,{indeterminate}")
    print(f"KILL_RATE_TESTED,{_rate(total['killed'], tested)}")
    print(f"KILL_RATE_ALL_GENERATED,{_rate(total['killed'], generated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
