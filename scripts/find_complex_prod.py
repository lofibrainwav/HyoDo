#!/usr/bin/env python3
"""Radon 복잡도 리포트에서 프로덕션 고복잡도 함수 추출."""

import re
from pathlib import Path
from typing import Any

EXCLUDE_DIRS = [
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "legacy",
    "archived",
    "dist",
    "build",
    "tests",
    "site-packages",
]
COMPLEXITY_PATTERN = re.compile(
    r"^\s*(?P<type>[FMCO])\s+(?P<line>\d+):(?P<col>\d+)\s+"
    r"(?P<name>.+?)\s+-\s+(?P<grade>[A-F])\s+\((?P<score>\d+)\)"
)


def find_complex() -> None:
    """Radon 리포트에서 C/D/E/F 등급 고복잡도 함수 목록 출력."""
    r_rep = Path("radon_full_report.txt")
    if not r_rep.exists():
        return

    complex_items: list[dict[str, Any]] = []
    current_file = ""
    is_prod = False

    for line in r_rep.read_text().splitlines():
        if not line.startswith(" "):
            current_file = line.strip()
            is_prod = not any(ex in current_file for ex in EXCLUDE_DIRS)
            continue

        if is_prod:
            m = COMPLEXITY_PATTERN.match(line)
            if m:
                item = m.groupdict()
                item["file"] = current_file
                if item["grade"] in ["C", "D", "E", "F"]:
                    complex_items.append(item)

    complex_items.sort(key=lambda x: int(x["score"]), reverse=True)

    print("Top 20 REAL Production Complex Items:")
    for item in complex_items[:20]:
        print(
            f"[{item['grade']}] Score {item['score']}: "
            f"{item['name']} ({item['file']}:{item['line']})"
        )


if __name__ == "__main__":
    find_complex()
