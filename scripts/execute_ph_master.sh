#!/bin/bash
set -euo pipefail

mkdir -p docs/tickets scripts

cat > docs/tickets/PH-CI-11_Structured_Concurrency_Anyio_Trio.md <<'MD'
# PH-CI-11 — Structured Concurrency Gate (Anyio/Trio) — SSOT

## 목적
AFO 비동기 실행을 “작업 생명주기(생성→실행→취소/정리)”가 보장되는 구조로 고정한다.

## Gate 규율 (Hard Rule)
- **허용**: `anyio.create_task_group()` (표준)
- **권장**: `anyio.move_on_after()`, `anyio.fail_after()` (취소/타임아웃)
- **금지**: `asyncio.create_task()` (고아 task 위험)
- **예외**: 기존 레거시 호환이 필요한 경우, 반드시 “격리 영역 + 테스트 + 주석”으로 봉인

## 예외 전파 표준
- 병렬 실패는 `ExceptionGroup`으로 표준화한다.
- 테스트에서 `except*`로 분기 처리한다.

## Instrumentation 표준
- Task 시작/종료/취소를 로그로 남긴다.
- 가능하면 TraceContext(OTel)와 함께 로깅한다.

## 검증(Tests)
- 취소 전파: `move_on_after()`로 하위 task 정리 보장
- 다중 실패: TaskGroup에서 2개 이상 예외 발생 시 ExceptionGroup으로 수렴
- 정리 보장: `finally`/cleanup이 반드시 호출되는지 확인

## CI Structured Gate (Soft)
- PR 단계에서 `asyncio.create_task(` 사용 유무를 grep로 탐지하여 경고/차단(프로젝트 정책에 따라).
MD

cat > docs/tickets/PH-ST-06_Obsidian_Scripting_Orchestration.md <<'MD'
# PH-ST-06 — Obsidian Scripting Orchestration (Active Neural Network) — SSOT

## 목적
Visual SSOT Vault를 “실행 가능한 지식(Active)”로 확장하되,
보안/프라이버시/자동실행 리스크를 0에 가깝게 유지한다.

## 원칙 (Non-negotiables)
- 기본값은 **OFF** (자동 실행 금지)
- 로컬 경로/시크릿 유출 금지
- 실행 스크립트는 Vault 밖(`scripts/`)에서 실행하고 결과만 Vault에 반영

## 1차 범위(MVP)
- Auto-MOC-Updater: Vault 링크/허브 문서 자동 갱신
- Link Density 리포트: 노드 수/링크 수/고립 노드 수 산출

## 산출물
- `scripts/obsidian/` 아래에 “생성/업데이트 스크립트”
- `config/obsidian/vault/_moc/`에 결과 요약 노트(수동 검토 후 반영)
MD

cat > docs/tickets/PH-FIN-01_Julie_CPA_Autopilot.md <<'MD'
# PH-FIN-01 — Julie CPA Finance Autopilot (Input → Label → Queue) — SSOT

## 목표
재무 데이터 정리를 “자율 주행 보조(Autopilot Assist)”로 만들되,
최종 판단(세무/회계/윤리)은 Julie CPA 승인으로만 확정한다.

## 3-Step Minimal-Invasive
1) Input: CSV/문서/이메일(옵션)을 Inbox로 수집  
2) Labeling: 카테고리 + 리스크 플래그(사마의 필터)  
3) Queue: Julie 리뷰 큐 생성 → 승인 후 후속 작업(수동/반자동)

## 안전장치
- 자동 posting/auto-commit 금지
- PII/시크릿 저장 금지(Repo 밖 raw)
- 모든 결과물은 artifacts로 분리
MD

cat > scripts/provision_ph_master_plan_ssot.sh <<'BASH'
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
VAULT="$ROOT/config/obsidian/vault"
SRC="$VAULT/src"
PH="$VAULT/ph"
PH_MOC="$VAULT/_moc/ph"
PH_MAP="$PH_MOC/PH_MAP.md"

mkdir -p "$SRC" "$PH" "$PH_MOC"

mkrel_link () {
  local target="$1"
  local link="$2"
  mkdir -p "$(dirname "$link")"
  python3 - <<PY
from pathlib import Path
t=Path("$target").resolve()
l=Path("$link").resolve()
rel=str(t.relative_to(l.parent)) if False else str(Path.relpath(t, l.parent))
print(rel)
PY
}

# 상대경로 symlink 생성 (실패하면 copy로 폴백)
link_or_copy () {
  local target="$1"
  local link="$2"
  local rel
  rel="$(python3 - <<PY
from pathlib import Path
t=Path("$target").resolve()
l=Path("$link").resolve()
print(Path.relpath(t, l.parent))
PY
)"
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
- 참조: [SSOT Ticket](src/PH-CI-11_Structured_Concurrency_Anyio_Trio.md)
MD

cat > "$PH/PH-ST-06.md" <<'MD'
# PH-ST-06 — Obsidian Scripting Orchestration
- [[PH Map (Project Hub)|PH_MAP]]
- [[Ops/Safety Map]]
- 참조: [SSOT Ticket](src/PH-ST-06_Obsidian_Scripting_Orchestration.md)
MD

cat > "$PH/PH-FIN-01.md" <<'MD'
# PH-FIN-01 — Julie CPA Finance Autopilot
- [[PH Map (Project Hub)|PH_MAP]]
- [[Ops/Safety Map]]
- 참조: [SSOT Ticket](src/PH-FIN-01_Julie_CPA_Autopilot.md)
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
rg -n "file://|<LOCAL_WORKSPACE>|/Users/|/home/|C:\\\\|\\\\Users\\\\" "$VAULT" || true

echo "[done] SSOT tickets + vault nodes provisioned."
BASH

bash scripts/provision_ph_master_plan_ssot.sh
