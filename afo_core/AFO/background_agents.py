"""
🎯 AFO Kingdom Background Agents 생태계 (Phase 79)

지속적 작업 지원 및 실시간 모니터링 강화 시스템
Trinity Score 기반 동적 리소스 할당 및 자동 최적화

작성자: 승상 (Chancellor)
날짜: 2026-01-22
"""

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentStatus:
    """에이전트 상태 데이터 클래스"""

    agent_id: str
    status: str  # 'idle', 'running', 'paused', 'error'
    last_activity: float
    performance_score: float
    resource_usage: dict[str, float]
    error_count: int


class BackgroundAgent(ABC):
    """Background Agent 기본 추상 클래스"""

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.status = AgentStatus(
            agent_id=agent_id,
            status="idle",
            last_activity=time.time(),
            performance_score=0.0,
            resource_usage={"cpu": 0.0, "memory": 0.0},
            error_count=0,
        )
        self.is_running = False
        self.task: asyncio.Task | None = None
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

    @abstractmethod
    async def execute_cycle(self) -> None:
        """각 에이전트의 주요 실행 로직"""
        pass

    @abstractmethod
    async def get_metrics(self) -> dict[str, Any]:
        """에이전트 성능 메트릭 반환"""
        pass

    async def start_background_task(self) -> None:
        """백그라운드 작업 시작"""
        if self.is_running:
            self.logger.warning(f"{self.name} already running")
            return

        self.is_running = True
        self.status.status = "running"
        self.logger.info(f"🚀 Starting {self.name} background agent")

        try:
            while self.is_running:
                time.time()

                try:
                    await self.execute_cycle()
                    self.status.performance_score = min(100.0, self.status.performance_score + 1)
                except Exception as e:
                    self.status.error_count += 1
                    self.status.performance_score = max(0.0, self.status.performance_score - 5)
                    self.logger.error(f"❌ {self.name} error: {e!s}")

                # 리소스 사용량 시뮬레이션 (실제로는 psutil 등으로 측정)
                self.status.resource_usage["cpu"] = random.uniform(1, 15)
                self.status.resource_usage["memory"] = random.uniform(50, 200)
                self.status.last_activity = time.time()

                # 실행 주기 조정 (30초)
                await asyncio.sleep(30)

        except asyncio.CancelledError:
            self.logger.info(f"🛑 {self.name} cancelled")
        finally:
            self.status.status = "idle"
            self.is_running = False

    async def stop_background_task(self) -> None:
        """백그라운드 작업 중지"""
        self.is_running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.logger.info(f"🛑 Stopped {self.name} background agent")

    async def pause_background_task(self) -> None:
        """백그라운드 작업 일시 중지"""
        self.status.status = "paused"
        self.logger.info(f"⏸️ Paused {self.name} background agent")

    async def resume_background_task(self) -> None:
        """백그라운드 작업 재개"""
        self.status.status = "running"
        self.logger.info(f"▶️ Resumed {self.name} background agent")


