from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path.cwd()
RULE = "reportUnknownVariableType"

# pyright output line:
# path:line:col - error: ... (reportUnknownVariableType)
RX = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+):(?P<col>\d+)\s+-\s+\w+:\s+(?P<msg>.*)\("
    + re.escape(RULE)
    + r"\)\s*$"
)

BOUNDARY_TOKENS = (
    "json.loads(",
    "json.load(",
    ".json(",
    "subprocess.run(",
    "subprocess.check_output(",
    "subprocess.Popen(",
    "async_playwright(",
    "playwright.",
)

RX_ASSIGN = re.compile(
    r"^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<expr>.+?)(?P<comment>\s+#.*)?$"
)

# one-line def/async def without return annotation
RX_DEF = re.compile(
    r"^(?P<indent>\s*)(?P<async>async\s+)?def\s+"
    r"(?P<name>[A-Za-z_]\w*)\s*\((?P<params>.*)\)\s*:\s*(?P<comment>#.*)?$"
)


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


def ensure_typing_import(src: str, needed: set[str]) -> str:
    if not needed:
        return src
    lines = src.splitlines(True)

    # merge existing typing import line if present
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


def is_boundary_expr(expr: str) -> bool:
    e = expr.strip()
    if e.startswith("cast("):
        return False
    for t in BOUNDARY_TOKENS:
        if t in e:
            return True
    return False


def patch_def_line(line: str) -> None:
    # only patch one-line defs without -> annotation
    if "->" in line:
        return line, False
    m = RX_DEF.match(line.rstrip("\n"))
    if not m:
        return line, False
    # avoid multi-line signature crammed with "):" in params in weird ways
    params = m.group("params")
    if params.count("(") != params.count(")"):
        return line, False

    indent = m.group("indent")
    async_kw = m.group("async") or ""
    name = m.group("name")
    comment = m.group("comment") or ""
    # keep original params as-is
    new_line = (
        f"{indent}{async_kw}def {name}({params}) -> Any:{(' ' + comment) if comment else ''}\n"
    )
    return new_line, True


def patch_assign_line(line: str) -> None:
    # annotate "x = <boundary>" => "x: Any = <boundary>"
    # only for simple name assignment
    if re.match(r"^\s*[A-Za-z_]\w*\s*:\s*", line):
        return line, False
    m = RX_ASSIGN.match(line.rstrip("\n"))
    if not m:
        return line, False
    name = m.group("name")
    expr = m.group("expr")
    comment = m.group("comment") or ""
    if not is_boundary_expr(expr):
        return line, False
    indent = m.group("indent")
    new_line = f"{indent}{name}: Any = {expr}{comment}\n"
    return new_line, True


def normalize_path(p: str) -> Path | None:
    rp = Path(p)
    if rp.is_absolute():
        try:
            rp = rp.relative_to(ROOT)
        except Exception:
            return None
    return rp


def main(report_path: Path) -> None:
    txt = report_path.read_text(encoding="utf-8", errors="replace").splitlines()
    hits: list[tuple[str, int, str]] = []
    for line in txt:
        m = RX.match(line.strip())
        if not m:
            continue
        rp = normalize_path(m.group("path"))
        if rp is None:
            continue
        hits.append((str(rp), int(m.group("line")), m.group("msg").strip()))

    by_file: dict[str, set[int]] = {}
    for f, ln, _ in hits:
        by_file.setdefault(f, set()).add(ln)

    changed_files: list[str] = []
    changed_lines = 0
    unpatched: list[str] = []

    for f, lns in by_file.items():
        fp = ROOT / f
        if not fp.exists():
            continue
        src0 = fp.read_text(encoding="utf-8", errors="replace")
        lines = src0.splitlines(True)
        changed = False
        needed_imports: set[str] = set()

        for ln in sorted(lns):
            if not (1 <= ln <= len(lines)):
                continue
            orig = lines[ln - 1]
            new = orig
            ok = False

            # try def patch first (pyright often points at the def line for unknown return)
            new, ok = patch_def_line(orig)
            if ok:
                needed_imports.add("Any")
            else:
                # try assignment boundary patch
                new, ok = patch_assign_line(orig)
                if ok:
                    needed_imports.add("Any")

            if ok and new != orig:
                lines[ln - 1] = new
                changed = True
                changed_lines += 1
            elif not ok:
                # keep track for manual sniping
                unpatched.append(f"{f}:{ln}")

        src1 = "".join(lines)
        if changed and src1 != src0:
            src1 = ensure_typing_import(src1, needed_imports)
            fp.write_text(src1, encoding="utf-8")
            changed_files.append(f)

    print("PATCH_RULE=", RULE)
    print("CHANGED_FILES=", len(changed_files))
    for f in changed_files[:200]:
        print(f)
    print("CHANGED_LINES=", changed_lines)

    # write unpatched report for precision follow-up
    out = ROOT / "artifacts" / "unpatched_unknownvar_v73.txt"
    out.write_text(
        "\n".join(sorted(set(unpatched))) + ("\n" if unpatched else ""),
        encoding="utf-8",
    )
    print("UNPATCHED_REPORT=", str(out))
    print("UNPATCHED_COUNT=", len(set(unpatched)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "usage: python3 scripts/pyright_patch_unknown_variable_v73_boundary.py <pyright_report.txt>"
        )
        raise SystemExit(2)
    main(Path(sys.argv[1]))
