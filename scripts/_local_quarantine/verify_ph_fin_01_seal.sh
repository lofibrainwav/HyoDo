set -euo pipefail

echo "== PH-FIN-01 SEAL CHECK =="

echo
echo "== 1) GIT STATE =="
git status -sb
echo
git log --oneline -5

echo
echo "== 2) DATA SHOULD NOT BE TRACKED (recommended) =="
git ls-files inbox/fin/csv artifacts/fin 2>/dev/null || true

echo
echo "== 3) DANGEROUS ACTION SCAN (must be empty) =="
rg -n "smtplib|sendmail|twilio|stripe|plaid|requests|httpx|boto3|googleapiclient|ftplib|paramiko|subprocess\.run|os\.system" packages/afo-core/AFO/julie_cpa packages/afo-core/AFO/api_server.py 2>/dev/null || true

echo
echo "== 4) RUN LABELER (local-only) =="
export AFO_FIN_ENABLED=1
python3 -c "import sys; print('python ok:', sys.version.split()[0])"
python3 packages/afo-core/AFO/julie_cpa/csv_inbox_labeler.py --help 2>/dev/null || true

echo
echo "== 5) ABSOLUTE PATH LEAK CHECK (vault+artifacts) =="
rg -n "file://|<LOCAL_WORKSPACE>|/Users/|/home/|C:\\\\|\\\\Users\\\\" config/obsidian/vault artifacts/fin 2>/dev/null || true

echo
echo "== DONE =="
