#!/bin/bash
set -euo pipefail

ts="$(date +%Y%m%d_%H%M%S)"
out="artifacts/ssot_validation_${ts}.txt"
mkdir -p artifacts
exec > >(tee "$out") 2>&1

echo "AS_OF=$(date -Iseconds)"
git fetch origin
git status -sb
git rev-parse HEAD
git rev-parse origin/main || true

echo "=== SKILLS COUNT ==="
python - <<'PY'
import importlib, inspect
mods = ["AFO.afo_skills_registry","afo_skills_registry"]
m=None
for name in mods:
  try:
    m=importlib.import_module(name); break
  except Exception: pass
print("module:", getattr(m,"__name__",None))
print("file:", getattr(m,"__file__",None))
cnt=None
for k,v in vars(m).items():
  if isinstance(v,(list,tuple,dict)) and "skill" in k.lower():
    try:
      cnt = len(v)
      print("candidate:", k, "len=", cnt)
    except Exception: pass
print("skills_count=", cnt)
PY

echo "=== TICKETS ==="
if [ -f TICKETS.md ]; then
  python - <<'PY'
import re, pathlib
t = pathlib.Path("TICKETS.md").read_text(encoding="utf-8", errors="ignore")
done = len(re.findall(r"^\s*[-*]\s*\[x\]", t, flags=re.M))
todo = len(re.findall(r"^\s*[-*]\s*\[ \]", t, flags=re.M))
print({"done": done, "todo": todo})
PY
else
  echo "TICKETS.md not found"
fi

echo "=== TEST FILES COUNT ==="
python - <<'PY'
import os
c=0
for r,_,fs in os.walk("."):
  for f in fs:
    if f.startswith("test_") and f.endswith(".py"):
      c+=1
print("test_files_like_pytest=", c)
PY

echo "=== DOCKER ==="
if command -v docker >/dev/null 2>&1; then
  docker ps --format 'table {{.Names}}\t{{.Status}}' || true
else
  echo "docker not found"
fi

echo "=== API LATENCY (sample) ==="
if command -v curl >/dev/null 2>&1; then
  for i in 1 2 3 4 5; do
    curl -sS -o /dev/null -w "time_total=%{time_total}\n" "http://127.0.0.1:8010/health" || true
  done
fi

echo "=== PROCESSES (top-level) ==="
ps aux | head -n 20 || true

echo "EVIDENCE_FILE=$out"
