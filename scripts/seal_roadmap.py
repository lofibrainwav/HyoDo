import os
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    wt_path = Path(os.environ.get("WT", "walkthrough.md"))

    if not wt_path.exists():
        print(f"Error: {wt_path} not found")
        return

    as_of = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    lines = []
    lines.append("<!-- AFO:ROADMAP:BEGIN -->")
    lines.append("")
    lines.append("## Phase 26 — Strategic Roadmap (Forward Looking)")
    lines.append(f"- LOCKED_AT: {as_of}")
    lines.append("")
    lines.append("### Current State: Option 3 (Legacy Segregation) 🛡️")
    lines.append(
        "- **Strategy**: `legacy/` & `scripts/` excluded or relaxed in `pyproject.toml` or `pyrightconfig.json`."
    )
    lines.append("- **Benefit**: 'Virtual Zero Debt' for new code (Strict Mode).")
    lines.append("- **Risk**: Blind spots in legacy code.")
    lines.append("")
    lines.append("### Next State: Option 2 (Progressive Masking) 🎭")
    lines.append("- **Trigger**: When a legacy file MUST be modified.")
    lines.append(
        "- **Action**: Enable strict mode for that file, apply specific `# type: ignore` or casts."
    )
    lines.append("- **Tool**: `monkeytype-harvest` (Pre-commit) gathers data to reduce masks.")
    lines.append("")
    lines.append("### Final State: Option 1 (True Zero Debt) 💎")
    lines.append("- **Strategy**: Full strict typing, no excludes, no ignores.")
    lines.append("- **Milestone**: `mypy --strict .` passes across the entire repo.")
    lines.append("- **Timeline**: Continuous (Weekly Harvests).")
    lines.append("")
    lines.append("<!-- AFO:ROADMAP:END -->")

    block = "\n".join(lines) + "\n"

    doc = wt_path.read_text(encoding="utf-8")

    b = "<!-- AFO:ROADMAP:BEGIN -->"
    e = "<!-- AFO:ROADMAP:END -->"

    if b in doc and e in doc:
        pre = doc.split(b)[0]
        post = doc.split(e)[1]
        new_doc = pre + block + post.lstrip("\n")
    else:
        # Append after Pyright section if exists
        pyright_end = "<!-- AFO:PYRIGHT_DEBT:END -->"
        if pyright_end in doc:
            parts = doc.split(pyright_end)
            new_doc = parts[0] + pyright_end + "\n\n" + block + parts[1]
        else:
            new_doc = doc.rstrip() + "\n\n" + block

    wt_path.write_text(new_doc, encoding="utf-8")
    print(f"✅ Sealed Strategic Roadmap into {wt_path}")


if __name__ == "__main__":
    main()
