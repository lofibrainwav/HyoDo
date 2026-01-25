from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path.cwd()
RULE = "reportUnknownVariableType"

RX = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+):(?P<col>\d+)\s+-\s+\w+:\s+(?P<msg>.*)\("
    + re.escape(RULE)
    + r"\)\s*$"
)

RX_ASSIGN_SIMPLE = re.compile(
    r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<expr>.+?)(?P<comment>\s+#.*)?$"
)

RX_ASSIGN_MULTI = re.compile(
    r"^(?P<indent>\s*)(?P<lhs>(?:[A-Za-z_]\w*\s*,\s*)+[A-Za-z_]\w*)\s*=\s*(?P<expr>.+?)(?P<comment>\s+#.*)?$"
)

RX_DEF = re.compile(
    r"^(?P<indent>\s*)(?P<async>async\s+)?def\s+(?P<name>[A-Za-z_]\w*)\s*\((?P<params>.*)\)\s*:\s*(?P<comment>#.*)?$"
)

RX_WITH_AS = re.compile(
    r"^(?P<indent>\s*)with\s+.+?\s+as\s+(?P<name>[A-Za-z_]\w*)\s*:\s*(?P<comment>#.*)?$"
)

RX_FOR_IN = re.compile(
    r"^(?P<indent>\s*)for\s+(?P<name>[A-Za-z_]\w*)\s+in\s+.+:\s*(?P<comment>#.*)?$"
)


def normalize_path(p: str) -> None:
    rp = Path(p)
    if rp.is_absolute():
        try:
            rp = rp.relative_to(ROOT)
        except Exception:
            return None
    return rp


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


def ensure_typing_import(src: str, needed) -> None:
    needed = set(needed)
    if not needed:
        return src
    lines = src.splitlines(True)
    for i, line in enumerate(lines):
        if line.startswith("from typing import "):
            existing = [
                x.strip()
                for x in line[len("from typing import ") :].strip().split(",")
                if x.strip()
            ]
            merged = sorted(set(existing) | needed)
            lines[i] = "from typing import " + ", ".join(merged) + "\n"
            return "".join(lines)
    ins = insert_index_for_import(lines)
    lines.insert(ins, "from typing import " + ", ".join(sorted(needed)) + "\n")
    return "".join(lines)


def already_has_any_annotation(line: str) -> bool:
    return bool(re.match(r"^\s*[A-Za-z_]\w*\s*:\s*", line))


def patch_def(line: str) -> None:
    if "->" in line:
        return line, False
    m = RX_DEF.match(line.rstrip("\n"))
    if not m:
        return line, False
    indent = m.group("indent")
    async_kw = m.group("async") or ""
    name = m.group("name")
    params = m.group("params")
    comment = (m.group("comment") or "").strip()
    new = f"{indent}{async_kw}def {name}({params}) -> Any:"
    if comment:
        new += " " + comment
    new += "\n"
    return new, True


def patch_assign_simple(line: str) -> None:
    if already_has_any_annotation(line):
        return line, False
    m = RX_ASSIGN_SIMPLE.match(line.rstrip("\n"))
    if not m:
        return line, False
    indent = m.group("indent")
    name = m.group("name")
    expr = m.group("expr")
    comment = m.group("comment") or ""
    new = f"{indent}{name}: Any = {expr}{comment}\n"
    return new, True


def patch_assign_multi(lines, idx) -> None:
    line = lines[idx].rstrip("\n")
    m = RX_ASSIGN_MULTI.match(line)
    if not m:
        return False
    indent = m.group("indent")
    lhs = m.group("lhs")
    names = [x.strip() for x in lhs.split(",") if x.strip()]
    if not names:
        return False
    ann_line = indent + "; ".join([f"{n}: Any" for n in names]) + "\n"
    if idx > 0 and lines[idx - 1].strip() == ann_line.strip():
        return False
    lines.insert(idx, ann_line)
    return True


def insert_cast_next_line(lines, idx, name: str, base_indent: str) -> None:
    indent = base_indent + "    "
    cast_line = f"{indent}{name} = cast(Any, {name})\n"
    if idx + 1 < len(lines) and lines[idx + 1] == cast_line:
        return False
    lines.insert(idx + 1, cast_line)
    return True


