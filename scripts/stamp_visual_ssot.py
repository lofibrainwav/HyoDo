#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

MARK_PREFIX = "SSOT-SOURCE-SHA256:"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def stamp_svg(svg_path: Path, source_hash: str) -> None:
    content = svg_path.read_text(encoding="utf-8", errors="replace")

    # Standardized Metadata Block for "Beauty & Logic"
    marker = f"\n  <!-- {MARK_PREFIX}{source_hash} -->"

    # Remove existing markers
    pattern = re.compile(rf"\n?\s*<!-- {re.escape(MARK_PREFIX)}[a-f0-9]+ -->")
    content = pattern.sub("", content)

    # Inject after the opening <svg> tag for immediate visibility
    if "<svg" in content:
        # Find the end of the <svg ...> opening tag
        match = re.search(r"<svg[^>]*>", content)
        if match:
            insertion_point = match.end()
            content = content[:insertion_point] + marker + content[insertion_point:]
        else:
            content = marker + "\n" + content
    else:
        content = marker + "\n" + content

    svg_path.write_text(content, encoding="utf-8")


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/diagrams")
    if not base.exists():
        print(f"Directory not found: {base}")
        return 1

    ex_files = sorted(base.rglob("*.excalidraw"))
    if not ex_files:
        print("No .excalidraw files found to stamp.")
        return 0

    stamped_count = 0
    for ex in ex_files:
        svg = ex.with_suffix(".svg")
        if not svg.exists():
            print(f"⚠️ Warning: Missing SVG for {ex.name}, skipped stamping.")
            continue

        src_hash = sha256_file(ex)
        stamp_svg(svg, src_hash)
        print(f"✅ Stamped: {svg.as_posix()}")
        stamped_count += 1

    print(f"🎉 Done. Stamped {stamped_count} SVG files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
