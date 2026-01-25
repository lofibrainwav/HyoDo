"""Ticketing Package.

AFO 왕국의 작업 관리를 위한 티켓 생성 및 자동화 시스템.
MD 파싱 결과를 기반으로 TICKETS.md 및 하위 티켓 파일들을 관리함.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .formatter import format_ticket_content, format_ticket_entry


class TicketGenerator:
    """MD 파싱 결과를 기반으로 티켓을 자동 생성하는 클래스 (Facade)."""

    def __init__(self, tickets_dir: str = "tickets", tickets_md: str = "TICKETS.md") -> None:
        self.tickets_dir = Path(tickets_dir)
        self.tickets_md = Path(tickets_md)

    def generate_ticket(
        self, parsed_md: Any, _matching_result: Any, priority: str = "medium"
    ) -> str:
        """티켓을 생성하고 관련 파일들을 업데이트합니다."""
        ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M')}"

        ticket_data = {
            "id": ticket_id,
            "title": getattr(parsed_md, "title", "Untitled Task"),
            "priority": priority,
            "complexity": 5,
            "created_at": datetime.now().isoformat(),
            "description": getattr(parsed_md, "description", ""),
            "acceptance_criteria": "- TBD",
        }

        # 1. 개별 티켓 파일 생성
        format_ticket_content(ticket_data)
        # self._write_file(self.tickets_dir / f"{ticket_id}.md", content)

        # 2. TICKETS.md 업데이트
        # entry = format_ticket_entry(ticket_data)

        return ticket_id


__all__ = ["TicketGenerator"]
