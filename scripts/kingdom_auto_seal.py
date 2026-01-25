#!/usr/bin/env python3
import datetime
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: str = ".") -> str:
    # Use errors='replace' to handle potential non-UTF-8 characters in output (e.g. Korean on some systems)
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=cwd, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print(f"❌ Error executing {' '.join(cmd)}: {result.stderr}")
        return ""
    return result.stdout.strip()


def auto_seal():
    print("💎 AFO Kingdom: Kingdom Auto-Seal (Skill 071) 💎")
    project_root = Path(__file__).resolve().parent.parent

    # 1. Update Evolution Log
    log_file = project_root / "AFO_EVOLUTION_LOG.md"
    today = datetime.date.today().isoformat()

    phase_entry = f"""
### Phase 70: Operation Resonance & The Great Awakening ({today}) 🌊💎
- **Truth (眞)**: LanceDB RAG integration & Semantic Search established.
- **Goodness (善)**: Ollama(DeepSeek-R1/Qwen) Real-time Streaming & Identity Hallucination fixed.
- **Beauty (美)**: Authentic Trinity Score (90.5) resonance & UX refinement.
- **Serenity (孝)**: Skill 071 Auto-Seal introduced for maintenance automation.
- **Eternity (永)**: Strategic victories sealed into SSOT history.
- **Status**: ✅ **봉인됨 (SEALED)**
"""

    if log_file.exists():
        content = log_file.read_text()
        # Insert after "## 🚀 Latest Updates" (around line 12)
        lines = content.splitlines()
        insert_idx = -1
        for i, line in enumerate(lines):
            if "## 🚀 Latest Updates" in line:
                insert_idx = i + 1
                break

        if insert_idx != -1:
            # Add to the table too (PH-70)
            table_entry = "| PH-70    | Operation Resonance Mastery        | SEALED |"
            lines.insert(insert_idx + 3, table_entry)

            # Find a place for the detailed entry (e.g., after the latest updates header)
            lines.insert(insert_idx + 10, phase_entry)

            log_file.write_text("\n".join(lines))
            print("✅ Evolution Log updated.")
        else:
            print("⚠️ Could not find update header in Evolution Log. Manual entry may be needed.")

    # 2. Git Stage and Commit
    print("🚀 Staging and Committing all changes...")
    run_command(["git", "add", "."], str(project_root))

    commit_msg = f"feat(resonance): Operation Resonance Zenith Mastery & Skill 071 Seal ({today})"
    run_command(["git", "commit", "-m", commit_msg], str(project_root))
    print(f"✅ Changes sealed with commit: {commit_msg}")

    # 3. Final Trinity Check
    print("📊 Performing final Trinity Score Audit...")
    audit_res = run_command([sys.executable, "scripts/trinity_score_check.py"], str(project_root))
    print(audit_res)


if __name__ == "__main__":
    auto_seal()
