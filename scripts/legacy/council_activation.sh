#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

RUNNER=""
if command -v poetry >/dev/null 2>&1 && grep -q "^\[tool\.poetry\]" pyproject.toml 2>/dev/null; then
  RUNNER="poetry run"
elif [ -f "packages/afo-core/.venv/bin/python" ]; then
  RUNNER="packages/afo-core/.venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
  RUNNER=".venv/bin/python"
fi

echo "=== Phase 4 / Action 1: Council Activation (Discovery) ==="

echo "=== 0) Python runner ==="
if [[ "$RUNNER" == *"python"* ]]; then
  $RUNNER -V
else
  $RUNNER python -V
fi

echo "=== 1) Find council/strategists definitions (search) ==="
if command -v rg >/dev/null 2>&1; then
  rg -n --hidden --glob '!**/.git/**' \
    "Council|Council of Minds|Strategist|장영실|이순신|신사임당|Jang|Yi|Shin" \
    packages scripts AFO 2>/dev/null || true
else
  grep -RIn "Council\|Council of Minds\|Strategist\|장영실\|이순신\|신사임당\|Jang\|Yi\|Shin" \
    packages scripts AFO 2>/dev/null || true
fi

echo "=== 2) Re-verify tools (smoke + philosophy) ==="
find_one () {
  local name="$1"
  find . -maxdepth 6 -type f -name "$name" | head -n 1 || true
}

SMOKE="$(find_one mcp_smoke_test_afo_skills.py)"
PHILO="$(find_one verify_all_skills_trinity_score.py)"
FULL="$(find_one skill_verify_full_stack.py)"

[ -n "$SMOKE" ] || { echo "❌ missing mcp_smoke_test_afo_skills.py"; exit 1; }
[ -n "$PHILO" ] || { echo "❌ missing verify_all_skills_trinity_score.py"; exit 1; }
[ -n "$FULL" ] || echo "⏭️  skill_verify_full_stack.py not found (skip)"

echo "✅ smoke: $SMOKE"
echo "✅ philosophy: $PHILO"
[ -n "$FULL" ] && echo "✅ full-stack: $FULL" || true

if [[ "$RUNNER" == *"python"* ]]; then
  $RUNNER "$SMOKE"
  $RUNNER "$PHILO"
  if [ -n "$FULL" ]; then
    $RUNNER "$FULL"
  fi
else
  $RUNNER python "$SMOKE"
  $RUNNER python "$PHILO"
  if [ -n "$FULL" ]; then
    $RUNNER python "$FULL"
  fi
fi

echo "=== 3) Proof-of-life demo: skills API execute (best-effort, no guessing lock-in) ==="
mkdir -p scripts

cat > scripts/demo_mcp_execute.py <<'PY'
import os, sys, json, time
import requests

BASE = os.environ.get("AFO_BASE_URL", "http://localhost:8010").rstrip("/")
S = requests.Session()
S.headers.update({"accept": "application/json"})

def get_json(url: str):
  r = S.get(url, timeout=10)
  return r.status_code, r.headers.get("content-type",""), r.text

def post_json(url: str, payload: dict):
  r = S.post(url, json=payload, timeout=20)
  return r.status_code, r.headers.get("content-type",""), r.text

def main():
  urls = [
    f"{BASE}/api/health/comprehensive",
    f"{BASE}/api/skills",
  ]
  print(f"[base] {BASE}")

  for u in urls:
    sc, ct, body = get_json(u)
    print(f"[GET] {u} -> {sc} {ct}")
    if sc != 200:
      print(body[:800])
      return 1

  sc, ct, body = get_json(f"{BASE}/api/skills")
  data = None
  try:
    data = json.loads(body)
  except Exception:
    print("[err] /api/skills returned non-json")
    print(body[:800])
    return 1

  skills = data.get("skills") if isinstance(data, dict) else None
  if not skills:
    print("[err] no skills list found in /api/skills payload keys:", list(data.keys()) if isinstance(data, dict) else type(data))
    return 1

  skill_id = os.environ.get("SKILL_ID")
  if not skill_id:
    first = skills[0]
    skill_id = first.get("skill_id") or first.get("id") or first.get("name")
  if not skill_id:
    print("[err] could not infer a skill_id")
    return 1

  print("[pick] skill_id =", skill_id)

  execute_candidates = [
    (f"{BASE}/api/skills/execute", {"skill_id": skill_id, "args": {}}),
    (f"{BASE}/api/skills/execute", {"skill_id": skill_id, "input": {}}),
    (f"{BASE}/api/skills/execute", {"skill_id": skill_id, "params": {}}),
    (f"{BASE}/api/skills/execute", {"id": skill_id, "args": {}}),
  ]

  for url, payload in execute_candidates:
    sc, ct, body = post_json(url, payload)
    print(f"[POST] {url} payload_keys={list(payload.keys())} -> {sc} {ct}")
    if sc == 200:
      print(body[:1200])
      return 0
    print(body[:400])

  print("[warn] execute endpoint shape differs. Above attempts show exact server responses.")
  return 2

if __name__ == "__main__":
  raise SystemExit(main())
PY

if [[ "$RUNNER" == *"python"* ]]; then
  $RUNNER scripts/demo_mcp_execute.py || true
else
  $RUNNER python scripts/demo_mcp_execute.py || true
fi

echo "=== RESULT ==="
echo "✅ Phase 4 / Action 1 executed: smoke + philosophy + demo attempted"
echo "ℹ️  If demo execute failed, the script printed the server’s exact expected schema."
