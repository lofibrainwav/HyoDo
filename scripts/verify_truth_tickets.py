#!/usr/bin/env python3
"""
📜 AFO Kingdom Audit Script - Tickets & Phases (Truth)
"""

import re
from pathlib import Path


def audit_tickets() -> None:
    tickets_path = Path("TICKETS.md")
    evolog_path = Path("AFO_EVOLUTION_LOG.md")

    if not tickets_path.exists() or not evolog_path.exists():
        print("❌ Critical Documents Missing!")
        return False

    tickets_content = tickets_path.read_text(encoding="utf-8")
    evolog_content = evolog_path.read_text(encoding="utf-8")

    # Extract Phases from TICKETS.md (Robust Regex)
    ticket_phases = re.findall(r"#{2,3}\s*(?:🚀)?\s*Phase\s*(\d+):", tickets_content)

    # Extract Phases from AFO_EVOLUTION_LOG.md (Robust Regex)
    log_phases = re.findall(r"#{2,3}\s*(?:🚀)?\s*Phase\s*(\d+):", evolog_content)

    print(f"📊 Tickets Phases: {sorted(set(ticket_phases))}")
    print(f"📊 Log Phases: {sorted(set(log_phases))}")

    missing_in_log = set(ticket_phases) - set(log_phases)
    missing_in_tickets = set(log_phases) - set(ticket_phases)

    if missing_in_log:
        print(f"⚠️  Phases in TICKETS but missing in LOG: {sorted(missing_in_log)}")
    if missing_in_tickets:
        print(f"⚠️  Phases in LOG but missing in TICKETS: {sorted(missing_in_tickets)}")

    return not (missing_in_log or missing_in_tickets)


if __name__ == "__main__":
    audit_tickets()
