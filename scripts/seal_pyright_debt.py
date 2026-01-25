import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    # 1. Setup Paths
    wt_path = Path(os.environ.get("WT", "walkthrough.md"))
    json_path = Path(os.environ.get("PYRIGHT_JSON", "artifacts/pyright_ssot_final.json"))

    if not wt_path.exists():
        print(f"Error: {wt_path} not found")
        return
    if not json_path.exists():
        print(f"Error: {json_path} not found")
        return

    # 2. Parse Pyright JSON
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        diagnostics = data.get("generalDiagnostics", [])
        summary = data.get("summary", {})
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return

    total_errors = summary.get("errorCount", 0)
    total_warnings = summary.get("warningCount", 0)
    total_files = summary.get("filesAnalyzed", 0)

    # Rule Analysis
    rules = [d.get("rule", "unknown") for d in diagnostics]
    rule_counts = Counter(rules).most_common(20)

    # 3. Build Markdown Block
    as_of = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    lines = []
    lines.append("<!-- AFO:PYRIGHT_DEBT:BEGIN -->")
    lines.append("")
    lines.append("## Phase 26 — Pyright Diagnostics (SSOT-LOCKED)")
    lines.append(f"- AS_OF: {as_of}")
    lines.append(f"- VERSION: {data.get('version', 'unknown')}")
    lines.append("")
    lines.append("### Summary")
    lines.append(f"- **Files Analyzed**: {total_files}")
    lines.append(f"- **Total Errors**: {total_errors}")
    lines.append(f"- **Total Warnings**: {total_warnings}")
    lines.append("")
    lines.append("### Top 20 Rules")
    lines.append("| Rule | Count |")
    lines.append("|---|---:|")
    for rule, count in rule_counts:
        lines.append(f"| `{rule}` | {count} |")

    lines.append("")
    lines.append("<!-- AFO:PYRIGHT_DEBT:END -->")
    block = "\n".join(lines) + "\n"

    # 4. Inject into Walkthrough
    doc = wt_path.read_text(encoding="utf-8")

    start_marker = "<!-- AFO:PYRIGHT_DEBT:BEGIN -->"
    end_marker = "<!-- AFO:PYRIGHT_DEBT:END -->"

    if start_marker in doc and end_marker in doc:
        # Replace existing
        pre = doc.split(start_marker)[0]
        post = doc.split(end_marker)[1]
        new_doc = pre + block + post.lstrip("\n")
    else:
        # Append (after MyPy Debt if possible, else end)
        mypy_end = "<!-- AFO:MYPY_DEBT:END -->"
        if mypy_end in doc:
            parts = doc.split(mypy_end)
            new_doc = parts[0] + mypy_end + "\n\n" + block + parts[1]
        else:
            new_doc = doc.rstrip() + "\n\n" + block

    wt_path.write_text(new_doc, encoding="utf-8")
    print(f"✅ Sealed Pyright Debt into {wt_path}")
    print(f"Stats: {total_errors} errors, {total_warnings} warnings")


if __name__ == "__main__":
    main()
