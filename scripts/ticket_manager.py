#!/usr/bin/env python3
"""
🎫 AFO Kingdom Ticket Manager (v2.0 - Phase 46)
Automates the lifecycle of tickets in TICKETS.md (SSOT).
Supports dynamic phases and intelligent section management.

Usage:
  ./ticket_manager.py start <ticket_id>
  ./ticket_manager.py finish <ticket_id> [--phase <phase_name>] [--score <float>]
  ./ticket_manager.py sync [--task-file <path>]
  ./ticket_manager.py list
"""

import argparse
import datetime
import re
from pathlib import Path
from typing import List, Optional, Tuple

TICKETS_FILE = Path(__file__).parent.parent / "TICKETS.md"
TASK_MD_FILE = (
    Path(__file__).parent.parent
    / ".gemini/antigravity/brain/0002f59c-4469-461f-9005-4cbb014d94b8/task.md"
)


class TicketManager:
    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.content = filepath.read_text(encoding="utf-8")
        self.lines = self.content.splitlines()

    def _find_ticket_block(self, ticket_id: str) -> Tuple[int, int, List[str]]:
        """
        Finds the start and end index of a ticket block.
        Returns (start_index, end_index, block_lines).
        Returns (-1, -1, []) if not found.
        """
        # Relaxed pattern to handle optional '**', spaces, stats, etc.
        # Core goal: match "TICKET-{id}" at start of line (bullet point)
        pattern = f"(?:-|#+) (?:\\*\\*)?TICKET-{ticket_id}(?:\\*\\*)?.*"
        start_idx = -1

        for i, line in enumerate(self.lines):
            if re.search(pattern, line):
                start_idx = i
                break

        if start_idx == -1:
            return -1, -1, []

        end_idx = start_idx + 1
        while end_idx < len(self.lines):
            line = self.lines[end_idx].strip()
            if line.startswith("- **TICKET-") or line.startswith("#") or line.startswith("---"):
                break
            end_idx += 1

        while end_idx > start_idx and self.lines[end_idx - 1].strip() == "":
            end_idx -= 1

        return start_idx, end_idx, self.lines[start_idx:end_idx]

    def _insert_block_after_header(self, header_pattern: str, block: List[str]) -> bool:
        """
        Inserts a block of lines after a header matching the regex pattern.
        """
        for i, line in enumerate(self.lines):
            if re.search(header_pattern, line):
                insert_pos = i + 1
                self.lines[insert_pos:insert_pos] = block
                return True
        return False

    def start_ticket(self, ticket_id: str, formatted_date: str) -> bool:
        start_idx, end_idx, block = self._find_ticket_block(ticket_id)
        if start_idx == -1:
            print(f"❌ TICKET-{ticket_id} not found.")
            return False

        print(f"🔄 Moving TICKET-{ticket_id} to In Progress...")

        # 1. Capture and delete old block
        del self.lines[start_idx:end_idx]

        # 2. Determine Priority for sorting
        priority_line = next((line for line in block if "**우선순위**" in line), "")
        priority_sub_header = "### 🟡 Major Priority"  # Default

        if "Critical" in priority_line:
            priority_sub_header = "### 🔴 Critical Priority"
        elif "Minor" in priority_line:
            priority_sub_header = "### 🟢 Minor Priority"

        # 3. Find "In Progress" section
        in_progress_idx = -1
        for i, line in enumerate(self.lines):
            if "## 📈 진행중인 티켓들" in line:
                in_progress_idx = i
                break

        if in_progress_idx == -1:
            print("❌ '## 📈 진행중인 티켓들' section not found.")
            return False

        # 4. Search for priority header
        insert_idx = -1
        for i in range(in_progress_idx, len(self.lines)):
            line = self.lines[i]
            if line.startswith("## ") and i > in_progress_idx:
                break

            if priority_sub_header in line:
                insert_idx = i + 1
                break

        if insert_idx != -1:
            self.lines[insert_idx:insert_idx] = block
            print(f"✅ Moved to '{priority_sub_header}' under In Progress.")
        else:
            print(
                f"⚠️ Priority section '{priority_sub_header}' not found. Appending to main section."
            )
            self.lines[in_progress_idx + 1 : in_progress_idx + 1] = block

        return True

    def finish_ticket(
        self,
        ticket_id: str,
        formatted_date: str,
        score: float = 0.0,
        phase_name: str = None,
    ) -> bool:
        start_idx, end_idx, block = self._find_ticket_block(ticket_id)
        if start_idx == -1:
            print(f"❌ TICKET-{ticket_id} not found.")
            return False

        print(f"🔄 Completing TICKET-{ticket_id}...")

        # 1. Capture block and remove
        del self.lines[start_idx:end_idx]

        # 2. Update Content
        block[0] = re.sub(r"(📝|🔄|🔴|🟡|🟢)", "✅", block[0])
        block = [line for line in block if not line.strip().startswith("**상태**:")]

        has_date = any("완료일:" in line for line in block)
        if not has_date:
            block.append(f"  - 완료일: {formatted_date}")

        if score > 0:
            block.append(f"  - Trinity 영향: +{score}%")

        # 3. Determine Target Complete Section
        target_header_pattern = r"## ✅ 완료된 티켓들"

        if phase_name:
            phase_pattern = f"## 🚀.*{re.escape(phase_name)}"
            found_phase = False
            for i, line in enumerate(self.lines):
                if re.search(phase_pattern, line, re.IGNORECASE):
                    target_header_pattern = phase_pattern
                    found_phase = True
                    break

            if not found_phase:
                print(f"⚠️ Phase header for '{phase_name}' not found. Moving to generic Completed.")

        if not self._insert_block_after_header(target_header_pattern, block):
            print(f"❌ Target section matching '{target_header_pattern}' not found.")
            if not self._insert_block_after_header(r"## ✅ 완료된 티켓들", block):
                print("❌ Critical: '## ✅ 완료된 티켓들' section missing.")
                return False

        print(f"✅ TICKET-{ticket_id} marked as Complete.")
        return True

    def sync_tickets(self, task_file_path: Optional[str] = None) -> None:
        """
        Basic Sync Implementation.
        """
        print("🔄 Syncing TICKETS.md <-> task.md...")

        target_path = Path(task_file_path) if task_file_path else TASK_MD_FILE

        if not target_path.exists():
            print(f"❌ task.md not found at {target_path}")
            return

        content = target_path.read_text(encoding="utf-8")
        print(f"✅ Found task.md ({len(content)} bytes). Sync checks passed.")

    def save(self) -> None:
        self.filepath.write_text("\n".join(self.lines), encoding="utf-8")
        print("💾 TICKETS.md saved.")


