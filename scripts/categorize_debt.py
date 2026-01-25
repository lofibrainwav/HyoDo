#!/usr/bin/env python3
"""Vulture 리포트 기반 Dead Code 분류 도구."""

import json
import re
from pathlib import Path
from typing import Any

EXCLUDE_DIRS = [".git", ".venv", "node_modules", "legacy", "archived", "dist", "build", "tests"]
DEBT_PATTERN = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+): unused (?P<type>\w+) '(?P<name>.+?)' \((?P<conf>\d+)% confidence\)"
)


def categorize_debt() -> None:
    """Vulture 리포트를 분석하여 Dead Code를 Zone별로 분류."""
    report = Path("vulture_report.txt")
    if not report.exists():
        return

    zones: dict[str, list[dict[str, Any]]] = {
        "strike_zone_1": [],
        "strike_zone_2": [],
        "review_zone": [],
    }

    for line in report.read_text().splitlines():
        if any(ex in line for ex in EXCLUDE_DIRS):
            continue
        m = DEBT_PATTERN.match(line)
        if m:
            hit: dict[str, Any] = {
                "path": m.group("path"),
                "line": int(m.group("line")),
                "type": m.group("type"),
                "name": m.group("name"),
                "conf": int(m.group("conf")),
            }

            if hit["type"] in ["function", "method"] and hit["conf"] >= 90:
                zones["strike_zone_2"].append(hit)
            elif hit["type"] in ["import", "variable", "attribute"]:
                zones["strike_zone_1"].append(hit)
            else:
                zones["review_zone"].append(hit)

    Path("scripts/debt_categorization.json").write_text(
        json.dumps(zones, indent=2), encoding="utf-8"
    )

    print("Production Dead Code:")
    print(f"  - Strike Zone 1 (Small Items): {len(zones['strike_zone_1'])}")
    print(f"  - Strike Zone 2 (Functions/Methods): {len(zones['strike_zone_2'])}")
    print(f"  - Review Zone: {len(zones['review_zone'])}")


if __name__ == "__main__":
    categorize_debt()
