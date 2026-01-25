from __future__ import annotations

import asyncio
from typing import Any

from rich.console import Console

from services.health_service import get_comprehensive_health

# Trinity Score: 95.0 (Verification Skill)
"""Skill: Verify Full Stack (眞)
시스템의 모든 구성요소(DB, Redis, API, Dashboard)를 검증하는 공식 스킬
"""


# AFO Core imports already loaded above

console = Console()


async def execute_skill(context: dict[str, Any] | None = None) -> dict[str, Any]:
    """[Skill Entry Point] 전체 시스템 상태 검증

    Args:
        context: 실행 컨텍스트 (옵션)

    Returns:
        검증 결과 리포트

    """
    console.print("[bold blue]🛡️ [Rule #1] Weapon Check: Verifying System Integrity...[/bold blue]")

    try:
        # 1. 종합 건강 검진 (Truth Check)
        health_data = await get_comprehensive_health()

        trinity_score = health_data.get("health_percentage", 0.0)
        details = health_data.get("organs", {})

        # 2. 결과 출력
        console.print(f"\n[bold green]⚖️ Trinity Score: {trinity_score}/100[/bold green]")

        for component, status in details.items():
            is_healthy = status.get("healthy") is True or status.get("status") == "healthy"
            icon = "✅" if is_healthy else "❌"
            console.print(f"{icon} {component}: {status.get('output', 'Unknown')}")

        return {
            "status": "success" if trinity_score > 80 else "warning",
            "trinity_score": trinity_score,
            "details": details,
        }

    except Exception as e:
        console.print(f"[bold red]❌ Skill Execution Failed: {e}[/bold red]")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # Independent Test Run
    asyncio.run(execute_skill())
