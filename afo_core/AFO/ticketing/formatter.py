"""Ticket Formatter.

티켓 파일 내용 및 TICKETS.md 엔트리 포맷팅 로직.
"""

from __future__ import annotations

from typing import Any


def format_ticket_content(data: dict[str, Any]) -> str:
    """티켓 본문 마크다운 내용을 포맷팅합니다."""
    return f"""# [{data["id"]}] {data["title"]}

## Metadata
- Priority: {data["priority"]}
- Complexity: {data["complexity"]}
- Created: {data["created_at"]}

## Description
{data["description"]}

## Acceptance Criteria
{data["acceptance_criteria"]}
"""


def format_ticket_entry(data: dict[str, Any]) -> str:
    """TICKETS.md에 추가할 요약 엔트리를 포맷팅합니다."""
    return (
        f"| {data['id']} | {data['title']} | {data['priority']} | [Link](tickets/{data['id']}.md) |"
    )
