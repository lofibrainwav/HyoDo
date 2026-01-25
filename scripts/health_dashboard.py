#!/usr/bin/env python3
"""
AFO Kingdom 헬스 체크 대시보드
실시간 모니터링 및 메트릭 표시
"""

import asyncio
from datetime import datetime
from typing import Any, Dict

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from system_health_check import check_system_health

console = Console()


class HealthDashboard:
    """실시간 헬스 체크 대시보드"""

    def __init__(self) -> None:
        self.metrics_history = []
        self.last_update = None

    async def collect_metrics(self) -> Dict[str, Any]:
        """메트릭 수집"""
        try:
            result = await check_system_health()
            self.metrics_history.append({"timestamp": datetime.now(), "data": result})
            # 최근 100개만 유지
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]
            return result
        except Exception as e:
            return {"error": str(e)}

    def create_dashboard(self, data: Dict[str, Any]) -> Panel:
        """대시보드 생성"""
        if "error" in data:
            return Panel(f"❌ Error: {data['error']}", title="Health Dashboard")

        # 메인 메트릭 추출
        trinity_score = data.get("trinity_contribution", {})
        total_score = sum(trinity_score.values()) * 100

        ollama_health = data.get("ollama_health", {})
        connectivity = "✅" if ollama_health.get("ollama_connectivity") else "❌"
        performance = ollama_health.get("performance_ms", 0)

        # 테이블 생성
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")

        table.add_row("Trinity Score", f"{total_score:.1f}%", "✅" if total_score > 15 else "⚠️")
        table.add_row("Ollama 연결성", connectivity, "✅" if connectivity == "✅" else "❌")
        table.add_row("응답 시간", f"{performance:.1f}ms", "✅" if performance < 100 else "⚠️")
        table.add_row(
            "시스템 상태",
            data.get("overall_status", "unknown"),
            "✅" if data.get("overall_status") == "healthy" else "⚠️",
        )

        # 패널 생성
        title = f"AFO Kingdom Health Dashboard - {datetime.now().strftime('%H:%M:%S')}"
        return Panel(table, title=title, border_style="blue")

    async def run_dashboard(self):
        """대시보드 실행"""
        console.print("[bold green]🚀 AFO Kingdom 모니터링 대시보드 시작[/bold green]")
        console.print("실시간 헬스 체크 모니터링 중... (Ctrl+C로 종료)\n")

        try:
            with Live(console=console, refresh_per_second=1) as live:
                while True:
                    data = await self.collect_metrics()
                    dashboard = self.create_dashboard(data)
                    live.update(dashboard)
                    await asyncio.sleep(5)  # 5초마다 업데이트

        except KeyboardInterrupt:
            console.print("\n[bold yellow]📊 최종 메트릭 요약:[/bold yellow]")

            # 히스토리 분석
            if self.metrics_history:
                total_checks = len(self.metrics_history)
                healthy_checks = sum(
                    1 for h in self.metrics_history if h["data"].get("overall_status") == "healthy"
                )
                avg_performance = (
                    sum(
                        h["data"].get("ollama_health", {}).get("performance_ms", 0)
                        for h in self.metrics_history
                    )
                    / total_checks
                )

                console.print(f"총 체크 수: {total_checks}")
                console.print(
                    f"정상 상태: {healthy_checks}/{total_checks} ({healthy_checks / total_checks * 100:.1f}%)"
                )
                console.print(f"평균 응답 시간: {avg_performance:.1f}ms")

            console.print("[bold green]✅ 모니터링 대시보드 종료[/bold green]")


if __name__ == "__main__":
    dashboard = HealthDashboard()
    asyncio.run(dashboard.run_dashboard())
