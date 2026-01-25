# Trinity Score: 90.0 (Established by Chancellor)
"""
System Monitoring Dashboard for AFO Kingdom (Phase 11)
Comprehensive system monitoring with real-time metrics and Trinity Score integration.
Sequential Thinking: 단계별 모니터링 시스템 구축 및 최적화
"""

import asyncio
import contextlib
import logging
import time
from typing import Any, cast

import psutil
from pydantic import BaseModel, Field

from .langchain_openai_service import get_ai_stats
from .redis_cache_service import get_cache_stats

# Import Task type for type hints
Task = asyncio.Task

# 로깅 설정
logger = logging.getLogger(__name__)

# 모니터링 설정
MONITORING_CONFIG = {
    "update_interval": 30,  # 30초마다 업데이트
    "retention_period": 3600,  # 1시간 데이터 유지
    "alert_thresholds": {
        "cpu_percent": 80.0,
        "memory_percent": 85.0,
        "disk_percent": 90.0,
        "error_rate": 5.0,  # 5% 에러율
    },
    "metrics_enabled": [
        "system_resources",
        "application_metrics",
        "cache_performance",
        "ai_service_stats",
        "trinity_health",
    ],
}


class SystemMetrics(BaseModel):
    """시스템 메트릭 모델"""

    timestamp: float = Field(default_factory=time.time)

    # 시스템 리소스
    cpu_percent: float = Field(default=0.0, description="CPU 사용률 (%)")
    memory_percent: float = Field(default=0.0, description="메모리 사용률 (%)")
    memory_used_gb: float = Field(default=0.0, description="사용 메모리 (GB)")
    memory_total_gb: float = Field(default=0.0, description="전체 메모리 (GB)")
    disk_percent: float = Field(default=0.0, description="디스크 사용률 (%)")
    disk_used_gb: float = Field(default=0.0, description="사용 디스크 (GB)")
    disk_total_gb: float = Field(default=0.0, description="전체 디스크 (GB)")
    network_bytes_sent: int = Field(default=0, description="네트워크 송신 바이트")
    network_bytes_recv: int = Field(default=0, description="네트워크 수신 바이트")

    # 프로세스 정보
    process_count: int = Field(default=0, description="실행 중인 프로세스 수")
    thread_count: int = Field(default=0, description="실행 중인 스레드 수")


class ApplicationMetrics(BaseModel):
    """애플리케이션 메트릭 모델"""

    timestamp: float = Field(default_factory=time.time)

    # 요청 메트릭
    total_requests: int = Field(default=0, description="총 요청 수")
    active_requests: int = Field(default=0, description="활성 요청 수")
    error_count: int = Field(default=0, description="에러 발생 수")
    avg_response_time: float = Field(default=0.0, description="평균 응답 시간 (초)")

    # 메모리 메트릭
    python_memory_mb: float = Field(default=0.0, description="Python 메모리 사용량 (MB)")
    gc_collections: int = Field(default=0, description="가비지 컬렉션 실행 횟수")

    # 서비스 상태
    services_status: dict[str, str] = Field(default_factory=dict, description="서비스별 상태")


class TrinityHealthScore(BaseModel):
    """Trinity 건강 점수 모델"""

    timestamp: float = Field(default_factory=time.time)

    truth_score: float = Field(default=0.0, ge=0.0, le=100.0, description="眞 점수")
    goodness_score: float = Field(default=0.0, ge=0.0, le=100.0, description="善 점수")
    beauty_score: float = Field(default=0.0, ge=0.0, le=100.0, description="美 점수")
    serenity_score: float = Field(default=0.0, ge=0.0, le=100.0, description="孝 점수")
    eternity_score: float = Field(default=0.0, ge=0.0, le=100.0, description="永 점수")

    overall_score: float = Field(default=0.0, ge=0.0, le=100.0, description="종합 Trinity 점수")

    health_status: str = Field(default="unknown", description="건강 상태")
    recommendations: list[str] = Field(default_factory=list, description="개선 권장사항")


