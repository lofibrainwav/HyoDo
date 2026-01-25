from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

BUILTIN_TYPES = {
    "str",
    "int",
    "float",
    "bool",
    "dict",
    "list",
    "tuple",
    "set",
    "object",
    "None",
    "Any",
}


def extract_expected_type(msg: str) -> str | None:
    m = re.search(r'of type\s+"([^"]+)"\s*$', msg)
    return m.group(1).strip() if m else None


def is_safe_type_expr(t: str) -> bool:
    tokens = re.findall(r"[A-Za-z_]\w*", t)
    for tok in tokens:
        if tok not in BUILTIN_TYPES:
            return False
    if re.search(r"[^A-Za-z0-9_\s\[\]\|\.,]", t):
        return False
    return True


def choose_cast_type(expected: str | None) -> str:
    if not expected:
        return "Any"
    expected = expected.replace("Unknown", "Any")
    if expected in {"str", "int", "float", "bool"}:
        return expected
    if expected.startswith("dict["):
        return "dict[str, Any]"
    if is_safe_type_expr(expected):
        return expected
    return "Any"


def ensure_typing_imports(text: str, need_any: bool, need_cast: bool) -> str:
    if not (need_any or need_cast):
        return text
    lines = text.splitlines(True)

    i = 0
    if lines and lines[0].startswith("#!"):
        i = 1
    if i < len(lines) and "coding" in lines[i]:
        i += 1
    if i < len(lines) and lines[i].lstrip().startswith(('"""', "'''")):
        q = lines[i].lstrip()[:3]
        i += 1
        while i < len(lines) and q not in lines[i]:
            i += 1
        if i < len(lines):
            i += 1
    while i < len(lines) and lines[i].startswith("from __future__ import"):
        i += 1

    for idx, line in enumerate(lines):
        if line.startswith("from typing import "):
            imported = [x.strip() for x in line[len("from typing import ") :].split(",")]
            s = set(imported)
            if need_any:
                s.add("Any")
            if need_cast:
                s.add("cast")
            lines[idx] = "from typing import " + ", ".join(sorted(s)) + "\n"
            return "".join(lines)

    items = []
    if need_any:
        items.append("Any")
    if need_cast:
        items.append("cast")
    lines.insert(i, f"from typing import {', '.join(items)}\n")
    return "".join(lines)


@dataclass
class Patch:
    sl: int
    sc: int
    el: int
    ec: int
    cast_type: str
    msg: str


def apply_file(path: Path, patches: list[Patch]) -> tuple[int, int, int]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(True)

    patches = sorted(patches, key=lambda p: (p.sl, p.sc), reverse=True)

    changed = 0
    skipped_multi = 0
    skipped_cast = 0
    need_any = False
    need_cast = False

    for p in patches:
        if p.sl != p.el:
            skipped_multi += 1
            continue
        if p.sl < 0 or p.sl >= len(lines):
            continue
        line = lines[p.sl]
        if p.sc < 0 or p.ec > len(line) or p.sc >= p.ec:
            continue
        seg = line[p.sc : p.ec]
        if "cast(" in seg:
            skipped_cast += 1
            continue

        ct = p.cast_type
        if ct == "Any" or "Any" in ct:
            need_any = True
        need_cast = True

        lines[p.sl] = line[: p.sc] + f"cast({ct}, {seg})" + line[p.ec :]
        changed += 1

    out = "".join(lines)
    out = ensure_typing_imports(out, need_any=need_any, need_cast=need_cast)

    if out != text:
        path.write_text(out, encoding="utf-8")

    return changed, skipped_multi, skipped_cast


def main() -> int:
    import sys

    rp = Path(sys.argv[1])
    data = json.loads(rp.read_text(encoding="utf-8"))

    diags = [
        d
        for d in data.get("generalDiagnostics", [])
        if d.get("severity") == "error" and d.get("rule") == "reportArgumentType"
    ]

    # trinity-os 안에서만, 그리고 "핫스팟 우선" 정렬을 위해 파일별로 모음
    by_file: dict[str, list[Patch]] = {}
    for d in diags:
        f = str(d.get("file", "")).replace("\\", "/")
        if "packages/trinity-os/" not in f:
            continue
        r = d.get("range") or {}
        s = r.get("start") or {}
        e = r.get("end") or {}
        msg = d.get("message", "")

        expected = extract_expected_type(msg)
        cast_type = choose_cast_type(expected)

        by_file.setdefault(f, []).append(
            Patch(
                sl=int(s.get("line", 0)),
                sc=int(s.get("character", 0)),
                el=int(e.get("line", 0)),
                ec=int(e.get("character", 0)),
                cast_type=cast_type,
                msg=msg,
            )
        )

    total_changed = total_multi = total_cast = 0
    print(f"argtype_diags={len(diags)} files={len(by_file)}")

    # 핫스팟 1위 파일 먼저: trinity_toolflow_graph_v1.py 우선
    files = sorted(
        by_file.items(),
        key=lambda kv: (
            0 if kv[0].endswith("trinity_toolflow_graph_v1.py") else 1,
            -len(kv[1]),
        ),
    )

    for f, patches in files:
        p = Path(f)
        if not p.exists():
            continue
        ch, mul, alc = apply_file(p, patches)
        total_changed += ch
        total_multi += mul
        total_cast += alc
        print(f"{ch:>3} changed | {mul:>3} multiline_skip | {alc:>3} already_cast | {f}")

    print(
        f"total_changed={total_changed} multiline_skipped={total_multi} already_cast_skipped={total_cast}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
