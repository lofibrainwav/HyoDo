#!/bin/bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
VAULT="$ROOT/config/obsidian/vault"
SRC="$VAULT/src"
PH="$VAULT/ph"
PH_MOC="$VAULT/_moc/ph"
# PH_MAP="$PH_MOC/PH_MAP.md" (unused in bash)

mkdir -p "$SRC" "$PH" "$PH_MOC"

# 상대경로 symlink 생성 (실패하면 copy로 폴백)
link_or_copy () {
  local target="$1"
  local link="$2"
  local rel
  
  # Ensure target exists
  if [ ! -f "$target" ]; then
    echo "⚠️ Target not found, skipping: $target"
    return
  fi

  rel="$(python3 - <<PY
import os
from pathlib import Path
try:
    t = Path("$target").resolve()
    l = Path("$link").resolve()
    # l.parent might not exist yet if we didn't mkdir, but we did.
    # We want path from link's dir to target.
    print(os.path.relpath(t, l.parent))
except Exception as e:
    print("ERROR")
PY
)"

  if [ "$rel" == "ERROR" ]; then
    echo "❌ Python path error for $link"
    return
  fi

  rm -f "$link" || true
  if ln -s "$rel" "$link" 2>/dev/null; then
    echo "[ok] symlink: $link -> $rel"
  else
    cp -f "$target" "$link"
    echo "[ok] copy: $link"
  fi
}

# 티켓을 Vault/src로 노출(상대경로)
link_or_copy "$ROOT/docs/tickets/PH-CI-11_Structured_Concurrency_Anyio_Trio.md" "$SRC/PH-CI-11_Structured_Concurrency_Anyio_Trio.md"
link_or_copy "$ROOT/docs/tickets/PH-ST-06_Obsidian_Scripting_Orchestration.md" "$SRC/PH-ST-06_Obsidian_Scripting_Orchestration.md"
link_or_copy "$ROOT/docs/tickets/PH-FIN-01_Julie_CPA_Autopilot.md" "$SRC/PH-FIN-01_Julie_CPA_Autopilot.md"

# PH 노드(그래프용)
cat > "$PH/PH-CI-11.md" <<'MD'
# PH-CI-11 — Structured Concurrency (Anyio/Trio)
- [[PH Map (Project Hub)|PH_MAP]]
- [[SSOT Map]]
- 참조: [SSOT Ticket](../src/PH-CI-11_Structured_Concurrency_Anyio_Trio.md)
MD

cat > "$PH/PH-ST-06.md" <<'MD'
# PH-ST-06 — Obsidian Scripting Orchestration
- [[PH Map (Project Hub)|PH_MAP]]
- [[Ops/Safety Map]]
- 참조: [SSOT Ticket](../src/PH-ST-06_Obsidian_Scripting_Orchestration.md)
MD

cat > "$PH/PH-FIN-01.md" <<'MD'
# PH-FIN-01 — Julie CPA Finance Autopilot
- [[PH Map (Project Hub)|PH_MAP]]
- [[Ops/Safety Map]]
- 참조: [SSOT Ticket](../src/PH-FIN-01_Julie_CPA_Autopilot.md)
MD

# PH_MAP에 링크 주입(중복 방지)
python3 - <<'PY'
from pathlib import Path

ph_map = Path("config/obsidian/vault/_moc/ph/PH_MAP.md")
ph_map.parent.mkdir(parents=True, exist_ok=True)
txt = ph_map.read_text(encoding="utf-8") if ph_map.exists() else "# PH Map (Project Hub)\n\n"

def ensure(line: str):
  global txt
  if line not in txt:
    txt += line + "\n"

if "## CI / Quality" not in txt:
  txt += "\n## CI / Quality\n"
ensure("- [[PH-CI-11]]")

if "## Finance" not in txt:
  txt += "\n## Finance\n"
ensure("- [[PH-FIN-01]]")

if "## Obsidian / Active Knowledge" not in txt:
  txt += "\n## Obsidian / Active Knowledge\n"
ensure("- [[PH-ST-06]]")

ph_map.write_text(txt.rstrip() + "\n", encoding="utf-8")
print("[ok] PH_MAP updated")
PY

# 절대경로/스킴 누출 검사(0건이어야 정상)
# grep returns 1 if no match found, which is good here.
if rg -n "file://|<LOCAL_WORKSPACE>|/Users/|/home/|C:\\\\|\\\\Users\\\\" "$VAULT"; then
    echo "⚠️ Absolute paths found! Please review."
else
    echo "✅ No absolute paths found."
fi

echo "[done] SSOT tickets + vault nodes provisioned."
