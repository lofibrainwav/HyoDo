#!/bin/bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

fail() { echo "[FAIL] $*"; exit 1; }
info() { echo "[INFO] $*"; }

# Gate 0: prevent accidental “Julie mode obsession”
: "${AFO_FIN_ENABLED:=0}"
if [ "$AFO_FIN_ENABLED" != "1" ]; then
  info "AFO_FIN_ENABLED!=1 -> Provisioning OK, but runtime will remain LOCKED by default."
fi

# Gate 1: clean working tree recommended
if ! git diff --quiet || ! git diff --cached --quiet; then
  fail "Working tree is dirty. Commit/stash before provisioning."
fi

info "Creating directories"
mkdir -p config/julie_cpa
mkdir -p inbox/fin/csv
mkdir -p artifacts/fin/ph_fin_01
mkdir -p packages/afo-core/AFO/julie_cpa
mkdir -p scripts
mkdir -p tests

backup_if_exists() {
  local p="$1"
  if [ -f "$p" ] || [ -L "$p" ]; then
    local ts
    ts="$(date +%Y%m%d_%H%M%S)"
    cp -a "$p" "${p}.bak.${ts}"
    info "Backup: $p -> ${p}.bak.${ts}"
  fi
}

info "Writing rules config (editable by Julie)"
backup_if_exists "config/julie_cpa/label_rules.json"
cat > config/julie_cpa/label_rules.json <<'JSON'
{
  "currency": "USD",
  "high_risk_amount_usd": 1000.0,
  "labels": [
    {"label": "investment", "match_any": ["vanguard", "fidelity", "robinhood", "schwab", "brokerage", "401k", "ira"]},
    {"label": "rent", "match_any": ["rent", "lease", "landlord", "apartment"]},
    {"label": "utilities", "match_any": ["electric", "gas", "water", "internet", "spectrum", "verizon", "att", "comcast"]},
    {"label": "groceries", "match_any": ["costco", "trader joe", "whole foods", "ralph", "grocery", "market"]},
    {"label": "transport", "match_any": ["uber", "lyft", "gas station", "shell", "chevron", "exxon"]},
    {"label": "fees_waste", "match_any": ["fee", "overdraft", "late fee", "interest charge"]}
  ],
  "always_queue_labels": ["unknown", "fees_waste"],
  "redact_description_in_reports": true
}
JSON

info "Writing Python labeler (stdlib only)"
backup_if_exists "packages/afo-core/AFO/julie_cpa/__init__.py"
cat > packages/afo-core/AFO/julie_cpa/__init__.py <<'PY'
PY

backup_if_exists "packages/afo-core/AFO/julie_cpa/csv_inbox_labeler.py"
cat > packages/afo-core/AFO/julie_cpa/csv_inbox_labeler.py <<'PY'
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Rule:
    label: str
    match_any: list[str]


@dataclass(frozen=True)
class Ruleset:
    currency: str
    high_risk_amount_usd: float
    labels: list[Rule]
    always_queue_labels: set[str]
    redact_description_in_reports: bool


def _load_rules(path: Path) -> Ruleset:
    raw = json.loads(path.read_text(encoding="utf-8"))
    labels = [Rule(label=x["label"], match_any=list(x.get("match_any", []))) for x in raw.get("labels", [])]
    return Ruleset(
        currency=str(raw.get("currency", "USD")),
        high_risk_amount_usd=float(raw.get("high_risk_amount_usd", 1000.0)),
        labels=labels,
        always_queue_labels=set(raw.get("always_queue_labels", ["unknown"])),
        redact_description_in_reports=bool(raw.get("redact_description_in_reports", True)),
    )


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _pick_label(desc: str, rules: Ruleset) -> str:
    d = _norm(desc)
    for rule in rules.labels:
        for kw in rule.match_any:
            if _norm(kw) in d:
                return rule.label
    return "unknown"


def _parse_amount(row: dict[str, str]) -> float | None:
    for k in ("amount", "Amount", "amt", "Amt", "value", "Value"):
        if k in row and row[k].strip():
            s = row[k].strip().replace(",", "")
            try:
                return float(s)
            except ValueError:
                return None
    return None


def _get_desc(row: dict[str, str]) -> str:
    for k in ("description", "Description", "memo", "Memo", "name", "Name", "merchant", "Merchant"):
        if k in row and row[k].strip():
            return row[k].strip()
    return ""


def _get_date(row: dict[str, str]) -> str:
    for k in ("date", "Date", "posted", "Posted", "transaction_date", "Transaction Date"):
        if k in row and row[k].strip():
            return row[k].strip()
    return ""


def _redact(s: str) -> str:
    if not s:
        return s
    if len(s) <= 6:
        return "***"
    return s[:3] + "***" + s[-2:]


