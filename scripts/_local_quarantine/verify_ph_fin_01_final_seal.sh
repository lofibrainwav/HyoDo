set -euo pipefail

echo "== PH-FIN-01 FINAL SEAL CHECK =="
echo "root: $(git rev-parse --show-toplevel)"
echo

echo "== 1) GIT CLEAN + LAST COMMIT =="
git status -sb
git diff --stat
git diff --cached --stat
echo
git log --oneline -3
echo

echo "== 2) DATA MUST NOT BE TRACKED (should print nothing) =="
git ls-files inbox/fin artifacts/fin 2>/dev/null || true
echo

echo "== 3) .gitignore EFFECTIVE CHECK (if paths exist) =="
test -d inbox/fin && git check-ignore -v inbox/fin || true
test -d artifacts/fin && git check-ignore -v artifacts/fin || true
echo

echo "== 4) FIN LABELER MUST NOT CONTAIN IEP LINKING =="
rg -n "IEP|evidence|progress data|SLP|SAI|AUT|IEE" packages/afo-core/AFO/julie_cpa 2>/dev/null || true
echo

echo "== 5) DANGEROUS OPS SCAN (should be empty or unrelated libs only) =="
rg -n "smtplib|sendmail|stripe|plaid|twilio|googleapiclient|boto3|ftplib|paramiko|requests|httpx" \
  packages/afo-core/AFO/julie_cpa packages/afo-core/AFO/api_server.py 2>/dev/null || true
echo

echo "== 6) ABSOLUTE PATH LEAK CHECK (vault only; artifacts may not exist) =="
rg -n "file://|<LOCAL_WORKSPACE>|/Users/|/home/|C:\\\\|\\\\Users\\\\" config/obsidian/vault 2>/dev/null || true
echo

echo "== 7) CI LOCK (truth gate) =="
bash scripts/ci_lock_protocol.sh
echo
echo "== ✅ SEALED CHECK COMPLETE =="