class HealthMonitorAgent(BackgroundAgent):
    """실시간 Trinity Score 모니터링 에이전트"""

    def __init__(self):
        super().__init__("health_monitor", "Health Monitor Agent")
        self.trinity_history: list[float] = []
        self.alert_threshold = 70.0
        self.alerts_sent = 0

    async def execute_cycle(self) -> None:
        # Trinity Score 모니터링 (실제로는 계산 엔진에서 가져옴)
        current_trinity = random.uniform(60, 100)
        self.trinity_history.append(current_trinity)

        # 최근 10개 평균 계산
        if len(self.trinity_history) > 10:
            self.trinity_history = self.trinity_history[-10:]

        avg_trinity = sum(self.trinity_history) / len(self.trinity_history)

        # 건강 상태 평가
        if avg_trinity < self.alert_threshold:
            await self._send_health_alert(avg_trinity)

        # 이상 감지 (급격한 하락)
        if len(self.trinity_history) >= 3:
            recent_drop = self.trinity_history[-3] - self.trinity_history[-1]
            if recent_drop > 15:
                await self._send_anomaly_alert(recent_drop)

    async def _send_health_alert(self, trinity_score: float) -> None:
        self.alerts_sent += 1
        self.logger.warning(
            f"🚨 HEALTH ALERT #{self.alerts_sent}: Trinity Score {trinity_score:.1f} (Threshold: {self.alert_threshold})"
        )
        self.logger.info("   권장 조치: 시스템 최적화 및 모니터링 강화")

        # 실제로는 Discord 알림, 이메일 등으로 전송
        # await self._send_notification("health_alert", trinity_score)

    async def _send_anomaly_alert(self, drop_amount: float) -> None:
        self.logger.warning(f"⚠️ ANOMALY DETECTED: Trinity Score 급락 {drop_amount:.1f}포인트")
        self.logger.info("   권장 조치: 즉시 시스템 진단 및 원인 분석")

    async def get_metrics(self) -> dict[str, Any]:
        return {
            "agent_type": "health_monitor",
            "current_trinity": self.trinity_history[-1] if self.trinity_history else 0,
            "avg_trinity": sum(self.trinity_history) / len(self.trinity_history)
            if self.trinity_history
            else 0,
            "alerts_sent": self.alerts_sent,
            "monitoring_samples": len(self.trinity_history),
        }


class CodeQualityGuardian(BackgroundAgent):
    """지속적 코드 품질 모니터링 에이전트"""

    def __init__(self):
        super().__init__("quality_guardian", "Code Quality Guardian")
        self.quality_issues: list[dict[str, Any]] = []
        self.improvements_suggested = 0

    async def execute_cycle(self) -> None:
        # 코드 품질 검사 (실제로는 AST 분석, linting 등 수행)
        issues_found = random.randint(0, 5)

        for i in range(issues_found):
            issue = {
                "type": random.choice(["type_hint", "docstring", "complexity", "import"]),
                "severity": random.choice(["low", "medium", "high"]),
                "file": f"packages/afo-core/src/{random.choice(['api', 'core', 'utils'])}/file_{i + 1}.py",
                "line": random.randint(1, 100),
                "description": f"코드 품질 개선 필요: {random.choice(['타입 힌트 누락', '문서화 부족', '복잡도 높음', '불필요한 import'])}",
            }
            self.quality_issues.append(issue)

        # 최근 10개 이슈만 유지
        if len(self.quality_issues) > 10:
            self.quality_issues = self.quality_issues[-10:]

        # 개선 제안 생성
        if issues_found > 0:
            await self._generate_improvement_suggestions(issues_found)

    async def _generate_improvement_suggestions(self, issues_count: int) -> None:
        self.improvements_suggested += issues_count
        self.logger.info(
            f"💡 CODE IMPROVEMENT #{self.improvements_suggested}: {issues_count}개 품질 이슈 발견"
        )

        # 개선 제안 생성 (실제로는 AI 모델이나 규칙 기반)
        suggestions = [
            "타입 힌트 추가로 코드 안정성 향상",
            "Docstring 작성으로 문서화 개선",
            "함수 분리로 복잡도 감소",
            "불필요한 import 정리로 성능 최적화",
        ]

        for i in range(min(issues_count, 3)):
            suggestion = random.choice(suggestions)
            self.logger.info(f"   → {suggestion}")

    async def get_metrics(self) -> dict[str, Any]:
        return {
            "agent_type": "quality_guardian",
            "issues_found": len(self.quality_issues),
            "improvements_suggested": self.improvements_suggested,
            "active_issues": len(
                [i for i in self.quality_issues if i["severity"] in ["medium", "high"]]
            ),
        }


