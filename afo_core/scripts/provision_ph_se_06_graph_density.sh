#!/bin/bash
set -euo pipefail

# PH-SE-06: Graph Density (Links) — code provisioning
# This script increases the density of the Obsidian Graph by creating Phase Hubs (PH)
# and injecting high-density links into existing MOCs.

if [ -d "packages/afo-core" ]; then
    ROOT="$(pwd)"
elif [ -d "../packages/afo-core" ]; then
    cd ..
    ROOT="$(pwd)"
else
    ROOT="$(git rev-parse --show-toplevel)"
fi

VAULT_REL="config/obsidian/vault"
VAULT="$ROOT/$VAULT_REL"

echo "💎 Enhancing Graph Density in: $VAULT"

mkdir -p "$VAULT/_moc" "$VAULT/_moc/ph" "$VAULT/ph"

export ROOT
export VAULT

python3 - <<'PY'
import os, re
from pathlib import Path

root = Path(os.environ["ROOT"])
vault = Path(os.environ["VAULT"])

home = vault / "00_HOME.md"
moc = vault / "_moc"
ph_dir = vault / "ph"
ph_moc = moc / "ph"

def read(p: Path) -> str:
  return p.read_text(encoding="utf-8") if p.exists() else ""

def write(p: Path, s: str) -> None:
  p.parent.mkdir(parents=True, exist_ok=True)
  p.write_text(s.rstrip() + "\n", encoding="utf-8")

def ensure_link_block(doc: Path, header: str, bullets: list[str]) -> None:
  txt = read(doc)
  if not txt:
      print(f"⚠️ Warning: {doc} not found, creating new.")
      txt = f"# {doc.stem}\n"
      
  if header not in txt:
    txt = txt.rstrip() + "\n\n" + header + "\n"
  for b in bullets:
    if b not in txt:
      txt += b + "\n"
  write(doc, txt)
  print(f"✅ Updated {doc.name} with links")

# ---- 1) PH 허브(MOC) 생성 ----
ph_index = ph_moc / "PH_MAP.md"
write(ph_index, "\n".join([
  "# PH Map (Project Hub)",
  "",
  "- [[00_HOME — Visual SSOT|00_HOME]]",
  "- [[SSOT_MAP|SSOT Map]]",
  "- [[OBS_MAP|Observability Map]]",
  "- [[OPS_MAP|Ops/Safety Map]]",
  "",
  "## Observability Line",
  "- [[PH-OBS-01]]",
  "- [[PH-OBS-02]]",
  "- [[PH-OBS-03]]",
  "- [[PH-OBS-04]]",
  "",
  "## Knowledge Line",
  "- [[PH-SE-05]]",
  "- [[PH-SE-06]]",
]))
print(f"✅ Created PH Map at {ph_index.name}")

# ---- 2) PH 노드들(그래프용 “중간 허브”) 생성 ----
def ph_note(name: str, body_lines: list[str]):
  p = ph_dir / f"{name}.md"
  if p.exists():
    return
  write(p, "\n".join([f"# {name}", ""] + body_lines))
  print(f"✅ Created PH Node: {name}")

ph_note("PH-OBS-01", [
  "- [[OBS_MAP|Observability Map]]",
  "- [[PH-OBS-02]]",
  "- 핵심: OTel Collector 단일화 → Tempo/Loki/Prometheus",
])
ph_note("PH-OBS-02", [
  "- [[OBS_MAP|Observability Map]]",
  "- [[PH-OBS-01]]",
  "- [[PH-OBS-03]]",
  "- 핵심: Grafana provisioning(데이터소스/대시보드) 코드 봉인",
])
ph_note("PH-OBS-03", [
  "- [[OBS_MAP|Observability Map]]",
  "- [[PH-OBS-02]]",
  "- [[PH-OBS-04]]",
  "- 핵심: Logs/Traces/Metrics 대시보드 3종 세트",
])
ph_note("PH-OBS-04", [
  "- [[OBS_MAP|Observability Map]]",
  "- [[OPS_MAP|Ops/Safety Map]]",
  "- [[PH-OBS-03]]",
  "- 핵심: Service Graph + Alerting Export 파이프라인",
])

ph_note("PH-SE-05", [
  "- [[SSOT_MAP|SSOT Map]]",
  "- [[OPS_MAP|Ops/Safety Map]]",
  "- [[PH-SE-06]]",
  "- 핵심: Vault + 상대경로 symlink + MOC 골격",
])
ph_note("PH-SE-06", [
  "- [[SSOT_MAP|SSOT Map]]",
  "- [[OBS_MAP|Observability Map]]",
  "- [[OPS_MAP|Ops/Safety Map]]",
  "- 핵심: 링크 밀도 증폭(그래프 신경망 완성)",
])

# ---- 3) 기존 MOC들에 “밀도 링크” 박기 ----
ssot_map = moc / "SSOT_MAP.md"
obs_map = moc / "OBS_MAP.md"
ops_map = moc / "OPS_MAP.md"

ensure_link_block(ssot_map, "## PH Links", [
  "- [[PH-OBS-01]]",
  "- [[PH-SE-05]]",
  "- [[PH-SE-06]]",
  "- [[PH_MAP|PH Map (Project Hub)]]",
])

ensure_link_block(obs_map, "## PH Observability Links", [
  "- [[PH-OBS-01]]",
  "- [[PH-OBS-02]]",
  "- [[PH-OBS-03]]",
  "- [[PH-OBS-04]]",
  "- [[PH_MAP|PH Map (Project Hub)]]",
])

ensure_link_block(ops_map, "## Ops Links", [
  "- [[PH-OBS-04]]",
  "- [[PH-SE-05]]",
  "- [[PH-SE-06]]",
  "- [[PH_MAP|PH Map (Project Hub)]]",
])

# ---- 4) 00_HOME에 PH 허브 링크 추가 ----
home_txt = read(home)
if "## Phase Hub" not in home_txt:
  insert = "\n".join([
    "",
    "## Phase Hub",
    "- [PH Map](_moc/ph/PH_MAP.md)",
  ])
  home_txt = home_txt.rstrip() + insert + "\n"
  write(home, home_txt)
  print("✅ Linked PH Map to 00_HOME")
else:
  print("ℹ️  PH Map already linked in 00_HOME")

print("[ok] PH-SE-06 graph density notes created/updated")
PY

echo "[ok] PH-SE-06 provision complete: config/obsidian/vault"
