#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

find_next_projects() {
  python3 - <<'PY'
import json, pathlib
root=pathlib.Path(".")
c=[]
for pj in root.rglob("package.json"):
    try:
        d=json.loads(pj.read_text(encoding="utf-8"))
    except Exception:
        continue
    deps=(d.get("dependencies") or {}) | (d.get("devDependencies") or {})
    if "next" in deps:
        c.append(str(pj.parent))
for x in sorted(set(c)):
    print(x)
PY
}

PM="pnpm"
if [ ! -f pnpm-lock.yaml ]; then
  if [ -f yarn.lock ]; then PM="yarn"; else PM="npm"; fi
fi

NEXT_DIR="${NEXT_APP_DIR:-}"
if [ -z "$NEXT_DIR" ]; then
  CANDS=()
  while IFS= read -r line; do
    CANDS+=("$line")
  done < <(find_next_projects)
  if [ "${#CANDS[@]}" -eq 0 ]; then
    echo "❌ Next.js 프로젝트를 찾지 못했습니다 (package.json에 next 의존성 없음)"
    exit 2
  fi
  if [ "${#CANDS[@]}" -gt 1 ]; then
    echo "❌ Next.js 프로젝트가 여러 개입니다. 아래 중 하나를 NEXT_APP_DIR로 지정해주세요:"
    printf '%s\n' "${CANDS[@]}"
    echo
    echo "예) NEXT_APP_DIR='${CANDS[0]}' bash scripts/phase6_debug_dashboard_missing_html.sh"
    exit 2
  fi
  NEXT_DIR="${CANDS[0]}"
fi

echo "=== TARGET NEXT APP ==="
echo "$NEXT_DIR"
echo "=== PACKAGE MANAGER ==="
echo "$PM"
echo

LOG="artifacts/phase6_dashboard_build_error.log"
mkdir -p artifacts

set +e
if [ "$PM" = "pnpm" ]; then
  (cd "$NEXT_DIR" && NEXT_TELEMETRY_DISABLED=1 pnpm build) 2>&1 | tee "$LOG"
  rc="${PIPESTATUS[0]}"
elif [ "$PM" = "yarn" ]; then
  (cd "$NEXT_DIR" && NEXT_TELEMETRY_DISABLED=1 yarn build) 2>&1 | tee "$LOG"
  rc="${PIPESTATUS[0]}"
else
  (cd "$NEXT_DIR" && NEXT_TELEMETRY_DISABLED=1 npm run build) 2>&1 | tee "$LOG"
  rc="${PIPESTATUS[0]}"
fi
set -e

if [ "$rc" -eq 0 ]; then
  echo
  echo "✅ build 성공. (HTML 누락 이슈 없음)"
  exit 0
fi

echo
echo "❌ build 실패 (rc=$rc). 누락된 .html 경로를 추출합니다..."

python3 - <<'PY'
import re, pathlib, sys
log = pathlib.Path("artifacts/phase6_dashboard_build_error.log").read_text(encoding="utf-8", errors="ignore")
patterns = [
    r"ENOENT: no such file or directory, open '([^']+\.html)'",
    r'ENOENT: no such file or directory, open "([^"]+\.html)"',
    r"Cannot find module '([^']+\.html)'",
    r'Cannot find module "([^"]+\.html)"',
]
hits=[]
for pat in patterns:
    for m in re.finditer(pat, log):
        hits.append(m.group(1))
hits=list(dict.fromkeys(hits))
print("missing_html_candidates:", len(hits))
for h in hits[:20]:
    print("-", h)
if not hits:
    sys.exit(3)
PY

echo
echo "=== grep where html is referenced (best-effort) ==="
if command -v rg >/dev/null 2>&1; then
  p_base=$(python3 - <<'PY'
import re, pathlib
import sys
log_path = pathlib.Path("artifacts/phase6_dashboard_build_error.log")
if not log_path.exists():
    sys.exit(0)
log = log_path.read_text(encoding="utf-8", errors="ignore")
m = re.search(r"(?:open ['\"])([^'\"]+\.html)(?:['\"])", log)
if not m:
    m = re.search(r"Cannot find module ['\"]([^'\"]+\.html)['\"]", log)
if m:
    print(pathlib.Path(m.group(1)).name)
PY
)
  if [ -n "$p_base" ]; then
    rg -n --hidden -S "$p_base" "$NEXT_DIR" || true
  fi
else
  echo "rg not installed. skipping."
fi

echo
echo "➡️ 로그 파일: $LOG"
