from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True)
class Rule:
    label: str
    match_any: list[str]
    default: bool = False


@dataclass(frozen=True)
class Ruleset:
    currency: str
    high_risk_amount_usd: float
    domains: list[Rule]
    actions: list[Rule]
    default_priority: str
    high_risk_priority: str
    always_queue_labels: set[str]
    evidence_index_path: str
    evidence_map: dict[str, str] = field(default_factory=dict)


def _load_evidence_map(index_path: Path) -> dict[str, str]:
    """Parses docs/evidence/INDEX.md to create a keyword -> file path map."""
    if not index_path.exists():
        return {}

    mapping = {}
    content = index_path.read_text(encoding="utf-8")
    # Simple parser: looks for "- [LABEL] Filename" ... "- file: path"
    # For now, we just map the BASENAME or Label to the path.
    # A more robust regex could be used.

    lines = content.splitlines()
    current_label = ""
    for line in lines:
        m_label = re.search(r"- \[(.*?)\] (.*)", line)
        if m_label:
            current_label = m_label.group(1).lower()
            continue

        m_file = re.search(r"- file: (.*)", line)
        if m_file and current_label:
            path = m_file.group(1).strip()
            mapping[current_label] = path
            # Also map "iep" if the label contains iep
            if "iep" in current_label:
                mapping["iep"] = path
    return mapping


def _load_rules(path: Path, root_dir: Path) -> Ruleset:
    raw = json.loads(path.read_text(encoding="utf-8"))

    domains = [
        Rule(label=x["label"], match_any=list(x.get("match_any", [])))
        for x in raw.get("domains", [])
    ]
    actions = [
        Rule(
            label=x["label"],
            match_any=list(x.get("match_any", [])),
            default=x.get("default", False),
        )
        for x in raw.get("actions", [])
    ]

    evidence_path_str = raw.get("evidence_index_path", "docs/evidence/INDEX.md")
    evidence_path = root_dir / evidence_path_str
    evidence_map = _load_evidence_map(evidence_path)

    return Ruleset(
        currency=str(raw.get("currency", "USD")),
        high_risk_amount_usd=float(raw.get("high_risk_amount_usd", 1000.0)),
        domains=domains,
        actions=actions,
        default_priority=raw.get("default_priority", "P2"),
        high_risk_priority=raw.get("high_risk_priority", "P1"),
        always_queue_labels=set(raw.get("always_queue_labels", ["TAX", "IEP"])),
        evidence_index_path=evidence_path_str,
        evidence_map=evidence_map,
    )


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _pick_label(desc: str, rules: Iterable[Rule]) -> str:
    d = _norm(desc)
    default_label = "UNKNOWN"
    for rule in rules:
        if rule.default:
            default_label = rule.label
        for kw in rule.match_any:
            if _norm(kw) in d:
                return rule.label
    return default_label


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
    for k in (
        "description",
        "Description",
        "memo",
        "Memo",
        "name",
        "Name",
        "merchant",
        "Merchant",
    ):
        if k in row and row[k].strip():
            return row[k].strip()
    return ""


def _get_date(row: dict[str, str]) -> str:
    for k in (
        "date",
        "Date",
        "posted",
        "Posted",
        "transaction_date",
        "Transaction Date",
    ):
        if k in row and row[k].strip():
            return row[k].strip()
    return ""


def _redact(s: str) -> str:
    if not s:
        return s
    if len(s) <= 6:
        return "***"
    return s[:3] + "***" + s[-2:]


def _generate_queue_card(
    domain: str,
    action: str,
    priority: str,
    desc: str,
    amount: float,
    date_s: str,
    risk: str,
    evidence: str,
) -> str:
    # [DOMAIN][ACTION][PRIORITY] Summary | Due: __ | Missing: __ | Next: __ | Evidence: __
    summary = f"{desc} ({amount})"
    card = f"[{domain}][{action}][{priority}] {summary} | Due: {date_s} | Missing: | Next: | Evidence: {evidence}"
    return card