class CollaborationOptimizer(BackgroundAgent):
    """3책사 협업 패턴 최적화 에이전트"""

    def __init__(self):
        super().__init__("collaboration_optimizer", "Collaboration Optimizer")
        self.collaboration_patterns: list[dict[str, Any]] = []
        self.optimizations_applied = 0

    async def execute_cycle(self) -> None:
        # 협업 패턴 분석 (실제로는 작업 로그, 통신 패턴 분석)
        current_efficiency = random.uniform(70, 95)

        # 최적화 기회 탐지
        optimization_opportunities = []

        # 작업 불균형 감지
        workload_balance = random.uniform(0.3, 0.9)
        if workload_balance < 0.6:
            optimization_opportunities.append(
                {
                    "type": "workload_balance",
                    "description": "제갈량의 작업량이 과중함 - 사마의로 재분배 권장",
                    "expected_improvement": 15,
                }
            )

        # 의사소통 효율성 분석
        communication_efficiency = random.uniform(0.5, 0.95)
        if communication_efficiency < 0.75:
            optimization_opportunities.append(
                {
                    "type": "communication",
                    "description": "3책사 간 의사소통 프로토콜 최적화 필요",
                    "expected_improvement": 20,
                }
            )

        # 최적화 적용
        if optimization_opportunities:
            await self._apply_collaboration_optimizations(optimization_opportunities)

        # 패턴 기록
        self.collaboration_patterns.append(
            {
                "timestamp": time.time(),
                "efficiency": current_efficiency,
                "optimizations": len(optimization_opportunities),
            }
        )

        # 최근 20개 패턴만 유지
        if len(self.collaboration_patterns) > 20:
            self.collaboration_patterns = self.collaboration_patterns[-20:]

    async def _apply_collaboration_optimizations(self, optimizations: list[dict[str, Any]]) -> None:
        for opt in optimizations:
            self.optimizations_applied += 1
            self.logger.info(f"🔧 COLLABORATION OPTIMIZATION #{self.optimizations_applied}")
            self.logger.info(f"   유형: {opt['type']}")
            self.logger.info(f"   설명: {opt['description']}")
            self.logger.info(f"   예상 개선: {opt['expected_improvement']}%")

            # 실제로는 최적화 로직 실행
            # await self._execute_optimization(opt)

    async def get_metrics(self) -> dict[str, Any]:
        return {
            "agent_type": "collaboration_optimizer",
            "patterns_analyzed": len(self.collaboration_patterns),
            "optimizations_applied": self.optimizations_applied,
            "avg_efficiency": sum(p["efficiency"] for p in self.collaboration_patterns)
            / len(self.collaboration_patterns)
            if self.collaboration_patterns
            else 0,
        }


