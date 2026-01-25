import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

REQ = {
    "T25": {
        "required_files": [
            "health_body.json",
            "skills_body.json",
            "docker_ps.txt",
            "bandit_exitcode.txt",
            "bandit_summary.txt",
        ],
        "json_files": ["health_body.json", "skills_body.json"],
        "done_requires": {"bandit_exitcode": 0},
    },
    "T26": {
        "required_files": [
            "docker_ps.txt",
            "dashboard_headers.txt",
            "julie_dashboard_headers.txt",
            "julie_dashboard_body.json",
            "approve_options_headers.txt",
        ],
        "json_files": ["julie_dashboard_body.json"],
        "done_requires": {},
    },
}

AUTO_BEGIN = "<!--AUTO:BEGIN-->"
AUTO_END = "<!--AUTO:END-->"


def sh(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_report(report: Path) -> dict:
    txt = report.read_text(encoding="utf-8")

    def get_line(prefix: str) -> str:
        m = re.search(rf"^{re.escape(prefix)}\s*(.*)$", txt, flags=re.MULTILINE)
        return m.group(1).strip() if m else ""

    status = get_line("Status:")
    ts = get_line("Capture Timestamp:")
    ev = get_line("Evidence Directory:")
    return {"status": status, "ts": ts, "evidence": ev, "text": txt}


def write_report_header(report: Path, status: str, ts: str, evidence: str) -> None:
    lines = report.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        if line.startswith("Status:"):
            out.append(f"Status: {status}")
        elif line.startswith("Capture Timestamp:"):
            out.append(f"Capture Timestamp: {ts}")
        elif line.startswith("Evidence Directory:"):
            out.append(f"Evidence Directory: {evidence}")
        else:
            out.append(line)
    report.write_text("\n".join(out) + "\n", encoding="utf-8")


def replace_auto(report: Path, auto: str) -> None:
    txt = report.read_text(encoding="utf-8")
    a = txt.find(AUTO_BEGIN)
    b = txt.find(AUTO_END)
    if a == -1 or b == -1 or b < a:
        return
    new_txt = txt[: a + len(AUTO_BEGIN)] + "\n\n" + auto + "\n\n" + txt[b:]
    report.write_text(new_txt, encoding="utf-8")


def seal(ticket: str, slug: str, ts: str) -> None:
    ticket = ticket.upper().strip()
    slug = re.sub(r"[^A-Z0-9_]", "", slug.upper().replace("-", "_").replace(" ", "_"))
    if ticket not in REQ:
        raise SystemExit(f"Unknown ticket {ticket}. Add to REQ map first.")

    report = Path(f"docs/reports/{ticket}_{slug}_SSOT.md")
    if not report.exists():
        raise SystemExit(f"Missing report: {report}")

    ev_dir = Path(f"artifacts/{ticket.lower().replace('t', 't')}/{ts}")
    if not ev_dir.exists():
        raise SystemExit(f"Missing evidence dir: {ev_dir}")

    req = REQ[ticket]
    missing = []
    for f in req["required_files"]:
        if not (ev_dir / f).exists():
            missing.append(f)

    json_ok = {}
    for jf in req["json_files"]:
        p = ev_dir / jf
        try:
            json.loads(p.read_text(encoding="utf-8"))
            json_ok[jf] = True
        except Exception:
            json_ok[jf] = False

    bandit_exit = None
    if (ev_dir / "bandit_exitcode.txt").exists():
        try:
            bandit_exit = int((ev_dir / "bandit_exitcode.txt").read_text().strip())
        except Exception:
            bandit_exit = 999

    functional_green = (len(missing) == 0) and all(json_ok.values())

    status = "UNVERIFIED"
    if functional_green:
        status = "SEALED (Functional Green)"
    if functional_green and ticket == "T25" and bandit_exit is not None and bandit_exit != 0:
        status = "SEALED (Functional Green) / BLOCKED-SECURITY (Bandit exit != 0)"

    done = False
    if functional_green:
        if ticket == "T25":
            done = bandit_exit == 0
        else:
            done = True
    if done:
        status = "DONE"

    files_meta = []
    for p in sorted(ev_dir.glob("*")):
        if p.is_file():
            files_meta.append(
                {
                    "name": p.name,
                    "bytes": p.stat().st_size,
                    "sha256": (sha256_file(p) if p.stat().st_size <= 25_000_000 else None),
                }
            )

    seal_json = {
        "ticket": ticket,
        "slug": slug,
        "timestamp": ts,
        "evidence_dir": ev_dir.as_posix(),
        "status": status,
        "missing_files": missing,
        "json_parse_ok": json_ok,
        "bandit_exitcode": bandit_exit,
        "files": files_meta,
    }

    (ev_dir / "seal.json").write_text(json.dumps(seal_json, indent=2), encoding="utf-8")

    auto = "\n".join(
        [
            "## AUTO Summary",
            f"- Ticket: {ticket}",
            f"- Slug: {slug}",
            f"- Capture Timestamp: {ts}",
            f"- Evidence Directory: {ev_dir.as_posix()}",
            f"- Status: {status}",
            "",
            "### Missing files",
            "- (none)" if not missing else "\n".join([f"- {m}" for m in missing]),
            "",
            "### JSON parse",
            "\n".join([f"- {k}: {v}" for k, v in json_ok.items()]),
            "",
            "### Bandit",
            (f"- exitcode: {bandit_exit}" if bandit_exit is not None else "- not provided"),
            "",
            "### Seal",
            f"- seal.json: {(ev_dir / 'seal.json').as_posix()}",
        ]
    )

    replace_auto(report, auto)
    write_report_header(report, status=status, ts=ts, evidence=ev_dir.as_posix())

    print(f"SEALED_REPORT={report}")
    print(f"EVIDENCE_DIR={ev_dir}")
    print(f"SEAL={ev_dir / 'seal.json'}")
    print(f"STATUS={status}")


def gate() -> None:
    # 1) staged changed files
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"], text=True
    ).splitlines()
    reports = [Path(p) for p in out if p.startswith("docs/reports/") and p.endswith("_SSOT.md")]

    # 2) forbid docs outside docs/reports in staged additions
    ns = subprocess.check_output(
        ["git", "diff", "--cached", "--name-status"], text=True
    ).splitlines()
    for line in ns:
        parts = line.split()
        if len(parts) >= 2 and parts[0].startswith("A"):
            p = parts[1]
            if p.startswith("docs/") and not p.startswith("docs/reports/"):
                print(f"BLOCK: new docs file outside docs/reports/: {p}")
                return 1
            if p.startswith("artifacts/") and not re.match(r"^artifacts/t\d+/", p):
                print(f"BLOCK: artifacts must be under artifacts/tXX/: {p}")
                return 1

    # 3) strict truth: if report Status says SEALED/DONE, require seal.json matches
    for r in reports:
        info = parse_report(r)
        status = info["status"]
        ts = info["ts"]
        ev = info["evidence"]
        if status.startswith("SEALED") or status == "DONE":
            if not ts or not ev:
                print(f"BLOCK: {r} missing Capture Timestamp/Evidence Directory")
                return 1
            ev_dir = Path(ev)
            if not ev_dir.exists():
                print(f"BLOCK: evidence dir missing for {r}: {ev_dir}")
                return 1
            sealp = ev_dir / "seal.json"
            if not sealp.exists():
                print(f"BLOCK: seal.json missing for {r}: {sealp}")
                return 1
            sealj = json.loads(sealp.read_text(encoding="utf-8"))
            if sealj.get("status") != status:
                print(f"BLOCK: report Status != seal.json Status for {r}")
                print(f"  report={status}")
                print(f"  seal={sealp} status={sealj.get('status')}")
                return 1
            if sealj.get("timestamp") != ts:
                print(f"BLOCK: report ts != seal.json ts for {r}")
                return 1
            if sealj.get("evidence_dir") != ev_dir.as_posix():
                print(f"BLOCK: report evidence_dir != seal.json evidence_dir for {r}")
                return 1
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_seal = sub.add_parser("seal")
    ap_seal.add_argument("ticket")
    ap_seal.add_argument("slug")
    ap_seal.add_argument("--ts", required=True)

    sub.add_parser("gate")

    args = ap.parse_args()
    if args.cmd == "seal":
        seal(args.ticket, args.slug, args.ts)
    else:
        raise SystemExit(gate())


if __name__ == "__main__":
    main()
