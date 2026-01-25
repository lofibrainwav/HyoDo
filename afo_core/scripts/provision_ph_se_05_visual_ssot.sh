#!/bin/bash
set -euo pipefail

# PH-SE-05: Visual SSOT (Obsidian Vault) — code provisioning
# This script creates an Obsidian Vault structure and symlinks key SSOT documents
# for graph visualization, ensuring relative paths and no absolute path leakage.

# Ensure we are at the root or find it
if [ -d "packages/afo-core" ]; then
    ROOT="$(pwd)"
elif [ -d "../packages/afo-core" ]; then
    cd ..
    ROOT="$(pwd)"
else
    # Fallback to git root
    ROOT="$(git rev-parse --show-toplevel)"
fi

VAULT_REL="config/obsidian/vault"
VAULT="$ROOT/$VAULT_REL"

export ROOT
export VAULT

echo "💎 Provisioning Obsidian Vault at: $VAULT"

mkdir -p "$VAULT/_moc" "$VAULT/src"

# Obsidian이 생성하는 로컬 설정/캐시는 커밋 금지(프라이버시/드리프트 방지)
cat > "$VAULT/.gitignore" <<'EOF'
.obsidian/
.trash/
.DS_Store
EOF

# Python script to handle relative symlinking intelligently
python3 - <<PY
import os
from pathlib import Path
import sys

root = Path(os.environ["ROOT"])
vault = Path(os.environ["VAULT"])
src = vault / "src"
moc = vault / "_moc"

# List of Target SSOTs to link
# Format: (Label for Home, [Candidate Paths relative to ROOT])
targets = [
  ("AFO Final SSOT", [
    "AFO_FINAL_SSOT.md",
    "docs/AFO_FINAL_SSOT.md",
    "docs/reports/AFO_FINAL_SSOT.md",
  ]),
  ("Trinity Constitution", [
    "packages/trinity-os/TRINITY_CONSTITUTION.md",
    "packages/trinity-os/TRINITY_CONSTITUTION_SUPREME.md",
  ]),
  ("Royal Library", [
    "docs/AFO_ROYAL_LIBRARY.md",
    "docs/field_manual/AFO_FIELD_MANUAL.md",
  ]),
  ("Kingdom Main", [
    "docs/AFO_KINGDOM_MAIN.md",
  ]),
  ("Victory Seal Routine", [
    "VICTORY_SEAL_ROUTINE.md",
    "docs/operations/VICTORY_SEAL_ROUTINE.md",
    "docs/VICTORY_SEAL_ROUTINE.md",
    "docs/reports/VICTORY_SEAL_ROUTINE.md",
  ]),
  ("Async Hardening SSOT", [
    "ASYNC_HARDENING_ANYIO_TRIO.md",
    "docs/ide/ASYNC_HARDENING_ANYIO_TRIO.md",
    "docs/ASYNC_HARDENING_ANYIO_TRIO.md",
    "docs/reports/ASYNC_HARDENING_ANYIO_TRIO.md",
  ]),
  ("Task List", [
    ".gemini/antigravity/brain/aaecc752-28e9-4bd3-aeea-f43d5b4051ef/task.md"
  ]),
  ("Implementation Plan", [
    ".gemini/antigravity/brain/aaecc752-28e9-4bd3-aeea-f43d5b4051ef/implementation_plan.md"
  ]),
  ("Walkthrough", [
    ".gemini/antigravity/brain/aaecc752-28e9-4bd3-aeea-f43d5b4051ef/walkthrough.md"
  ])
]

found = []
for label, candidates in targets:
  picked = None
  for rel in candidates:
    p = root / rel
    if p.exists() and p.is_file():
      picked = rel
      print(f"✅ Found source for '{label}': {rel}")
      break
  if not picked:
    print(f"⚠️  Source not found for '{label}' (checked {candidates})")
    continue

  # Create Symlink
  link = src / Path(picked).name
  link.parent.mkdir(parents=True, exist_ok=True)

  if link.exists() or link.is_symlink():
    link.unlink()

  target_abs = root / picked
  # Relative path from link directory to target file
  target_rel = os.path.relpath(target_abs, link.parent)
  link.symlink_to(target_rel)
  
  # Store for Home generation
  # The path in Obsidian Home should be relative to Vault root
  found.append((label, f"src/{link.name}"))

# Generate 00_HOME.md
home_lines = [
  "# 00_HOME — Visual SSOT (Obsidian Graph)",
  "",
  "> 이 Vault는 AFO 문서들을 **상대경로 링크**로 묶어 Graph로 시각화합니다.",
  "",
  "## Core SSOT (핵심 노드)",
]
for label, path in found:
  home_lines.append(f"- [{label}]({path})")

home_lines += [
  "",
  "## Maps of Content (신경망 허브)",
  "- [SSOT Map](_moc/SSOT_MAP.md)",
  "- [Observability Map](_moc/OBS_MAP.md)",
  "- [Ops/Safety Map](_moc/OPS_MAP.md)",
  "",
  "## Graph 사용 팁",
  "- 노트(원) = 파일, 선 = 내부 링크입니다.",
  "- 허브(MOC)에서 시작하면 그래프가 빠르게 ‘신경망’ 형태로 자랍니다.",
]

(vault / "00_HOME.md").write_text("\n".join(home_lines) + "\n", encoding="utf-8")
print("✅ Generated 00_HOME.md")

# Generate MOCs
(moc / "SSOT_MAP.md").write_text(
  "# SSOT Map\n\n"
  "- [[00_HOME — Visual SSOT|00_HOME]]\n"
  "- 핵심 SSOT 문서들을 여기에 계속 링크로 추가하십시오.\n",
  encoding="utf-8",
)
(moc / "OBS_MAP.md").write_text(
  "# Observability Map\n\n"
  "- PH-OBS-01 ~ 04 관련 문서/결과/체크리스트를 여기서 한 번에 연결하십시오.\n",
  encoding="utf-8",
)
(moc / "OPS_MAP.md").write_text(
  "# Ops/Safety Map\n\n"
  "- CI/CD LOCK, Victory Routine, Debug Agent Safety, Alerting Export 등 운영 규율을 여기서 연결하십시오.\n",
  encoding="utf-8",
)
print("✅ Generated MOCs")

PY

echo "[done] PH-SE-05 vault provisioned!"
export VAULT