class BackgroundAgentManager:
    """Background Agent들을 관리하는 중앙 매니저"""

    def __init__(self):
        self.agents: dict[str, BackgroundAgent] = {}
        self.is_system_running = False
        self.logger = logging.getLogger(f"{__name__}.BackgroundAgentManager")

    def register_agent(self, agent: BackgroundAgent) -> None:
        """에이전트 등록"""
        self.agents[agent.agent_id] = agent
        self.logger.info(f"📝 Registered background agent: {agent.name}")

    async def start_all_agents(self) -> None:
        """모든 백그라운드 에이전트 시작"""
        if self.is_system_running:
            self.logger.warning("Background system already running")
            return

        self.is_system_running = True
        self.logger.info("🚀 Starting Background Agent System")

        # 각 에이전트를 별도 태스크로 실행
        for agent in self.agents.values():
            agent.task = asyncio.create_task(agent.start_background_task())

        self.logger.info(f"✅ {len(self.agents)} background agents started")

    async def stop_all_agents(self) -> None:
        """모든 백그라운드 에이전트 중지"""
        if not self.is_system_running:
            self.logger.warning("Background system not running")
            return

        self.logger.info("🛑 Stopping Background Agent System")

        # 모든 에이전트 중지
        stop_tasks = []
        for agent in self.agents.values():
            stop_tasks.append(agent.stop_background_task())

        await asyncio.gather(*stop_tasks, return_exceptions=True)
        self.is_system_running = False

        self.logger.info("✅ All background agents stopped")

    async def get_system_status(self) -> dict[str, Any]:
        """전체 시스템 상태 조회"""
        agent_statuses = {}
        total_performance = 0

        for agent_id, agent in self.agents.items():
            metrics = await agent.get_metrics()
            agent_statuses[agent_id] = {
                "name": agent.name,
                "status": agent.status.status,
                "performance_score": agent.status.performance_score,
                "error_count": agent.status.error_count,
                "resource_usage": agent.status.resource_usage,
                "metrics": metrics,
            }
            total_performance += agent.status.performance_score

        return {
            "system_running": self.is_system_running,
            "total_agents": len(self.agents),
            "avg_performance": total_performance / len(self.agents) if self.agents else 0,
            "agent_statuses": agent_statuses,
        }

    async def optimize_resource_allocation(self, trinity_score: float) -> None:
        """Trinity Score 기반 리소스 할당 최적화"""
        if trinity_score > 90:
            # 고성능 모드: 모든 에이전트 활성화
            for agent in self.agents.values():
                if agent.status.status == "paused":
                    await agent.resume_background_task()
            self.logger.info("🔥 High-performance mode: All agents activated")

        elif trinity_score > 75:
            # 표준 모드: 필수 에이전트만 활성화
            essential_agents = ["health_monitor", "quality_guardian"]
            for agent_id, agent in self.agents.items():
                if agent_id in essential_agents and agent.status.status == "paused":
                    await agent.resume_background_task()
                elif agent_id not in essential_agents and agent.status.status == "running":
                    await agent.pause_background_task()
            self.logger.info("⚖️ Standard mode: Essential agents only")

        else:
            # 저성능 모드: 최소 에이전트만 활성화
            for agent in self.agents.values():
                if agent.agent_id != "health_monitor" and agent.status.status == "running":
                    await agent.pause_background_task()
            self.logger.info("🛡️ Low-performance mode: Critical monitoring only")


# 글로벌 매니저 인스턴스
background_agent_manager = BackgroundAgentManager()


# 초기화 함수
def initialize_background_agents():
    """백그라운드 에이전트 시스템 초기화"""
    global background_agent_manager

    # 에이전트 등록
    background_agent_manager.register_agent(HealthMonitorAgent())
    background_agent_manager.register_agent(CodeQualityGuardian())
    background_agent_manager.register_agent(CollaborationOptimizer())

    logger.info("🎯 Background Agents system initialized")
    return background_agent_manager


# 유틸리티 함수들
async def start_background_system():
    """백그라운드 시스템 시작"""
    await background_agent_manager.start_all_agents()


async def stop_background_system():
    """백그라운드 시스템 중지"""
    await background_agent_manager.stop_all_agents()


async def get_background_status():
    """백그라운드 시스템 상태 조회"""
    return await background_agent_manager.get_system_status()


async def optimize_based_on_trinity(trinity_score: float):
    """Trinity Score 기반 최적화"""
    await background_agent_manager.optimize_resource_allocation(trinity_score)


if __name__ == "__main__":
    # 직접 실행 시 데모
    async def demo():
        print("🎯 Background Agents Phase 79 프로토타입 데모")
        print("=" * 60)

        # 초기화
        initialize_background_agents()

        # 시스템 시작
        await start_background_system()

        # 짧은 데모 (실제로는 지속 실행)
        print("\n⏳ Background agents running for 10 seconds...")
        await asyncio.sleep(10)

        # 상태 보고
        status = await get_background_status()
        print(f"\n📊 시스템 상태: {'✅ 실행 중' if status['system_running'] else '❌ 중지됨'}")
        print(f"등록된 에이전트: {status['total_agents']}개")
        print(f"평균 성능 점수: {status['avg_performance']:.1f}%")

        # 시스템 종료
        await stop_background_system()
        print("\n✅ Background Agents 데모 완료!")

    asyncio.run(demo())
