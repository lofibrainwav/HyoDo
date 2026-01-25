#!/usr/bin/env python3
"""
TICKET-059: Phase 36 자율 진화 - 자동 모니터링 시스템
Council of Minds가 스스로 왕국 상태를 진단하고 티켓을 발행하는 완전 자동화 루프

기능:
- Cron 기반 주기적 건강 진단
- Trinity Score 모니터링
- 이상 징후 자동 감지
- 자동 티켓 발행 (TICKET-064)
"""

import asyncio
import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import redis
from pydantic import BaseModel, Field

# aiofiles는 optional import (테스트 환경에서 없을 수 있음)
try:
    import aiofiles

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

from .types import (
    CouncilAnalysis,
    HealthMetrics,
    MonitoringCycleResult,
    StrategyAnalysis,
)

logger = logging.getLogger(__name__)

# 왕국 내부 모듈
try:
    # Use council_graph from multi_agent router
    from AFO.api.routers.multi_agent import council_graph
    from AFO.auto_ticket_generator import AutoTicketGenerator
    from AFO.config.settings import get_settings
    from AFO.health.monitor import HealthMonitor
    from services.trinity_calculator import trinity_calculator

    class ChancellorGraph:
        """Wrapper for Council Graph"""

        async def analyze_health(self, metrics: dict[str, Any]) -> dict[str, Any]:
            # Simulate an analysis task for the council
            task = f"Analyze System Health: {json.dumps(metrics)}"
            state = await council_graph.ainvoke(
                {
                    "task": task,
                    "context": {"source": "auto_monitor"},
                    "truth_output": {},
                    "goodness_output": {},
                    "beauty_output": {},
                    "consensus_output": {},
                    "trinity_score": 0.0,
                    "final_decision": "",
                    "errors": [],
                    "start_time": time.time(),
                    "task_id": "health_check",
                }
            )
            return {"analysis": state["final_decision"], "trinity_score": state["trinity_score"]}

    def calculate_trinity_score() -> None:
        return trinity_calculator.calculate_trinity_score(
            [1.0, 1.0, 1.0, 1.0, 1.0]
        )  # Default perfect score for check

except ImportError as e:
    logger.warning(f"AFO modules not fully found: {e}. Using mocks.")

    class ChancellorGraph:
        async def analyze_health(self, metrics: dict[str, Any]) -> dict[str, Any]:
            return {"analysis": "Mock analysis", "issues": [], "recommendations": []}

    class HealthMonitor:
        async def get_comprehensive_health(self) -> dict[str, Any]:
            return {"trinity": {"score": 85.0}, "organs": {}, "status": "healthy"}

    class AutoTicketGenerator:
        def generate_ticket_from_issue(self, issue_data: dict[str, Any]) -> str | None:
            return f"TICKET-064-{int(time.time())}"

    def calculate_trinity_score() -> float:
        return 85.0

    class Settings:
        REDIS_HOST = "localhost"
        REDIS_PORT = 6379
        PROJECT_ROOT = Path(os.getcwd())
        AUTO_MONITOR_INTERVAL = 3600  # 1시간
        HEALTH_CHECK_TIMEOUT = 30

    def get_settings() -> None:
        return Settings()


settings = get_settings()


class HealthIssue(BaseModel):
    """건강 이슈 모델"""

    issue_id: str = Field(..., description="고유 식별자")
    category: str = Field(..., description="문제 카테고리")
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    title: str
    description: str
    trinity_impact: float = Field(..., ge=0.0, le=1.0)
    affected_components: list[str] = []
    recommended_actions: list[str] = []
    detected_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    council_analysis: dict[str, Any] = Field(default_factory=dict)