class Alert(BaseModel):
    """알림 모델"""

    id: str
    timestamp: float = Field(default_factory=time.time)
    level: str = Field(..., description="알림 레벨 (info/warning/error/critical)")
    service: str = Field(..., description="관련 서비스")
    message: str = Field(..., description="알림 메시지")
    details: dict[str, Any] = Field(default_factory=dict, description="상세 정보")
    resolved: bool = Field(default=False, description="해결 여부")


class SystemMonitoringDashboard:
    """
    시스템 모니터링 대시보드
    Sequential Thinking: 단계별 모니터링 시스템 구현
    """

    def __init__(self) -> None:
        self._running = False
        self._task: Task | None = None

        # 메트릭 저장소
        self.system_metrics_history: list[SystemMetrics] = []
        self.application_metrics_history: list[ApplicationMetrics] = []
        self.trinity_scores_history: list[TrinityHealthScore] = []

        # 알림 시스템
        self.active_alerts: list[Alert] = []
        self.alert_history: list[Alert] = []

        # 성능 카운터
        self._last_network_sent = 0
        self._last_network_recv = 0

    async def start_monitoring(self) -> bool:
        """
        모니터링 시작 (Sequential Thinking Phase 1)
        """
        if self._running:
            logger.warning("모니터링이 이미 실행 중입니다")
            return False

        try:
            self._running = True
            self._task = asyncio.create_task(self._monitoring_loop())

            logger.info("✅ 시스템 모니터링 대시보드 시작")
            return True

        except Exception as e:
            logger.error(f"❌ 모니터링 시작 실패: {e}")
            self._running = False
            return False

    async def stop_monitoring(self) -> bool:
        """
        모니터링 중지 (Sequential Thinking Phase 2)
        """
        if not self._running:
            return True

        try:
            self._running = False

            if self._task:
                self._task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._task

            logger.info("✅ 시스템 모니터링 대시보드 중지")
            return True

        except Exception as e:
            logger.error(f"❌ 모니터링 중지 실패: {e}")
            return False

    async def _monitoring_loop(self) -> None:
        """
        모니터링 루프 (Sequential Thinking Phase 3)
        """
        logger.info("모니터링 루프 시작")

        while self._running:
            try:
                # Phase 3.1: 시스템 메트릭 수집
                system_metrics = await self._collect_system_metrics()

                # Phase 3.2: 애플리케이션 메트릭 수집
                app_metrics = await self._collect_application_metrics()

                # Phase 3.3: Trinity 건강 점수 계산
                trinity_score = await self._calculate_trinity_health_score()

                # Phase 3.4: 메트릭 저장
                self._store_metrics(system_metrics, app_metrics, trinity_score)

                # Phase 3.5: 알림 검사
                await self._check_alerts(system_metrics, app_metrics, trinity_score)

                # Phase 3.6: 오래된 데이터 정리
                self._cleanup_old_data()

                # 대기
                await asyncio.sleep(cast("float", MONITORING_CONFIG["update_interval"]))

            except Exception as e:
                logger.error(f"모니터링 루프 에러: {e}")
                await asyncio.sleep(5)  # 에러 시 잠시 대기

    async def _collect_system_metrics(self) -> SystemMetrics:
        """
        시스템 메트릭 수집 (Sequential Thinking Phase 4)
        """
        try:
            # CPU 정보
            cpu_percent = psutil.cpu_percent(interval=1)

            # 메모리 정보
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)

            # 디스크 정보
            disk = psutil.disk_usage("/")
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)

            # 네트워크 정보
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv

            # 네트워크 변화량 계산
            sent_diff = (
                network_bytes_sent - self._last_network_sent if self._last_network_sent > 0 else 0
            )
            recv_diff = (
                network_bytes_recv - self._last_network_recv if self._last_network_recv > 0 else 0
            )

            self._last_network_sent = network_bytes_sent
            self._last_network_recv = network_bytes_recv

            # 프로세스 정보
            process_count = len(psutil.pids())
            thread_count = sum(
                len(p.threads()) for p in psutil.process_iter(["threads"]) if p.info["threads"]
            )

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=round(memory_used_gb, 2),
                memory_total_gb=round(memory_total_gb, 2),
                disk_percent=disk.percent,
                disk_used_gb=round(disk_used_gb, 2),
                disk_total_gb=round(disk_total_gb, 2),
                network_bytes_sent=sent_diff,
                network_bytes_recv=recv_diff,
                process_count=process_count,
                thread_count=thread_count,
            )

        except Exception as e:
            logger.error(f"시스템 메트릭 수집 실패: {e}")
            return SystemMetrics()

    async def _collect_application_metrics(self) -> ApplicationMetrics:
        """
        애플리케이션 메트릭 수집 (Sequential Thinking Phase 5)
        """
        try:
            # Python 메모리 사용량
            process = psutil.Process()
            memory_info = process.memory_info()
            python_memory_mb = memory_info.rss / (1024 * 1024)

            # GC 정보
            import gc

            gc_collections = sum(gc.get_stats()[i]["collected"] for i in range(3))

            # 서비스 상태 확인
            services_status = {}

            # 캐시 서비스 상태
            try:
                cache_stats = await get_cache_stats()
                services_status["redis_cache"] = "healthy" if cache_stats else "unknown"
            except Exception:
                services_status["redis_cache"] = "error"

            # AI 서비스 상태
            try:
                ai_stats = await get_ai_stats()
                services_status["ai_service"] = (
                    "healthy" if ai_stats.get("initialized") else "unhealthy"
                )
            except Exception:
                services_status["ai_service"] = "error"

            return ApplicationMetrics(
                python_memory_mb=round(python_memory_mb, 2),
                gc_collections=gc_collections,
                services_status=services_status,
            )

        except Exception as e:
            logger.error(f"애플리케이션 메트릭 수집 실패: {e}")
            return ApplicationMetrics()

    async def _calculate_trinity_health_score(self) -> TrinityHealthScore:
        """
        Trinity 건강 점수 계산 (Sequential Thinking Phase 6)
        """
        try:
            # 시스템 메트릭 기반 점수 계산
            if not self.system_metrics_history:
                return TrinityHealthScore()

            latest_system = self.system_metrics_history[-1]

            # 眞 (Truth) - 기술적 정확성: CPU/메모리 효율성
            truth_score = max(
                0, 100 - (latest_system.cpu_percent + latest_system.memory_percent) / 2
            )

            # 善 (Goodness) - 안전성: 리소스 사용량 적정성
            goodness_score = min(100, 100 - max(0, latest_system.memory_percent - 70))

            # 美 (Beauty) - 구조적 우아함: 시스템 균형
            beauty_score = 100 - abs(latest_system.cpu_percent - latest_system.memory_percent)

            # 孝 (Serenity) - 평온함: 안정적 리소스 사용
            serenity_score = 100 - (latest_system.cpu_percent + latest_system.memory_percent) / 4

            # 永 (Eternity) - 지속가능성: 장기 안정성
            eternity_score = min(100, 100 - latest_system.disk_percent)

            # 종합 점수 계산
            weights = [0.35, 0.35, 0.20, 0.08, 0.02]  # Trinity 가중치
            scores = [
                truth_score,
                goodness_score,
                beauty_score,
                serenity_score,
                eternity_score,
            ]
            overall_score = sum(w * s for w, s in zip(weights, scores, strict=False))

            # 건강 상태 판정
            if overall_score >= 90:
                health_status = "excellent"
            elif overall_score >= 80:
                health_status = "good"
            elif overall_score >= 70:
                health_status = "fair"
            elif overall_score >= 60:
                health_status = "poor"
            else:
                health_status = "critical"

            # 개선 권장사항 생성
            recommendations = []

            if latest_system.cpu_percent > 80:
                recommendations.append("CPU 사용량이 높습니다. 최적화가 필요합니다.")
            if latest_system.memory_percent > 85:
                recommendations.append("메모리 사용량이 높습니다. 메모리 관리가 필요합니다.")
            if latest_system.disk_percent > 90:
                recommendations.append("디스크 사용량이 높습니다. 정리 또는 확장이 필요합니다.")
            if overall_score < 80:
                recommendations.append("전체 시스템 건강 상태 개선이 필요합니다.")

            return TrinityHealthScore(
                truth_score=round(truth_score, 1),
                goodness_score=round(goodness_score, 1),
                beauty_score=round(beauty_score, 1),
                serenity_score=round(serenity_score, 1),
                eternity_score=round(eternity_score, 1),
                overall_score=round(overall_score, 1),
                health_status=health_status,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Trinity 건강 점수 계산 실패: {e}")
            return TrinityHealthScore()

    def _store_metrics(
        self,
        system_metrics: SystemMetrics,
        app_metrics: ApplicationMetrics,
        trinity_score: TrinityHealthScore,
    ) -> None:
        """
        메트릭 저장 (Sequential Thinking Phase 7)
        """
        try:
            # 메트릭 저장
            self.system_metrics_history.append(system_metrics)
            self.application_metrics_history.append(app_metrics)
            self.trinity_scores_history.append(trinity_score)

            # 오래된 데이터 제한 (최근 100개 유지)
            max_history = 100
            if len(self.system_metrics_history) > max_history:
                self.system_metrics_history = self.system_metrics_history[-max_history:]
            if len(self.application_metrics_history) > max_history:
                self.application_metrics_history = self.application_metrics_history[-max_history:]
            if len(self.trinity_scores_history) > max_history:
                self.trinity_scores_history = self.trinity_scores_history[-max_history:]

        except Exception as e:
            logger.error(f"메트릭 저장 실패: {e}")

    async def _check_alerts(
        self,
        system_metrics: SystemMetrics,
        app_metrics: ApplicationMetrics,
        trinity_score: TrinityHealthScore,
    ) -> None:
        """
        알림 검사 (Sequential Thinking Phase 8)
        """
        try:
            alerts_to_add = []
            # 타입 명시: alert_thresholds는 dict[str, float]
            monitoring_config: dict[str, Any] = MONITORING_CONFIG
            alert_thresholds: dict[str, float] = monitoring_config["alert_thresholds"]

            # CPU 사용량 알림
            if system_metrics.cpu_percent > alert_thresholds["cpu_percent"]:
                alerts_to_add.append(
                    Alert(
                        id=f"cpu_high_{int(time.time())}",
                        level="warning",
                        service="system",
                        message=f"CPU 사용량이 높습니다: {system_metrics.cpu_percent:.1f}%",
                        details={"cpu_percent": system_metrics.cpu_percent},
                    )
                )

            # 메모리 사용량 알림
            if system_metrics.memory_percent > alert_thresholds["memory_percent"]:
                alerts_to_add.append(
                    Alert(
                        id=f"memory_high_{int(time.time())}",
                        level="warning",
                        service="system",
                        message=f"메모리 사용량이 높습니다: {system_metrics.memory_percent:.1f}%",
                        details={"memory_percent": system_metrics.memory_percent},
                    )
                )

            # 디스크 사용량 알림
            if system_metrics.disk_percent > alert_thresholds["disk_percent"]:
                alerts_to_add.append(
                    Alert(
                        id=f"disk_high_{int(time.time())}",
                        level="critical",
                        service="system",
                        message=f"디스크 사용량이 위험합니다: {system_metrics.disk_percent:.1f}%",
                        details={"disk_percent": system_metrics.disk_percent},
                    )
                )

            # Trinity 건강 상태 알림
            if trinity_score.overall_score < 70:
                alerts_to_add.append(
                    Alert(
                        id=f"trinity_low_{int(time.time())}",
                        level="error",
                        service="trinity",
                        message=f"Trinity 건강 점수가 낮습니다: {trinity_score.overall_score:.1f}",
                        details={"trinity_score": trinity_score.overall_score},
                    )
                )

            # 활성 알림 추가
            for alert in alerts_to_add:
                self.active_alerts.append(alert)
                logger.warning(f"새 알림 발생: {alert.message}")

        except Exception as e:
            logger.error(f"알림 검사 실패: {e}")

    def _cleanup_old_data(self) -> None:
        """
        오래된 데이터 정리 (Sequential Thinking Phase 9)
        """
        try:
            current_time = time.time()
            retention_time = cast("float", MONITORING_CONFIG["retention_period"])

            # 메트릭 정리
            # 타입 명시: timestamp는 float
            self.system_metrics_history = [
                m
                for m in self.system_metrics_history
                if isinstance(m.timestamp, (int, float))
                and current_time - m.timestamp < retention_time
            ]
            self.application_metrics_history = [
                m
                for m in self.application_metrics_history
                if isinstance(m.timestamp, (int, float))
                and current_time - m.timestamp < retention_time
            ]
            self.trinity_scores_history = [
                m
                for m in self.trinity_scores_history
                if isinstance(m.timestamp, (int, float))
                and current_time - m.timestamp < retention_time
            ]

            # 해결된 알림 정리
            self.alert_history.extend([a for a in self.active_alerts if a.resolved])
            self.active_alerts = [a for a in self.active_alerts if not a.resolved]

        except Exception as e:
            logger.error(f"데이터 정리 실패: {e}")

    def get_dashboard_data(self) -> dict[str, Any]:
        """
        대시보드 데이터 조회 (Sequential Thinking Phase 10)
        """
        try:
            return {
                "timestamp": time.time(),
                "monitoring_status": "running" if self._running else "stopped",
                # 최신 메트릭
                "latest_system_metrics": (
                    self.system_metrics_history[-1].model_dump()
                    if self.system_metrics_history
                    else None
                ),
                "latest_app_metrics": (
                    self.application_metrics_history[-1].model_dump()
                    if self.application_metrics_history
                    else None
                ),
                "latest_trinity_score": (
                    self.trinity_scores_history[-1].model_dump()
                    if self.trinity_scores_history
                    else None
                ),
                # 메트릭 히스토리
                "system_metrics_count": len(self.system_metrics_history),
                "app_metrics_count": len(self.application_metrics_history),
                "trinity_scores_count": len(self.trinity_scores_history),
                # 알림 상태
                "active_alerts": [alert.model_dump() for alert in self.active_alerts],
                "total_alerts_history": len(self.alert_history),
                # 설정 정보
                "config": MONITORING_CONFIG,
            }

        except Exception as e:
            logger.error(f"대시보드 데이터 조회 실패: {e}")
            return {"error": str(e)}

    def resolve_alert(self, alert_id: str) -> bool:
        """
        알림 해결 처리
        """
        try:
            for alert in self.active_alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    logger.info(f"알림 해결됨: {alert_id}")
                    return True
            return False

        except Exception as e:
            logger.error(f"알림 해결 처리 실패: {e}")
            return False


# 전역 인스턴스
monitoring_dashboard = SystemMonitoringDashboard()


async def start_monitoring_dashboard() -> bool:
    """모니터링 대시보드 시작"""
    return await monitoring_dashboard.start_monitoring()


async def stop_monitoring_dashboard() -> bool:
    """모니터링 대시보드 중지"""
    return await monitoring_dashboard.stop_monitoring()


async def get_monitoring_dashboard_data() -> dict[str, Any]:
    """모니터링 대시보드 데이터 조회"""
    return monitoring_dashboard.get_dashboard_data()


def resolve_monitoring_alert(alert_id: str) -> bool:
    """모니터링 알림 해결"""
    return monitoring_dashboard.resolve_alert(alert_id)
