from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

# Trinity Score: 95.0 (Robust Parsing)
"""
AFO Ticket Manager Domain Service (domain/tickets/manager.py)

Centralized management and parsing of TICKETS.md.
Provides truth (眞) about the Kingdom's work state.
Handles mixed Markdown formats (Header/List styles) and various header levels.
"""


class Ticket(BaseModel):
    id: str
    title: str
    priority: str = "Unknown"
    status: str = "Unknown"
    phase: str | None = None
    description: str | None = None
    line_number: int | None = None


class PhaseBlock(BaseModel):
    name: str
    status: str
    tickets: list[Ticket] = []


class TicketManager:
    """
    Manages the lifecycle and state of TICKETS.md
    """

    def __init__(self, tickets_path: Path | str | None = None) -> None:
        if tickets_path:
            self.filepath = Path(tickets_path)
        else:
            # Default to repo root TICKETS.md assumption
            repo_root = Path(__file__).resolve().parents[3]
            self.filepath = repo_root / "TICKETS.md"

    def _read_content(self) -> list[str]:
        if not self.filepath.exists():
            return []
        return self.filepath.read_text(encoding="utf-8").splitlines()

    def get_all_tickets(self) -> list[Ticket]:
        """Parses TICKETS.md and returns all tickets."""
        lines = self._read_content()
        tickets: list[Ticket] = []
        current_phase = "Unknown"

        i = 0
        while i < len(lines):
            line = lines[i]

            # 1. Update Phase context
            phase = self._parse_phase(line)
            if phase:
                current_phase = phase
                i += 1
                continue

            # 2. Check for Header Format
            ticket, next_i = self._parse_header_style_ticket(lines, i, current_phase)
            if ticket:
                tickets.append(ticket)
                i = next_i
                continue

            # 3. Check for List Format
            ticket, next_i = self._parse_list_style_ticket(lines, i, current_phase)
            if ticket:
                tickets.append(ticket)
                i = next_i
                continue

            i += 1

        return tickets

    def _parse_phase(self, line: str) -> str | None:
        """Attempts to parse a phase header from the line."""
        # Phase Pattern: Allow ## or ###, optional emoji, capture "Phase X: Title"
        match = re.search(r"^#{2,3} (?:🚀 )?(Phase \d+(?::.*)?)", line)
        return match.group(1).strip() if match else None

    def _parse_header_style_ticket(
        self, lines: list[str], index: int, phase: str
    ) -> tuple[Ticket | None, int]:
        """Parses a header-style ticket starting at index."""
        line = lines[index]
        match = re.search(r"^#{3,4} TICKET-(\d+): (.*)", line)
        if not match:
            return None, index

        ticket_id = match.group(1)
        title = match.group(2).strip()
        status = "Open"
        priority = "Normal"

        # Scan metadata
        j = index + 1
        while j < len(lines):
            subline = lines[j].strip()
            if subline.startswith("#"):
                break

            s_val = self._extract_metadata(
                subline, ["**상태**:", "**Status**:", "- **상태**:", "- **Status**:"]
            )
            if s_val:
                status = self._normalize_status(s_val)

            p_val = self._extract_metadata(
                subline, ["**우선순위**:", "**Priority**:", "- **우선순위**:", "- **Priority**:"]
            )
            if p_val:
                priority = self._normalize_priority(p_val)

            j += 1

        return Ticket(
            id=ticket_id,
            title=title,
            phase=phase,
            status=status,
            priority=priority,
            line_number=index + 1,
        ), j

    def _parse_list_style_ticket(
        self, lines: list[str], index: int, phase: str
    ) -> tuple[Ticket | None, int]:
        """Parses a list-style ticket starting at index."""
        line = lines[index]
        match = re.search(r"^\s*- \*\*TICKET-(\d+)\*\*: (.*)", line)
        if not match:
            return None, index

        ticket_id = match.group(1)
        raw_title = match.group(2).strip()
        status = "Open"
        priority = "Normal"

        # Inline status check
        if "✅" in raw_title or "Completed" in raw_title:
            status = "Completed"
            title = (
                raw_title.replace("(✅)", "").replace("✅", "").replace("(Completed)", "").strip()
            )
        else:
            title = raw_title

        # Scan indented metadata
        j = index + 1
        while j < len(lines):
            subline = lines[j]
            if not subline.strip():
                j += 1
                continue
            if not subline.startswith(" ") and not subline.startswith("\t"):
                break

            clean_sub = subline.strip()
            # Limited metadata support for list style (as per original logic)
            if clean_sub.startswith("- **상태**:") or clean_sub.startswith("- **Status**:"):
                val = clean_sub.split(":", 1)[1].strip()
                if "✅" in val:
                    status = "Completed"
            j += 1

        # Original logic incremented i by 1 for list items mostly, but returning j allows skipping if we parsed metadata
        # However, to maintain exact behavior of original loop which was `i += 1` at the end or `continue` (which implies loop),
        # The list parser logic had `i += 1` effectively.
        # Let's return j-1 so that the main loop's `i = next_i` sets it correctly?
        # Actually logic was: `tickets.append(...)` then `i += 1` then `continue`.
        # So we should return j if we consumed lines, or just index + 1?
        # The original code scanned `j` to find metadata but didn't advance main `i` to `j`. It just did `i += 1`.
        # Wait, the original code had `i += 1` after appending. It did NOT set `i = j`.
        # This means list style tickets are assumed to be 1 line or effectively 1 line + metadata that doesn't contain other tickets.
        # Safest is to return index + 1 to be safe, BUT if metadata is multi-line we might want to skip it.
        # Let's replicate original logic: `i += 1` was used.
        return Ticket(
            id=ticket_id,
            title=title,
            phase=phase,
            status=status,
            priority=priority,
            line_number=index + 1,
        ), index + 1

    def _extract_metadata(self, line: str, prefixes: list[str]) -> str | None:
        for p in prefixes:
            if line.startswith(p):
                return line.split(":", 1)[1].strip()
        return None

    def _normalize_status(self, val: str) -> str:
        if "✅" in val or "Completed" in val:
            return "Completed"
        if "🔄" in val or "In Progress" in val:
            return "In Progress"
        if "📝" in val or "Open" in val:
            return "Open"
        if "❌" in val or "Cancelled" in val:
            return "Cancelled"
        return val

    def _normalize_priority(self, val: str) -> str:
        if "🔴" in val or "Critical" in val:
            return "Critical"
        if "🟡" in val or "Major" in val:
            return "Major"
        if "🟢" in val or "Minor" in val:
            return "Minor"
        return val

    def get_statistics(self) -> dict[str, Any]:
        """Returns statistics about tickets."""
        tickets = self.get_all_tickets()
        stats = {
            "total": len(tickets),
            "open": len([t for t in tickets if t.status == "Open"]),
            "in_progress": len([t for t in tickets if t.status == "In Progress"]),
            "completed": len([t for t in tickets if t.status == "Completed"]),
            "critical": len([t for t in tickets if t.priority == "Critical"]),
        }
        return stats
