from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path.cwd()

RULE = "reportUnknownVariableType"


def docstring_span(lines, i) -> None:
    if i >= len(lines):
        return None
    s = lines[i].lstrip()
    m = re.match(r'^(?:[rRuU])?("""|\'\'\')', s)
    if not m:
        return None
    q = m.group(1)
    if s.count(q) >= 2:
        return (i, i)
    j = i + 1
    while j < len(lines):
        if q in lines[j]:
            return (i, j)
        j += 1
    return (i, len(lines) - 1)


def insert_index_for_import(lines) -> None:
    idx = 0
    if idx < len(lines) and lines[idx].startswith("#!"):
        idx += 1
    if idx < len(lines) and re.match(r"^#.*coding[:=]", lines[idx]):
        idx += 1
    ds = docstring_span(lines, idx)
    if ds:
        idx = ds[1] + 1
    while idx < len(lines) and (lines[idx].strip() == "" or lines[idx].lstrip().startswith("#")):
        idx += 1
    while idx < len(lines) and lines[idx].startswith("from __future__ import "):
        idx += 1
    return idx


def ensure_typing_import(src, needed) -> None:
    lines = src.splitlines(True)
    for i, line in enumerate(lines):
        if line.startswith("from typing import "):
            existing = [
                x.strip()
                for x in line[len("from typing import ") :].strip().split(",")
                if x.strip()
            ]
            merged = sorted(set(existing) | set(needed))
            lines[i] = "from typing import " + ", ".join(merged) + "\n"
            return "".join(lines)
    ins = insert_index_for_import(lines)
    lines.insert(ins, "from typing import " + ", ".join(sorted(needed)) + "\n")
    return "".join(lines)


# pyright 기본 출력 라인 파서:
# path:line:col - error: ... (reportUnknownVariableType)
RX = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+):(?P<col>\d+)\s+-\s+\w+:\s+.*\(" + re.escape(RULE) + r"\)\s*$"
)

RX_EMPTY_LIST = re.compile(
    r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=\s*\[\]\s*(?P<comment>#.*)?$"
)
RX_EMPTY_DICT = re.compile(
    r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=\s*\{\}\s*(?P<comment>#.*)?$"
)
RX_EMPTY_SET = re.compile(
    r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=\s*set\(\)\s*(?P<comment>#.*)?$"
)


def patch_line(line: str) -> None:
    # 이미 주석 타입이 있으면 스킵 (x: list[Any] = [] 같은)
    if re.match(r"^\s*[A-Za-z_]\w*\s*:\s*", line):
        return line, False

    m = RX_EMPTY_LIST.match(line)
    if m:
        c = m.group("comment") or ""
        comment_part = (" " + c) if c else ""
        return (
            "{}{}: list[Any] = []{}\n".format(m.group("indent"), m.group("name"), comment_part),
            True,
        )

    m = RX_EMPTY_DICT.match(line)
    if m:
        c = m.group("comment") or ""
        comment_part = (" " + c) if c else ""
        return (
            "{}{}: dict[str, Any] = {{{}}}{}\n".format(
                m.group("indent"), m.group("name"), "", comment_part
            ),
            True,
        )

    m = RX_EMPTY_SET.match(line)
    if m:
        c = m.group("comment") or ""
        comment_part = (" " + c) if c else ""
        return (
            "{}{}: set[Any] = set(){}\n".format(m.group("indent"), m.group("name"), comment_part),
            True,
        )

    return line, False


def main(report_path: Path) -> None:
    txt = report_path.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = []
    for line in txt:
        m = RX.match(line.strip())
        if not m:
            continue
        p = m.group("path")
        # pyright가 절대경로를 찍는 경우가 있으니 루트 기준으로 정규화
        rp = Path(p)
        if rp.is_absolute():
            try:
                rp = rp.relative_to(ROOT)
            except Exception:
                # 루트 밖이면 스킵
                continue
        hits.append((str(rp), int(m.group("line"))))

    # 파일별 라인 수집
    by_file = {}
    for f, ln in hits:
        by_file.setdefault(f, set()).add(ln)

    changed_files = []
    changed_lines = 0
    for f, lns in by_file.items():
        fp = ROOT / f
        if not fp.exists():
            continue
        src0 = fp.read_text(encoding="utf-8", errors="replace")
        lines = src0.splitlines(True)
        changed = False

        for ln in sorted(lns):
            if 1 <= ln <= len(lines):
                new, ok = patch_line(lines[ln - 1])
                if ok:
                    lines[ln - 1] = new
                    changed = True
                    changed_lines += 1

        src1 = "".join(lines)
        if changed and src1 != src0:
            src1 = ensure_typing_import(src1, {"Any"})
            fp.write_text(src1, encoding="utf-8")
            changed_files.append(f)

    print("PATCH_RULE=", RULE)
    print("CHANGED_FILES=", len(changed_files))
    for f in changed_files[:200]:
        print(f)
    print("CHANGED_LINES=", changed_lines)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python3 scripts/pyright_patch_unknown_variable_v72.py <pyright_report.txt>")
        raise SystemExit(2)
    main(Path(sys.argv[1]))