def main(report_path: Path) -> None:
    txt = report_path.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = []
    for line in txt:
        m = RX.match(line.strip())
        if not m:
            continue
        rp = normalize_path(m.group("path"))
        if rp is None:
            continue
        hits.append((str(rp), int(m.group("line")), m.group("msg").strip()))

    by_file = {}
    for f, ln, msg in hits:
        by_file.setdefault(f, []).append((ln, msg))

    changed_files = 0
    changed_lines = 0
    unpatched = []

    for f, items in by_file.items():
        fp = ROOT / f
        if not fp.exists():
            continue
        src0 = fp.read_text(encoding="utf-8", errors="replace")
        lines = src0.splitlines(True)

        need = set()
        changed = False

        targets = sorted(set([ln for ln, _ in items]))
        offset = 0
        for ln in targets:
            i = ln - 1 + offset
            if i < 0 or i >= len(lines):
                continue

            orig = lines[i]

            new, ok = patch_def(orig)
            if ok and new != orig:
                lines[i] = new
                need.add("Any")
                changed = True
                changed_lines += 1
                continue

            m_with = RX_WITH_AS.match(orig.rstrip("\n"))
            if m_with:
                name = m_with.group("name")
                base_indent = m_with.group("indent")
                ok2 = insert_cast_next_line(lines, i, name, base_indent)
                if ok2:
                    need.add("Any")
                    need.add("cast")
                    changed = True
                    changed_lines += 1
                    offset += 1
                else:
                    unpatched.append(f"{f}:{ln}")
                continue

            m_for = RX_FOR_IN.match(orig.rstrip("\n"))
            if m_for:
                name = m_for.group("name")
                base_indent = m_for.group("indent")
                ok3 = insert_cast_next_line(lines, i, name, base_indent)
                if ok3:
                    need.add("Any")
                    need.add("cast")
                    changed = True
                    changed_lines += 1
                    offset += 1
                else:
                    unpatched.append(f"{f}:{ln}")
                continue

            m_multi = RX_ASSIGN_MULTI.match(orig.rstrip("\n"))
            if m_multi:
                okm = patch_assign_multi(lines, i)
                if okm:
                    need.add("Any")
                    changed = True
                    changed_lines += 1
                    offset += 1
                else:
                    unpatched.append(f"{f}:{ln}")
                continue

            new2, ok4 = patch_assign_simple(orig)
            if ok4 and new2 != orig:
                lines[i] = new2
                need.add("Any")
                changed = True
                changed_lines += 1
                continue

            # 3) 핵심: 위로 스캔해서 "x = ..." 라인 찾으면 거길 x: Any = 로 교체
            patched = False
            for back in range(1, 9):  # 8줄 위까지
                j = i - back
                if j < 0:
                    break
                cand = lines[j]
                # 들여쓰기 레벨 크게 깨지는 라인은 스킵 (보수적)
                if cand.strip() == "":
                    continue
                if cand.lstrip().startswith(
                    (
                        "return ",
                        "yield ",
                        "if ",
                        "elif ",
                        "else:",
                        "for ",
                        "while ",
                        "with ",
                        "try:",
                        "except",
                        "finally:",
                    )
                ):
                    continue
                new3, ok5 = patch_assign_simple(cand)
                if ok5 and new3 != cand:
                    lines[j] = new3
                    need.add("Any")
                    changed = True
                    changed_lines += 1
                    patched = True
                    break
            if not patched:
                unpatched.append(f"{f}:{ln}")

        src1 = "".join(lines)
        if changed and src1 != src0:
            src1 = ensure_typing_import(src1, need)
            fp.write_text(src1, encoding="utf-8")
            changed_files += 1

    out = ROOT / "artifacts" / "unpatched_unknownvar_v732.txt"
    out.write_text(
        "\n".join(sorted(set(unpatched))) + ("\n" if unpatched else ""),
        encoding="utf-8",
    )

    print("PATCH_RULE=", RULE)
    print("CHANGED_FILES=", changed_files)
    print("CHANGED_LINES=", changed_lines)
    print("UNPATCHED_REPORT=", str(out))
    print("UNPATCHED_COUNT=", len(set(unpatched)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "usage: python3 scripts/pyright_patch_unknown_variable_v732_upscan.py <pyright_report.txt>"
        )
        raise SystemExit(2)
    main(Path(sys.argv[1]))