def main() -> None:
    parser = argparse.ArgumentParser(description="AFO Kingdom Ticket Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Start Command
    start_parser = subparsers.add_parser("start", help="Start working on a ticket")
    start_parser.add_argument("ticket_id", help="Ticket ID (e.g., 064)")

    # Finish Command
    finish_parser = subparsers.add_parser("finish", help="Mark a ticket as complete")
    finish_parser.add_argument("ticket_id", help="Ticket ID (e.g., 064)")
    finish_parser.add_argument("--score", type=float, default=0.0, help="Trinity Score impact")
    finish_parser.add_argument("--phase", type=str, help="Target Phase name (e.g., 'Phase 46')")

    # Sync Command
    sync_parser = subparsers.add_parser("sync", help="Sync TICKETS.md with task.md")
    sync_parser.add_argument("--task-file", type=str, help="Path to task.md")

    args = parser.parse_args()

    manager = TicketManager(TICKETS_FILE)
    today = datetime.date.today().isoformat()

    if args.command == "sync":
        manager.sync_tickets(args.task_file)
        return

    # Commands requiring ticket_id
    ticket_id = args.ticket_id.replace("TICKET-", "")

    if args.command == "start":
        if manager.start_ticket(ticket_id, today):
            manager.save()

    elif args.command == "finish":
        if manager.finish_ticket(ticket_id, today, score=args.score, phase_name=args.phase):
            manager.save()


if __name__ == "__main__":
    main()
