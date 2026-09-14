#!/usr/bin/env python3
"""Fail closed when the public historical-secret register is not closed."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|.*?\|\s*`(SYNTHETIC|ROTATED|REMOVED_AND_VERIFIED|PENDING_OWNER)`\s*\|\s*$"
)
ALLOWED = {"SYNTHETIC", "ROTATED", "REMOVED_AND_VERIFIED"}


def read_rows(path: Path) -> dict[int, tuple[str, str]]:
    rows: dict[int, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW_RE.match(line)
        if match:
            finding_id = int(match.group(1))
            disposition = match.group(2)
            if finding_id in rows:
                raise ValueError(f"duplicate finding id: {finding_id}")
            rows[finding_id] = (disposition, line)
    return rows


def check(path: Path, expected_count: int) -> list[str]:
    try:
        rows = read_rows(path)
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"register unreadable or invalid: {exc}"]

    expected_ids = set(range(1, expected_count + 1))
    errors: list[str] = []
    missing = sorted(expected_ids - rows.keys())
    extra = sorted(rows.keys() - expected_ids)
    if missing:
        errors.append(f"missing finding IDs: {missing}")
    if extra:
        errors.append(f"unexpected finding IDs: {extra}")

    for finding_id in sorted(rows):
        disposition, line = rows[finding_id]
        if disposition == "PENDING_OWNER":
            errors.append(f"finding {finding_id}: PENDING_OWNER")
        elif disposition not in ALLOWED:
            errors.append(f"finding {finding_id}: unsupported disposition")
        if disposition == "SYNTHETIC" and "synthetic" not in line.lower():
            errors.append(f"finding {finding_id}: SYNTHETIC lacks a reason")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("register", type=Path)
    parser.add_argument("--expected-count", type=int, default=16)
    args = parser.parse_args()

    errors = check(args.register, args.expected_count)
    if errors:
        print("FAIL: historical-secret disposition gate")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: historical-secret disposition gate ({args.expected_count} findings closed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