def label_csv_file(csv_path: Path, rules: Ruleset) -> dict[str, Any]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, str]] = [dict(r) for r in reader]

    labeled: list[dict[str, Any]] = []
    queued: list[dict[str, Any]] = []
    skipped = 0

    for row in rows:
        amount = _parse_amount(row)
        if amount is None:
            skipped += 1
            continue

        desc = _get_desc(row)
        date_s = _get_date(row)

        label = _pick_label(desc, rules)
        abs_amount = abs(amount)
        risk = "high" if abs_amount >= rules.high_risk_amount_usd else "normal"
        needs_review = (label in rules.always_queue_labels) or (risk == "high")

        item = {
            "date": date_s,
            "amount": amount,
            "currency": rules.currency,
            "label": label,
            "risk": risk,
            "description": _redact(desc) if rules.redact_description_in_reports else desc,
            "source_file": str(csv_path.as_posix()),
        }

        labeled.append(item)
        if needs_review:
            queued.append(item)

    counts: dict[str, int] = {}
    for x in labeled:
        counts[x["label"]] = counts.get(x["label"], 0) + 1

    return {
        "file": str(csv_path.as_posix()),
        "total_rows": len(rows),
        "skipped_rows": skipped,
        "labeled_rows": len(labeled),
        "label_counts": counts,
        "queue_size": len(queued),
        "labeled": labeled,
        "queue": queued,
    }


def _iter_csv_inputs(p: Path) -> Iterable[Path]:
    if p.is_file() and p.suffix.lower() == ".csv":
        yield p
        return
    if p.is_dir():
        for f in sorted(p.glob("*.csv")):
            yield f


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="CSV file or directory")
    ap.add_argument("--rules", default="config/julie_cpa/label_rules.json", help="Rules JSON path")
    ap.add_argument("--out-dir", default="artifacts/fin/ph_fin_01", help="Output directory")
    ap.add_argument("--lock-env", default="AFO_FIN_ENABLED", help="Env var required to run (value must be '1')")
    ns = ap.parse_args(argv)

    lock_env = str(ns.lock_env)
    if os.getenv(lock_env, "0") != "1":
        print(f"[LOCKED] {lock_env}!=1 (default OFF). Set {lock_env}=1 to run.", file=sys.stderr)
        return 3

    rules = _load_rules(Path(ns.rules))
    inp = Path(ns.inp)
    out_dir = Path(ns.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    outputs: list[Path] = []

    processed = 0
    for csv_path in _iter_csv_inputs(inp):
        processed += 1
        report = label_csv_file(csv_path, rules)
        safe_name = csv_path.stem.replace(" ", "_")
        out_path = out_dir / f"{safe_name}.report.{run_id}.json"
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs.append(out_path)

    if processed == 0:
        print("[WARN] No CSV files found.", file=sys.stderr)
        return 2

    index = {"run_id": run_id, "reports": [p.as_posix() for p in outputs]}
    (out_dir / f"index.{run_id}.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(json.dumps(index, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

info "Writing run wrapper (keeps PYTHONPATH explicit)"
backup_if_exists "scripts/run_ph_fin_01_csv_inbox.sh"
cat > scripts/run_ph_fin_01_csv_inbox.sh <<'SH'
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

: "${AFO_FIN_ENABLED:=0}"
export AFO_FIN_ENABLED

PYTHONPATH="$ROOT/packages/afo-core:${PYTHONPATH:-}" \
python3 -m AFO.julie_cpa.csv_inbox_labeler "$@"
SH
chmod +x scripts/run_ph_fin_01_csv_inbox.sh

info "Writing sample CSV (optional)"
if [ ! -f "inbox/fin/csv/example.csv" ]; then
  cat > inbox/fin/csv/example.csv <<'CSV'
date,description,amount
2025-12-01,Costco Wholesale,-123.45
2025-12-02,Vanguard Brokerage,-2500.00
2025-12-03,Overdraft Fee,-35.00
CSV
fi

info "Writing pytest"
backup_if_exists "tests/test_ph_fin_01_csv_inbox_labeler.py"
cat > tests/test_ph_fin_01_csv_inbox_labeler.py <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from AFO.julie_cpa.csv_inbox_labeler import _load_rules, label_csv_file


def test_labeler_basic(tmp_path: Path) -> None:
    rules_path = Path("config/julie_cpa/label_rules.json")
    rules = _load_rules(rules_path)

    csv_path = tmp_path / "t.csv"
    csv_path.write_text(
        "date,description,amount\n"
        "2025-12-01,Costco,-10.00\n"
        "2025-12-02,Vanguard,-2000.00\n"
        "2025-12-03,Something,5.00\n",
        encoding="utf-8",
    )

    report = label_csv_file(csv_path, rules)
    assert report["labeled_rows"] == 3
    assert report["label_counts"]["groceries"] == 1
    assert report["label_counts"]["investment"] == 1
    assert report["label_counts"]["unknown"] == 1
    assert report["queue_size"] >= 2
    json.dumps(report)
PY

info "Done. Next:"
info "1) Run: AFO_FIN_ENABLED=1 bash scripts/run_ph_fin_01_csv_inbox.sh --in inbox/fin/csv"
info "2) Outputs: artifacts/fin/ph_fin_01/*.json"
