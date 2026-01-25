#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

MARK_PREFIX = "SSOT-SOURCE-SHA256:"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/diagrams")
    manifest_path = base / "SSOT_VISUAL_MANIFEST.txt"

    if not base.exists():
        # If directory doesn't exist, we skip since there might be no diagrams yet
        print(f"Directory {base} not found, skipping visual check.")
        return 0

    ex_files = sorted(base.rglob("*.excalidraw"))

    # Manifest Logic
    manifest_files: set[str] = set()
    if manifest_path.exists():
        manifest_files = {
            line.strip()
            for line in manifest_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }

    errors: list[str] = []

    # 1) Check if manifest files exist
    for m_file in manifest_files:
        p = base / m_file
        if not p.exists():
            errors.append(f"MANIFEST ERROR: Declared file missing: {m_file}")

    # 2) Sync check for found files
    for ex in ex_files:
        # If manifest exists, only check those in the manifest to reduce noise
        rel_path = str(ex.relative_to(base))
        if manifest_files and rel_path not in manifest_files:
            continue

        svg = ex.with_suffix(".svg")
        if not svg.exists():
            errors.append(f"missing svg: {svg.as_posix()}")
            continue

        src_hash = sha256_file(ex)
        svg_text = svg.read_text(encoding="utf-8", errors="replace")

        expected_marker = f"{MARK_PREFIX}{src_hash}"
        if expected_marker not in svg_text:
            errors.append(f"stale svg: {svg.as_posix()} (stamp mismatch or missing)")

    if errors:
        print("VISUAL SSOT SYNC: FAIL")
        for e in errors:
            print(f"- {e}")
        print("\n💡 Hint: Open the diagram in Excalidraw, Export as SVG, and then run:")
        print(f"   python3 scripts/stamp_visual_ssot.py {base}")
        return 1

    print("VISUAL SSOT SYNC: PASS")
    print(f"- checked pairs: {len(ex_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
