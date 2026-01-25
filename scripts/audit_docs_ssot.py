from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Adjust CWD to root if running from scripts/
if Path.cwd().name == "scripts":
    ROOT = Path("..")
else:
    ROOT = Path(".")

DOCS = ROOT / "docs"
REQUIRED_CORE = [
    "SSOT_IMPORT_PATHS.md",
    "FAILURE_MODE_MATRIX.md",
    "GRAPH_STATE_CONTRACT.md",
    "QUICK_START_VERIFIED.md",
    "OPERATIONAL_METRICS.md",
    "CONTEXT7_SEQUENTIAL_THINKING_SKILLS_MASTER_INDEX.md",
]

# Patterns for legacy/internal paths that should not be in Core SSOT
BANNED_PATTERNS = [
    re.compile(r"\btrinity_os\b(?!/)", re.IGNORECASE),
]

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def is_external_link(target: str) -> bool:
    t = target.strip()
    return t.startswith(("http://", "https://", "mailto:", "#"))


def normalize_link_target(raw: str) -> str:
    # Handle file:// absolute links and masked placeholders as OK for local
    if raw.startswith("file://") or "<LOCAL_WORKSPACE>" in raw:
        return ""
    t = raw.split("#", 1)[0].strip()
    return t


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit SSOT Documentation Integrity")
    parser.add_argument(
        "--core-only", action="store_true", help="Only check the core SSOT documents"
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=["docs/reports", "docs/_templates"],
        help="Directories to exclude from full audit",
    )
    args = parser.parse_args()

    errors: list[str] = []

    if not DOCS.exists() or not DOCS.is_dir():
        errors.append("docs/ directory not found")
        print("\n".join(errors))
        return 1

    # 1) Check CORE documents exist
    for name in REQUIRED_CORE:
        p = DOCS / name
        if not p.exists():
            errors.append(f"MISSING CORE DOC: {p.relative_to(ROOT) if p.is_absolute() else p}")

    # 2) scan files
    if args.core_only:
        files_to_scan = [DOCS / name for name in REQUIRED_CORE if (DOCS / name).exists()]
    else:
        # Full scan excluding specified dirs
        exclude_paths = [ROOT / p for p in args.exclude]
        files_to_scan = []
        for f in DOCS.rglob("*.md"):
            if any(str(f).startswith(str(ep)) for ep in exclude_paths):
                continue
            files_to_scan.append(f)

    for f in files_to_scan:
        text = read_text(f)

        # 1) Strip code blocks and backticks to ignore examples
        # Fenced blocks
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        # Inline backticks
        text = re.sub(r"`.*?`", "", text)

        # banned imports (core only check for strictness)
        if f.name in REQUIRED_CORE:
            for pat in BANNED_PATTERNS:
                if pat.search(text):
                    errors.append(
                        f"BANNED PATTERN '{pat.pattern}' in core doc: {f.relative_to(ROOT)}"
                    )

        # relative link integrity
        for m in MD_LINK.finditer(text):
            raw = m.group(1)
            if is_external_link(raw):
                continue
            target = normalize_link_target(raw)
            if not target:
                continue

            try:
                if target.startswith("/"):
                    candidate = ROOT / target.lstrip("/")
                else:
                    candidate = (f.parent / target).resolve()

                if not candidate.exists():
                    errors.append(f"BROKEN LINK in {f.relative_to(ROOT)}: ({raw}) -> {target}")
            except Exception as e:
                errors.append(f"ERROR resolving link {f.relative_to(ROOT)} ({raw}): {e}")

    if errors:
        print("SSOT DOC AUDIT: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1

    print("SSOT DOC AUDIT: PASS")
    print(f"- scanned files: {len(files_to_scan)}")
    print("- core docs present and verified")
    print("- links look OK (excluding local-only file:// links)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
