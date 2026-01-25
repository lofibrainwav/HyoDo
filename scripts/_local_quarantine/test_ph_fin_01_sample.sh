set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

export AFO_FIN_ENABLED=1

INBOX_DIR="inbox/fin/csv"
OUT_DIR="artifacts/fin/ph_fin_01"
mkdir -p "$INBOX_DIR" "$OUT_DIR"

SAMPLE="$INBOX_DIR/sample_ph_fin_01.csv"
TS="$(date +%Y%m%d_%H%M%S)"

cat > "$SAMPLE" <<'CSV'
Date,Description,Amount
2025-12-01,COSTCO WHOLESALE,-152.33
2025-12-01,AMAZON MKTPLACE PMTS,-49.99
2025-12-02,CHARTER COMM,-129.00
2025-12-03,SHELL OIL,-63.21
2025-12-04,IRS PAYMENT,-1200.00
2025-12-05,ADP PAYROLL FEE,-89.00
2025-12-06,TRANSFER TO SAVINGS,-500.00
2025-12-07,RENT PAYMENT,-3200.00
2025-12-08,CLIENT DEPOSIT,+4500.00
CSV

LABELER="packages/afo-core/AFO/julie_cpa/csv_inbox_labeler.py"
test -f "$LABELER" || { echo "[FAIL] labeler not found: $LABELER"; exit 1; }

LOG="$OUT_DIR/run_${TS}.log"

echo "Running labeler on $SAMPLE..."
set +e
# CORRECTION: Added --in for argparse compatibility
python3 "$LABELER" --in "$SAMPLE" --out-dir "$OUT_DIR" >"$LOG" 2>&1
RC=$?
set -e

if [ "$RC" -ne 0 ]; then
  echo "[FAIL] labeler run failed (exit=$RC)"
  echo "---- last 20 lines of log ----"
  tail -n 20 "$LOG" || true
  echo
  echo "[HINT] try this to see supported CLI:"
  echo "python3 $LABELER --help"
  exit 1
fi

echo "[OK] labeler run success"
echo

echo "== outputs in $OUT_DIR =="
ls -lah "$OUT_DIR" | grep "$TS" || true
echo

# Show the generated Markdown Queue
MD_REPORT=$(find "$OUT_DIR" -name "queue_report.*.md" | head -n 1)
if [ -f "$MD_REPORT" ]; then
    echo "== Content of Queue Report =="
    cat "$MD_REPORT"
    echo
else
    echo "[WARN] No Queue Report found"
fi

SUMMARY="$OUT_DIR/julie_summary_template_${TS}.md"
cat > "$SUMMARY" <<EOF
As-of: $(date -I) (America/Los_Angeles)

1) P0/P1 (결정 1~3개)
- [__] 요약: __ | 결정(A/B): __ | 리스크: __ | 근거: __

2) WAITING / Missing
- [__] Missing: __ | 상대: __ | 내가 할 일: __

3) DRAFT (내가 만들 초안)
- [__] 대상: __ | 톤(정중/단호): __ | 핵심 1줄: __

4) 오늘 끝내면 평온해지는 1개
- __
EOF

echo "[OK] summary template created: $SUMMARY"
