#!/usr/bin/env python3
"""Keep KINGDOM/AFO runtime material out of HyoDo's public package."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "hyodo"
FORBIDDEN = re.compile(
    r"afo_core|api_wallet|(?:from|import)\s+kingdom(?:\.|\s|$)|kingdom/",
    re.IGNORECASE,
)


def main() -> int:
    failures: list[str] = []
    for path in sorted(ROOT.rglob("*.py")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if FORBIDDEN.search(line):
                failures.append(f"{path.relative_to(ROOT.parent)}:{line_number}")
    if failures:
        print("FAIL: HyoDo public package contains KINGDOM/AFO boundary reference")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS: HyoDo public package boundary is free of AFO/KINGDOM runtime references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
