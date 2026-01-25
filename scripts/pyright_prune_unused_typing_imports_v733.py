from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path.cwd()

RX = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+):(?P<col>\d+)\s+-\s+\w+:\s+(?P<msg>.*)\((?P<rule>report[A-Za-z0-9_]+)\)\s*$"
)
RX_NAME = re.compile(r'"([A-Za-z_]\w*)"')

TARGET_RULES = {"reportUnusedImport", "reportUnusedVariable"}


def normalize_path(p: str) -> Path | None:
    rp = Path(p)
    if rp.is_absolute():
        try:
            rp = rp.relative_to(ROOT)
        except Exception:
            return None
    return rp


def prune_from_import_line(line: str, drop: set[str]) -> str | None:
    s = line.rstrip("\n")
    if not (s.startswith("from typing import ") or s.startswith("from typing_extensions import ")):
        return None

    prefix = (
        "from typing import "
        if s.startswith("from typing import ")
        else "from typing_extensions import "
    )
    rest = s[len(prefix) :].strip()
    if "(" in rest or ")" in rest:
        return None

    parts = [p.strip() for p in rest.split(",") if p.strip()]
    kept = [p for p in parts if p.split(" as ")[0].strip() not in drop]

    if not kept:
        return ""
    return prefix + ", ".join(kept) + "\n"


def main(report_path: Path) -> None:
    txt = report_path.read_text(encoding="utf-8", errors="replace").splitlines()

    targets: dict[Path, dict[int, set[str]]] = {}
    for ln in txt:
        m = RX.match(ln.strip())
        if not m:
            continue
        rule = m.group("rule")
        if rule not in TARGET_RULES:
            continue

        rp = normalize_path(m.group("path"))
        if rp is None:
            continue

        line_no = int(m.group("line"))
        msg = m.group("msg")

        nm = RX_NAME.search(msg)
        if not nm:
            continue
        name = nm.group(1)

        targets.setdefault(rp, {}).setdefault(line_no, set()).add(name)

    changed_files = 0
    changed_lines = 0

    for rel, by_line in targets.items():
        fp = ROOT / rel
        if not fp.exists():
            continue
        lines = fp.read_text(encoding="utf-8", errors="replace").splitlines(True)
        updated = False

        for line_no, names in sorted(by_line.items()):
            i = line_no - 1
            if i < 0 or i >= len(lines):
                continue
            new_line = prune_from_import_line(lines[i], names)
            if new_line is None:
                continue
            if new_line != lines[i]:
                lines[i] = new_line
                updated = True
                changed_lines += 1

        if updated:
            fp.write_text("".join(lines), encoding="utf-8")
            changed_files += 1

    print("CHANGED_FILES=", changed_files)
    print("CHANGED_LINES=", changed_lines)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "usage: python3 scripts/pyright_prune_unused_typing_imports_v733.py <pyright_report.txt>"
        )
        raise SystemExit(2)
    main(Path(sys.argv[1]))