class AutoMonitor:
    """Phase 36 자율 진화 - 자동 모니터링 코어"""

    def __init__(self) -> None:
        self.chancellor = ChancellorGraph()
        self.health_monitor = HealthMonitor()
        self.ticket_generator = AutoTicketGenerator()
        self.redis = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True
        )

        # 모니터링 상태 저장소
        self.monitoring_dir = Path(settings.BASE_DIR) / "data" / "monitoring"
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)

        self.last_health_check = None
        self.monitoring_active = False

    async def _get_current_health_metrics(self) -> HealthMetrics:
        """현재 왕국 건강 메트릭 수집"""
        try:
            health_data = await self.health_monitor.get_comprehensive_health()

            # 추가 메트릭 수집
            additional_metrics = {
                "timestamp": datetime.now(UTC).isoformat(),
                "system_load": await self._get_system_load(),
                "memory_usage": await self._get_memory_usage(),
                "disk_usage": await self._get_disk_usage(),
                "network_status": await self._check_network_status(),
            }

            return {**health_data, **additional_metrics}

        except Exception as e:
            logger.error(f"Health metrics collection failed: {e}")
            return {"error": str(e), "timestamp": datetime.now(UTC).isoformat()}

    async def _get_system_load(self) -> float:
        """시스템 부하 측정"""
        try:
            # 간단한 시스템 부하 측정 (실제 구현에서는 psutil 등 사용)
            return 0.5  # Mock value
        except Exception:
            return 0.0

    async def _get_memory_usage(self) -> float:
        """메모리 사용률 측정"""
        try:
            return 0.6  # Mock value
        except Exception:
            return 0.0

    async def _get_disk_usage(self) -> float:
        """디스크 사용률 측정"""
        try:
            return 0.4  # Mock value
        except Exception:
            return 0.0

    async def _check_network_status(self) -> str:
        """네트워크 상태 확인"""
        try:
            return "healthy"  # Mock value
        except Exception:
            return "unknown"

    async def _analyze_health_with_council(self, metrics: HealthMetrics) -> CouncilAnalysis:
        """Council of Minds로 건강 상태 분석"""
        try:
            analysis = await self.chancellor.analyze_health(metrics)

            # 3책사별 분석 결과
            council_insights = {
                "truth_analysis": await self._analyze_with_truth(metrics),
                "goodness_analysis": await self._analyze_with_goodness(metrics),
                "beauty_analysis": await self._analyze_with_beauty(metrics),
            }

            return {
                **analysis,
                "council_insights": council_insights,
                "analyzed_at": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(f"Council analysis failed: {e}")
            return {"error": str(e), "council_insights": {}}

    async def _analyze_with_truth(self, metrics: HealthMetrics) -> StrategyAnalysis:
        """제갈량(眞): 기술적 정확성 분석"""
        trinity_score = metrics.get("trinity", {}).get("score", 0)

        issues = []
        if trinity_score < 80:
            issues.append("Trinity Score가 낮음 - 기술적 안정성 저하")
        if metrics.get("system_load", 0) > 0.8:
            issues.append("시스템 부하 과다 - 성능 저하 가능성")

        return {
            "technical_accuracy": 0.95,
            "issues_detected": issues,
            "recommendations": ["시스템 최적화 검토", "캐시 전략 재설계"],
        }

    async def _analyze_with_goodness(self, metrics: HealthMetrics) -> StrategyAnalysis:
        """사마의(善): 보안 및 안정성 분석"""
        health_status = metrics.get("status", "unknown")

        issues = []
        if health_status != "healthy":
            issues.append(f"건강 상태 이상: {health_status}")
        if metrics.get("memory_usage", 0) > 0.9:
            issues.append("메모리 사용률 비정상 - 메모리 누수 가능성")

        return {
            "security_score": 0.92,
            "issues_detected": issues,
            "recommendations": ["보안 감사 실시", "메모리 관리 최적화"],
        }

    async def _analyze_with_beauty(self, metrics: HealthMetrics) -> StrategyAnalysis:
        """주유(美): UX 및 성능 분석"""
        network_status = metrics.get("network_status", "unknown")

        issues = []
        if network_status != "healthy":
            issues.append(f"네트워크 상태 불안정: {network_status}")
        if metrics.get("disk_usage", 0) > 0.85:
            issues.append("디스크 공간 부족 - 성능 저하")

        return {
            "ux_score": 0.88,
            "issues_detected": issues,
            "recommendations": ["네트워크 최적화", "디스크 정리 및 관리"],
        }

    async def _detect_issues(self, analysis: CouncilAnalysis) -> list[HealthIssue]:
        """분석 결과에서 이슈 추출"""
        issues = []

        # Council 분석에서 이슈 추출
        for category, insights in analysis.get("council_insights", {}).items():
            for issue_desc in insights.get("issues_detected", []):
                severity = self._determine_severity(issue_desc)

                issue = HealthIssue(
                    issue_id=f"ISSUE-{int(time.time())}-{len(issues)}",
                    category=category.split("_")[0],  # truth, goodness, beauty
                    severity=severity,
                    title=issue_desc,
                    description=f"자동 진단에서 발견된 이슈: {issue_desc}",
                    trinity_impact=0.1,  # 기본 영향도
                    affected_components=["system"],
                    recommended_actions=insights.get("recommendations", []),
                    council_analysis=insights,
                )
                issues.append(issue)

        return issues

    def _determine_severity(self, issue_description: str) -> str:
        """이슈 설명으로 심각도 결정"""
        if any(word in issue_description.lower() for word in ["critical", "crash", "failure"]):
            return "critical"
        elif any(word in issue_description.lower() for word in ["high", "error", "exception"]):
            return "high"
        elif any(word in issue_description.lower() for word in ["warning", "low"]):
            return "low"
        else:
            return "medium"

    async def _generate_tickets_for_issues(self, issues: list[HealthIssue]) -> list[str]:
        """발견된 이슈에 대한 티켓 자동 생성"""
        ticket_ids = []

        for issue in issues:
            if issue.severity in ["critical", "high"]:
                try:
                    ticket_id = self.ticket_generator.generate_ticket_from_issue(
                        {
                            "title": f"[자율 진화] {issue.title}",
                            "description": issue.description,
                            "severity": issue.severity,
                            "category": issue.category,
                            "trinity_impact": issue.trinity_impact,
                            "recommendations": issue.recommended_actions,
                        }
                    )

                    if ticket_id:
                        ticket_ids.append(ticket_id)
                        logger.info(f"Auto-generated ticket: {ticket_id} for issue: {issue.title}")

                except Exception as e:
                    logger.error(f"Failed to generate ticket for issue {issue.issue_id}: {e}")

        return ticket_ids

    async def _save_monitoring_data(
        self,
        metrics: HealthMetrics,
        analysis: CouncilAnalysis,
        issues: list[HealthIssue],
        tickets: list[str],
    ) -> None:
        """모니터링 데이터 저장"""
        monitoring_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "metrics": metrics,
            "analysis": analysis,
            "issues": [issue.model_dump() for issue in issues],
            "generated_tickets": tickets,
            "cycle_duration": time.time() - (self.last_health_check or time.time()),
        }

        filename = f"monitoring_{int(time.time())}.json"
        filepath = self.monitoring_dir / filename

        try:
            if AIOFILES_AVAILABLE:
                async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(monitoring_data, indent=2, ensure_ascii=False))
            else:
                # Fallback to sync write
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(json.dumps(monitoring_data, indent=2, ensure_ascii=False))
            logger.info(f"Monitoring data saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save monitoring data: {e}")

    async def run_monitoring_cycle(self) -> MonitoringCycleResult:
        """단일 모니터링 사이클 실행"""
        logger.info("🚀 Starting autonomous monitoring cycle (Phase 36)")

        try:
            # 1. 건강 메트릭 수집
            metrics = await self._get_current_health_metrics()
            logger.info(
                f"📊 Health metrics collected: Trinity={metrics.get('trinity', {}).get('score', 'N/A')}"
            )

            # 2. Council 분석
            analysis = await self._analyze_health_with_council(metrics)
            logger.info(
                f"🎭 Council analysis completed: {len(analysis.get('council_insights', {}))} insights"
            )

            # 3. 이슈 감지
            issues = await self._detect_issues(analysis)
            logger.info(
                f"🔍 Issues detected: {len(issues)} ({sum(1 for i in issues if i.severity in ['critical', 'high'])} high/critical)"
            )

            # 4. 자동 티켓 발행
            tickets = await self._generate_tickets_for_issues(issues)
            logger.info(f"🎫 Tickets generated: {len(tickets)}")

            # 5. 모니터링 데이터 저장
            await self._save_monitoring_data(metrics, analysis, issues, tickets)

            self.last_health_check = time.time()

            result = {
                "success": True,
                "metrics": metrics,
                "issues_count": len(issues),
                "tickets_generated": len(tickets),
                "cycle_completed_at": datetime.now(UTC).isoformat(),
            }

            logger.info("✅ Autonomous monitoring cycle completed successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Monitoring cycle failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "cycle_failed_at": datetime.now(UTC).isoformat(),
            }

    async def start_continuous_monitoring(self):
        """지속적 모니터링 시작 (Cron 대체)"""
        logger.info("🔄 Starting continuous autonomous monitoring (Phase 36 자율 진화)")

        self.monitoring_active = True

        while self.monitoring_active:
            try:
                result = await self.run_monitoring_cycle()

                if result["success"]:
                    logger.info(
                        f"📈 Cycle result: {result['issues_count']} issues, {result['tickets_generated']} tickets"
                    )
                else:
                    logger.error(f"💥 Cycle failed: {result.get('error', 'Unknown error')}")

                # 다음 사이클까지 대기
                await asyncio.sleep(settings.AUTO_MONITOR_INTERVAL)

            except Exception as e:
                logger.error(f"💥 Continuous monitoring error: {e}")
                await asyncio.sleep(60)  # 에러 시 1분 대기 후 재시도

    def stop_monitoring(self) -> None:
        """모니터링 중지"""
        logger.info("🛑 Stopping autonomous monitoring")
        self.monitoring_active = False


# CLI 인터페이스
async def main():
    """CLI 진입점"""
    import argparse

    parser = argparse.ArgumentParser(description="Phase 36 - Autonomous Evolution Monitor")
    parser.add_argument("--once", action="store_true", help="Run single monitoring cycle")
    parser.add_argument("--continuous", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--interval", type=int, default=3600, help="Monitoring interval in seconds")

    args = parser.parse_args()

    monitor = AutoMonitor()

    if args.once:
        result = await monitor.run_monitoring_cycle()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.continuous:
        try:
            await monitor.start_continuous_monitoring()
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\nMonitoring stopped by user")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
