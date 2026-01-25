#!/usr/bin/env python3
"""Sync Phase 3 Issue Sync Map statuses in TICKETS.md."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import date
from pathlib import Path

SECTION_HEADER = "## \ud83d\udd17 Phase 3 Issue Sync Map"
STATUS_LINE_PREFIX = "> \uc0c1\ud0dc \uae30\uc900: GitHub \uc774\uc288 \uc0c1\ud0dc"


def load_issue_states(json_path: Path | None) -> dict[str, str]:
    if json_path:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    else:
        gh_path = None
        env_path = os.environ.get("GH_PATH")
        if env_path and Path(env_path).exists():
            gh_path = env_path
        if not gh_path:
            gh_path = shutil.which("gh")
        if not gh_path:
            for candidate in ("/opt/homebrew/bin/gh", "/usr/local/bin/gh", "/usr/bin/gh"):
                if Path(candidate).exists():
                    gh_path = candidate
                    break
        if not gh_path:
            raise FileNotFoundError("gh CLI not found in PATH or common locations")

        result = subprocess.run(
            [gh_path, "issue", "list", "-L", "200", "--json", "number,state"],
            check=True,
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)

    return {f"#{item['number']}": item["state"] for item in data}


def update_issue_sync_map(contents: str, issue_states: dict[str, str]) -> str:
    lines = contents.splitlines()
    today = date.today().isoformat()
    updated_lines: list[str] = []

    in_section = False
    in_table = False

    for line in lines:
        if line.startswith(SECTION_HEADER):
            in_section = True
            in_table = False
            updated_lines.append(line)
            continue

        if in_section and line.startswith(STATUS_LINE_PREFIX):
            updated_lines.append(
                f"> \uc0c1\ud0dc \uae30\uc900: GitHub \uc774\uc288 \uc0c1\ud0dc (OPEN/CLOSED). \ub9c8\uc9c0\ub9c9 \ub3d9\uae30\ud654: {today}."
            )
            continue

        if in_section and line.startswith("| Layer"):
            in_table = True
            updated_lines.append(line)
            continue

        if in_section and line.startswith("| ---"):
            updated_lines.append(line)
            continue

        if in_section and in_table:
            if not line.startswith("|"):
                in_table = False
                in_section = False
                updated_lines.append(line)
                continue

            columns = [col.strip() for col in line.strip().strip("|").split("|")]
            if len(columns) >= 5:
                issue = columns[2]
                if issue in issue_states:
                    columns[3] = issue_states[issue]
                elif issue not in {"TBD", ""}:
                    columns[3] = "UNKNOWN"
                line = "| " + " | ".join(columns) + " |"

            updated_lines.append(line)
            continue

        updated_lines.append(line)

    return "\n".join(updated_lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Phase 3 Issue Sync Map")
    parser.add_argument(
        "--tickets",
        default="TICKETS.md",
        help="Path to TICKETS.md (default: TICKETS.md)",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        help="Path to issue list JSON (skip gh call)",
    )
    args = parser.parse_args()

    tickets_path = Path(args.tickets)
    issue_states = load_issue_states(Path(args.json_path) if args.json_path else None)

    contents = tickets_path.read_text(encoding="utf-8")
    updated = update_issue_sync_map(contents, issue_states)
    changed = updated != contents
    if changed:
        tickets_path.write_text(updated, encoding="utf-8")
    print(f"sync_phase3_issue_map: updated={changed} tickets={tickets_path}")


if __name__ == "__main__":
    main()
