#!/usr/bin/env python3
"""Dead Code 후보의 실제 사용 여부를 ripgrep으로 검증."""

import json
import os
import subprocess
from typing import Any


def scholar_check() -> None:
    """debt_categorization.json의 후보들을 검증하여 안전한 삭제 목록 생성."""
    if not os.path.exists("scripts/debt_categorization.json"):
        return

    with open("scripts/debt_categorization.json") as f:
        zones: dict[str, list[dict[str, Any]]] = json.load(f)

    candidates = zones["review_zone"] + zones["strike_zone_2"]
    safe_to_prune: list[dict[str, Any]] = []

    for c in candidates:
        if c["type"] not in ["function", "method"]:
            continue
        name = c["name"]
        try:
            cmd = (
                f'rg -F "{name}" . '
                f'-g "!{os.path.basename(c["path"])}" '
                f'-g "!legacy/*" -g "!archived/*" -g "!site-packages/*" --count'
            )
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            if not output:
                safe_to_prune.append(c)
        except subprocess.CalledProcessError:
            safe_to_prune.append(c)

    print(f"🎓 Optimized Scholars verified {len(safe_to_prune)} safe deletions.")

    with open("scripts/safe_prune_list.json", "w") as f:
        json.dump(safe_to_prune, f, indent=2)


if __name__ == "__main__":
    scholar_check()
