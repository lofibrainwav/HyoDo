#!/bin/bash
set -euo pipefail

mkdir -p artifacts

# Resolve Evidence Files
debt="$(ls -1t artifacts/mypy_debt_*.txt 2>/dev/null | head -1 || true)"
pre="$(ls -1t artifacts/syntax_surgery_precommit_*.txt 2>/dev/null | head -1 || true)"
audit="$(ls -1t artifacts/phase26_audit_*.txt 2>/dev/null | head -1 || true)"

# Resolve Walkthrough Path
wt=""
if [ -n "${WT:-}" ]; then wt="$WT"; fi
if [ -z "$wt" ] && [ -f docs/walkthrough.md ]; then wt="docs/walkthrough.md"; fi
if [ -z "$wt" ] && [ -f walkthrough.md ]; then wt="walkthrough.md"; fi

if [ -z "$wt" ]; then 
    echo "ERROR: walkthrough.md NOT FOUND"
    exit 1
fi

if [ -z "$debt" ]; then 
    echo "ERROR: mypy_debt_*.txt NOT FOUND in artifacts/"
    exit 1
fi

echo "Updating Walkthrough: $wt"
echo "Using Debt File: $debt"

python3 - <<'PY'
import os, re
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

wt = Path(os.environ["WT"])
debt = Path(os.environ["DEBT"])
pre = Path(os.environ["PRE"]) if os.environ.get("PRE") else None
audit = Path(os.environ["AUDIT"]) if os.environ.get("AUDIT") else None

txt = debt.read_text(encoding="utf-8", errors="ignore")
codes = re.findall(r"\[([A-Za-z0-9\-]+)\]\s*$", txt, flags=re.M)
c = Counter(codes)

top = c.most_common(20)
total = sum(c.values())

def fmt_size(p: Path) -> str:
    n = p.stat().st_size
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.0f}PB"

db_lines = []
for name in ["monkeytype.sqlite3", "monkeytype_fast.sqlite3"]:
    p = Path(name)
    if p.exists():
        db_lines.append(f"- {name} ({fmt_size(p)})")
if not db_lines:
    db_lines.append("- (no monkeytype sqlite found in repo root)")

as_of = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

lines = []
lines.append("<!-- AFO:MYPY_DEBT:BEGIN -->")
lines.append("")
lines.append("## Phase 26 — MyPy Debt Statistics (SSOT-LOCKED)")
lines.append(f"- AS_OF: {as_of}")
lines.append("")
lines.append("### Evidence")
lines.append(f"- MYPY_DEBT_FILE: `{debt.as_posix()}`")
if pre and pre.exists():
    lines.append(f"- SYNTAX_PRECOMMIT_EVIDENCE: `{pre.as_posix()}`")
if audit and audit.exists():
    lines.append(f"- AUDIT_LOG: `{audit.as_posix()}`")
lines.append("")
lines.append("### MonkeyType State")
lines.extend(db_lines)
lines.append("")
lines.append("### MyPy Debt (Top 20)")
lines.append("| Error Code | Count |")
lines.append("|---|---:|")
for code, n in top:
    lines.append(f"| `{code}` | {n} |")
lines.append(f"| **TOTAL ERRORS** | **{total}** |")
lines.append("")
lines.append("<!-- AFO:MYPY_DEBT:END -->")
block = "\n".join(lines) + "\n"

doc = wt.read_text(encoding="utf-8", errors="ignore")

b = "<!-- AFO:MYPY_DEBT:BEGIN -->"
e = "<!-- AFO:MYPY_DEBT:END -->"

if b in doc and e in doc:
    pre_txt = doc.split(b, 1)[0]
    post_txt = doc.split(e, 1)[1]
    new_doc = pre_txt + block + post_txt.lstrip("\n")
else:
    new_doc = doc.rstrip("\n") + "\n\n" + block

wt.write_text(new_doc, encoding="utf-8")

log = Path("artifacts") / f"walkthrough_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logContent = []
logContent.append(f"AS_OF={as_of}")
logContent.append(f"WALKTHROUGH={wt.as_posix()}")
logContent.append(f"MYPY_DEBT_FILE={debt.as_posix()}")
if pre: logContent.append(f"SYNTAX_PRECOMMIT_EVIDENCE={pre.as_posix()}")
if audit: logContent.append(f"AUDIT_LOG={audit.as_posix()}")

log.write_text("\n".join(logContent) + "\n", encoding="utf-8")

print(f"WALKTHROUGH_UPDATED={wt.as_posix()}")
print(f"UPDATE_EVIDENCE={log.as_posix()}")
PY
