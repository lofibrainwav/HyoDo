#!/usr/bin/env python3
import pathlib
import re
import sys


def die(msg: str, code: int = 1) -> None:
    print(msg)
    sys.exit(code)


def main() -> None:
    if len(sys.argv) != 2:
        die("usage: python3 scripts/verify_ssot_ph_capsules.py docs/AFO_EVOLUTION_LOG.md")

    p = pathlib.Path(sys.argv[1])
    if not p.exists():
        die(f"missing file: {p}")

    t = p.read_text(encoding="utf-8").splitlines()

    hdr_re = re.compile(r"^## \[SSOT/PH-[A-Z0-9-]+/\d{4}-\d{2}-\d{2}/([0-9a-f]{7,40})?\] .+$")
    status_re = re.compile(r"^- Status: (SEALED|PARTIAL|PENDING)$")
    scope_re = re.compile(r"^- Scope: .+$")
    evidence_re = re.compile(r"^- Evidence: .+$")
    gaps_re = re.compile(r"^- Gaps: .+$")

    hdr_idx = [i for i, line in enumerate(t) if line.startswith("## [SSOT/PH-")]
    if not hdr_idx:
        die("❌ SSOT/PH capsules not found (0). This must FAIL to prevent silent regression.")

    bad = []

    for i in hdr_idx:
        header = t[i]

        # Header strict
        if not hdr_re.match(header):
            bad.append((i + 1, "header", header))

        block = t[i : i + 5]
        if len(block) < 5:
            bad.append((i + 1, "short", header))
            continue

        # Exact 5-line internal structure
        if not status_re.match(block[1]):
            bad.append((i + 2, "status", block[1]))
        if not scope_re.match(block[2]):
            bad.append((i + 3, "scope", block[2]))
        if not evidence_re.match(block[3]):
            bad.append((i + 4, "evidence", block[3]))
        if not gaps_re.match(block[4]):
            bad.append((i + 5, "gaps", block[4]))

        # No extra bullet lines immediately following capsule
        if i + 5 < len(t) and t[i + 5].startswith("- "):
            bad.append((i + 6, "extra_line_in_capsule", t[i + 5]))

        # SEALED must have sha + gaps none
        m = re.match(r"^## \[SSOT/PH-[A-Z0-9-]+/\d{4}-\d{2}-\d{2}/([0-9a-f]{7,40})?\] ", header)
        sha = m.group(1) if m else None
        status = block[1].split(": ", 1)[1] if ": " in block[1] else ""
        gaps_val = block[4].split(": ", 1)[1] if ": " in block[4] else ""

        if status == "SEALED":
            if not sha:
                bad.append((i + 1, "sealed_requires_sha", header))
            if gaps_val != "None":
                bad.append((i + 5, "sealed_requires_gaps_none", block[4]))

    if bad:
        print("❌ SSOT/PH-* capsule format violations:")
        for ln, why, content in bad[:10]:
            print(f"  Line {ln}: {why} | {content}")
        sys.exit(1)

    print(f"✅ {len(hdr_idx)} SSOT capsules validated (strict 5-line format)")


if __name__ == "__main__":
    main()