def label_csv_file(csv_path: Path, rules: Ruleset) -> dict[str, Any]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, str]] = [dict(r) for r in reader]

    labeled: list[dict[str, Any]] = []
    queued: list[dict[str, Any]] = []
    skipped = 0

    queue_md_lines = []

    for row in rows:
        amount = _parse_amount(row)
        if amount is None:
            skipped += 1
            continue

        desc = _get_desc(row)
        date_s = _get_date(row)

        domain = _pick_label(desc, rules.domains)
        action = _pick_label(desc, rules.actions)

        abs_amount = abs(amount)
        risk = "high" if abs_amount >= rules.high_risk_amount_usd else "normal"

        priority = rules.high_risk_priority if risk == "high" else rules.default_priority

        needs_review = (domain in rules.always_queue_labels) or (risk == "high")

        # Evidence: Financial CSVs utilize the source file itself as primary evidence.
        # IEP/External evidence linking is decoupled to avoid cross-contamination.
        evidence = f"Source: {csv_path.name}"

        item = {
            "date": date_s,
            "amount": amount,
            "currency": rules.currency,
            "domain": domain,
            "action": action,
            "priority": priority,
            "risk": risk,
            "description": desc,
            "source_file": str(csv_path.as_posix()),
            "evidence": evidence,
        }

        queue_card = _generate_queue_card(
            domain, action, priority, desc, amount, date_s, risk, evidence
        )
        item["queue_card"] = queue_card

        labeled.append(item)
        if needs_review:
            queued.append(item)
            queue_md_lines.append(f"- {queue_card}")

    counts: dict[str, int] = {}
    for x in labeled:
        counts[x["domain"]] = counts.get(x["domain"], 0) + 1

    return {
        "file": str(csv_path.as_posix()),
        "total_rows": len(rows),
        "skipped_rows": skipped,
        "labeled_rows": len(labeled),
        "domain_counts": counts,
        "queue_size": len(queued),
        "labeled": labeled,
        "queue": queued,
        "queue_md": "\n".join(queue_md_lines),
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
    ap.add_argument(
        "--lock-env",
        default="AFO_FIN_ENABLED",
        help="Env var required to run (value must be '1')",
    )
    ns = ap.parse_args(argv)

    lock_env = str(ns.lock_env)
    if os.getenv(lock_env, "0") != "1":
        print(
            f"[LOCKED] {lock_env}!=1 (default OFF). Set {lock_env}=1 to run.",
            file=sys.stderr,
        )
        return 3

    # Assuming we run from root usually, but let's be safe
    root_dir = Path.cwd()
    rules = _load_rules(Path(ns.rules), root_dir)
    inp = Path(ns.inp)
    out_dir = Path(ns.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    outputs: list[Path] = []

    queue_report_md = out_dir / f"queue_report.{run_id}.md"
    all_queues = []

    processed = 0
    for csv_path in _iter_csv_inputs(inp):
        processed += 1
        report = label_csv_file(csv_path, rules)
        safe_name = csv_path.stem.replace(" ", "_")
        out_path = out_dir / f"{safe_name}.report.{run_id}.json"
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs.append(out_path)

        if report["queue_md"]:
            all_queues.append(f"### {csv_path.name}\n{report['queue_md']}")

    if processed == 0:
        print("[WARN] No CSV files found.", file=sys.stderr)
        return 2

    # Write MD Queue Report
    if all_queues:
        md_content = f"# Julie CPA Queue Report ({run_id})\n\n" + "\n\n".join(all_queues)
        queue_report_md.write_text(md_content, encoding="utf-8")
        print(f"[INFO] Queue Report: {queue_report_md}")

    index = {
        "run_id": run_id,
        "reports": [p.as_posix() for p in outputs],
        "queue_md": str(queue_report_md.as_posix()),
    }

    if processed == 0:
        print("[WARN] No CSV files found.", file=sys.stderr)
        return 2

    index = {"run_id": run_id, "reports": [p.as_posix() for p in outputs]}
    (out_dir / f"index.{run_id}.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(json.dumps(index, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
