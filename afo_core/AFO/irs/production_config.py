"""
Production Config - 프로덕션 환경 설정

孝 (Serenity): 평온 수호/운영 마찰 제거
- 프로덕션 환경 설정 관리
- 환경 변수 및 보안 설정
- 로깅 및 모니터링 설정
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class IRSProductionConfig:
    """
    IRS Monitor Agent 프로덕션 설정
    """

    # ===== IRS 모니터링 설정 =====
    IRS_MONITOR_ENABLED: bool = True
    IRS_MONITOR_CRITICAL_INTERVAL_HOURS: int = 6
    IRS_MONITOR_HIGH_INTERVAL_HOURS: int = 12
    IRS_MONITOR_MEDIUM_INTERVAL_HOURS: int = 24

    # ===== 크롤러 설정 =====
    IRS_CRAWLER_MAX_RETRIES: int = 3
    IRS_CRAWLER_RETRY_BACKOFF_SECONDS: int = 2
    IRS_CRAWLER_TIMEOUT_SECONDS: int = 30
    IRS_CRAWLER_RATE_LIMIT_DELAY_SECONDS: int = 5
    IRS_CRAWLER_USER_AGENT: str = "AFO-Kingdom-IRS-Monitor/1.0 (Tax Law Monitoring System)"

    # ===== 캐싱 설정 =====
    IRS_CACHE_ENABLED: bool = True
    IRS_CACHE_EXPIRY_HOURS: int = 6
    IRS_CACHE_MAX_SIZE_MB: int = 100

    # ===== Trinity Score Gate 설정 =====
    TRINITY_GATE_MIN_AUTO_RUN_SCORE: float = 0.90
    TRINITY_GATE_MIN_ASK_SCORE: float = 0.70
    TRINITY_GATE_MAX_RISK_SCORE: float = 0.10

    # ===== 업데이트 설정 =====
    IRS_UPDATER_MIN_TRINITY_SCORE: float = 0.80

    # ===== 롤백 설정 =====
    IRS_ROLLBACK_ENABLED: bool = True
    IRS_ROLLBACK_MAX_VERSIONS: int = 10

    # ===== 알림 설정 =====
    IRS_NOTIFICATION_ENABLED: bool = True
    IRS_NOTIFICATION_CHANNELS: list[str] = field(default_factory=lambda: ["discord"])
    IRS_NOTIFICATION_CRITICAL_CHANNELS: list[str] = field(
        default_factory=lambda: ["discord", "email"]
    )

    # ===== Julie CPA 통합 설정 =====
    JULIE_INTEGRATION_ENABLED: bool = True
    JULIE_ALERTS_MAX_COUNT: int = 1000

    # ===== 로깅 설정 =====
    IRS_LOG_LEVEL: str = "INFO"
    IRS_LOG_FILE: str = "logs/irs_monitor.log"
    IRS_LOG_MAX_SIZE_MB: int = 10
    IRS_LOG_BACKUP_COUNT: int = 5

    # ===== 보안 설정 =====
    IRS_ENCRYPTION_ENABLED: bool = True
    IRS_ENCRYPTION_KEY_FILE: str = "data/keys/encryption_key"
    IRS_SECURITY_GATE_ENABLED: bool = True
    IRS_SECURITY_PII_DETECTION_ENABLED: bool = True

    # ===== 데이터 저장소 설정 =====
    IRS_SSOT_PATH: str = "data/ssot"
    IRS_BACKUP_PATH: str = "data/ssot/backups"
    IRS_EVIDENCE_PATH: str = "data/irs_monitor/evidence_bundles"
    IRS_TRANSACTION_LOG: str = "data/transactions/log.json"
    IRS_ROLLBACK_LOG: str = "data/rollbacks/log.json"
    IRS_ALERTS_FILE: str = "data/julie_alerts/alerts.json"
    IRS_CACHE_DIR: str = "data/irs_monitor/cache"
    IRS_SCHEDULER_STATE: str = "data/irs_monitor/scheduler_state.json"

    # ===== 외부 서비스 설정 =====
    IRS_WEBHOOK_URL: str | None = None
    IRS_EMAIL_ENABLED: bool = False
    IRS_EMAIL_SMTP_HOST: str = "smtp.gmail.com"
    IRS_EMAIL_SMTP_PORT: int = 587
    IRS_EMAIL_FROM: str = "alerts@afo-kingdom.com"
    IRS_EMAIL_TO: str = "cpa-team@afo-kingdom.com"

    # ===== 모니터링 설정 =====
    IRS_HEALTH_CHECK_ENABLED: bool = True
    IRS_METRICS_ENABLED: bool = True
    IRS_METRICS_PORT: int = 9090

    @classmethod
    def from_env(cls) -> IRSProductionConfig:
        """
        환경 변수에서 설정 로드

        Returns:
            IRSProductionConfig
        """
        return cls(
            # IRS 모니터링 설정
            IRS_MONITOR_ENABLED=os.getenv("IRS_MONITOR_ENABLED", "true").lower() == "true",
            IRS_MONITOR_CRITICAL_INTERVAL_HOURS=int(
                os.getenv("IRS_MONITOR_CRITICAL_INTERVAL_HOURS", "6")
            ),
            IRS_MONITOR_HIGH_INTERVAL_HOURS=int(os.getenv("IRS_MONITOR_HIGH_INTERVAL_HOURS", "12")),
            IRS_MONITOR_MEDIUM_INTERVAL_HOURS=int(
                os.getenv("IRS_MONITOR_MEDIUM_INTERVAL_HOURS", "24")
            ),
            # 크롤러 설정
            IRS_CRAWLER_MAX_RETRIES=int(os.getenv("IRS_CRAWLER_MAX_RETRIES", "3")),
            IRS_CRAWLER_RETRY_BACKOFF_SECONDS=int(
                os.getenv("IRS_CRAWLER_RETRY_BACKOFF_SECONDS", "2")
            ),
            IRS_CRAWLER_TIMEOUT_SECONDS=int(os.getenv("IRS_CRAWLER_TIMEOUT_SECONDS", "30")),
            IRS_CRAWLER_RATE_LIMIT_DELAY_SECONDS=int(
                os.getenv("IRS_CRAWLER_RATE_LIMIT_DELAY_SECONDS", "5")
            ),
            IRS_CRAWLER_USER_AGENT=os.getenv(
                "IRS_CRAWLER_USER_AGENT",
                cls.IRS_CRAWLER_USER_AGENT,
            ),
            # 캐싱 설정
            IRS_CACHE_ENABLED=os.getenv("IRS_CACHE_ENABLED", "true").lower() == "true",
            IRS_CACHE_EXPIRY_HOURS=int(os.getenv("IRS_CACHE_EXPIRY_HOURS", "6")),
            IRS_CACHE_MAX_SIZE_MB=int(os.getenv("IRS_CACHE_MAX_SIZE_MB", "100")),
            # Trinity Score Gate 설정
            TRINITY_GATE_MIN_AUTO_RUN_SCORE=float(
                os.getenv("TRINITY_GATE_MIN_AUTO_RUN_SCORE", "0.90")
            ),
            TRINITY_GATE_MIN_ASK_SCORE=float(os.getenv("TRINITY_GATE_MIN_ASK_SCORE", "0.70")),
            TRINITY_GATE_MAX_RISK_SCORE=float(os.getenv("TRINITY_GATE_MAX_RISK_SCORE", "0.10")),
            # 업데이트 설정
            IRS_UPDATER_MIN_TRINITY_SCORE=float(os.getenv("IRS_UPDATER_MIN_TRINITY_SCORE", "0.80")),
            # 롤백 설정
            IRS_ROLLBACK_ENABLED=os.getenv("IRS_ROLLBACK_ENABLED", "true").lower() == "true",
            IRS_ROLLBACK_MAX_VERSIONS=int(os.getenv("IRS_ROLLBACK_MAX_VERSIONS", "10")),
            # 알림 설정
            IRS_NOTIFICATION_ENABLED=os.getenv("IRS_NOTIFICATION_ENABLED", "true").lower()
            == "true",
            IRS_NOTIFICATION_CHANNELS=os.getenv("IRS_NOTIFICATION_CHANNELS", "discord").split(","),
            IRS_NOTIFICATION_CRITICAL_CHANNELS=os.getenv(
                "IRS_NOTIFICATION_CRITICAL_CHANNELS", "discord,email"
            ).split(","),
            # Julie CPA 통합 설정
            JULIE_INTEGRATION_ENABLED=os.getenv("JULIE_INTEGRATION_ENABLED", "true").lower()
            == "true",
            JULIE_ALERTS_MAX_COUNT=int(os.getenv("JULIE_ALERTS_MAX_COUNT", "1000")),
            # 로깅 설정
            IRS_LOG_LEVEL=os.getenv("IRS_LOG_LEVEL", "INFO"),
            IRS_LOG_FILE=os.getenv("IRS_LOG_FILE", "logs/irs_monitor.log"),
            IRS_LOG_MAX_SIZE_MB=int(os.getenv("IRS_LOG_MAX_SIZE_MB", "10")),
            IRS_LOG_BACKUP_COUNT=int(os.getenv("IRS_LOG_BACKUP_COUNT", "5")),
            # 보안 설정
            IRS_ENCRYPTION_ENABLED=os.getenv("IRS_ENCRYPTION_ENABLED", "true").lower() == "true",
            IRS_ENCRYPTION_KEY_FILE=os.getenv(
                "IRS_ENCRYPTION_KEY_FILE", "data/keys/encryption_key"
            ),
            IRS_SECURITY_GATE_ENABLED=os.getenv("IRS_SECURITY_GATE_ENABLED", "true").lower()
            == "true",
            IRS_SECURITY_PII_DETECTION_ENABLED=os.getenv(
                "IRS_SECURITY_PII_DETECTION_ENABLED", "true"
            ).lower()
            == "true",
            # 데이터 저장소 설정
            IRS_SSOT_PATH=os.getenv("IRS_SSOT_PATH", "data/ssot"),
            IRS_BACKUP_PATH=os.getenv("IRS_BACKUP_PATH", "data/ssot/backups"),
            IRS_EVIDENCE_PATH=os.getenv("IRS_EVIDENCE_PATH", "data/irs_monitor/evidence_bundles"),
            IRS_TRANSACTION_LOG=os.getenv("IRS_TRANSACTION_LOG", "data/transactions/log.json"),
            IRS_ROLLBACK_LOG=os.getenv("IRS_ROLLBACK_LOG", "data/rollbacks/log.json"),
            IRS_ALERTS_FILE=os.getenv("IRS_ALERTS_FILE", "data/julie_alerts/alerts.json"),
            IRS_CACHE_DIR=os.getenv("IRS_CACHE_DIR", "data/irs_monitor/cache"),
            IRS_SCHEDULER_STATE=os.getenv(
                "IRS_SCHEDULER_STATE", "data/irs_monitor/scheduler_state.json"
            ),
            # 외부 서비스 설정
            IRS_WEBHOOK_URL=os.getenv("IRS_WEBHOOK_URL"),
            IRS_EMAIL_ENABLED=os.getenv("IRS_EMAIL_ENABLED", "false").lower() == "true",
            IRS_EMAIL_SMTP_HOST=os.getenv("IRS_EMAIL_SMTP_HOST", "smtp.gmail.com"),
            IRS_EMAIL_SMTP_PORT=int(os.getenv("IRS_EMAIL_SMTP_PORT", "587")),
            IRS_EMAIL_FROM=os.getenv("IRS_EMAIL_FROM", "alerts@afo-kingdom.com"),
            IRS_EMAIL_TO=os.getenv("IRS_EMAIL_TO", "cpa-team@afo-kingdom.com"),
            # 모니터링 설정
            IRS_HEALTH_CHECK_ENABLED=os.getenv("IRS_HEALTH_CHECK_ENABLED", "true").lower()
            == "true",
            IRS_METRICS_ENABLED=os.getenv("IRS_METRICS_ENABLED", "true").lower() == "true",
            IRS_METRICS_PORT=int(os.getenv("IRS_METRICS_PORT", "9090")),
        )

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "IRS_MONITOR_ENABLED": self.IRS_MONITOR_ENABLED,
            "IRS_MONITOR_CRITICAL_INTERVAL_HOURS": self.IRS_MONITOR_CRITICAL_INTERVAL_HOURS,
            "IRS_MONITOR_HIGH_INTERVAL_HOURS": self.IRS_MONITOR_HIGH_INTERVAL_HOURS,
            "IRS_MONITOR_MEDIUM_INTERVAL_HOURS": self.IRS_MONITOR_MEDIUM_INTERVAL_HOURS,
            "IRS_CRAWLER_MAX_RETRIES": self.IRS_CRAWLER_MAX_RETRIES,
            "IRS_CRAWLER_RETRY_BACKOFF_SECONDS": self.IRS_CRAWLER_RETRY_BACKOFF_SECONDS,
            "IRS_CRAWLER_TIMEOUT_SECONDS": self.IRS_CRAWLER_TIMEOUT_SECONDS,
            "IRS_CRAWLER_RATE_LIMIT_DELAY_SECONDS": self.IRS_CRAWLER_RATE_LIMIT_DELAY_SECONDS,
            "IRS_CACHE_ENABLED": self.IRS_CACHE_ENABLED,
            "IRS_CACHE_EXPIRY_HOURS": self.IRS_CACHE_EXPIRY_HOURS,
            "TRINITY_GATE_MIN_AUTO_RUN_SCORE": self.TRINITY_GATE_MIN_AUTO_RUN_SCORE,
            "TRINITY_GATE_MIN_ASK_SCORE": self.TRINITY_GATE_MIN_ASK_SCORE,
            "TRINITY_GATE_MAX_RISK_SCORE": self.TRINITY_GATE_MAX_RISK_SCORE,
            "IRS_UPDATER_MIN_TRINITY_SCORE": self.IRS_UPDATER_MIN_TRINITY_SCORE,
            "IRS_ROLLBACK_ENABLED": self.IRS_ROLLBACK_ENABLED,
            "IRS_ROLLBACK_MAX_VERSIONS": self.IRS_ROLLBACK_MAX_VERSIONS,
            "IRS_NOTIFICATION_ENABLED": self.IRS_NOTIFICATION_ENABLED,
            "IRS_NOTIFICATION_CHANNELS": self.IRS_NOTIFICATION_CHANNELS,
            "JULIE_INTEGRATION_ENABLED": self.JULIE_INTEGRATION_ENABLED,
            "IRS_LOG_LEVEL": self.IRS_LOG_LEVEL,
            "IRS_ENCRYPTION_ENABLED": self.IRS_ENCRYPTION_ENABLED,
            "IRS_SECURITY_GATE_ENABLED": self.IRS_SECURITY_GATE_ENABLED,
            "IRS_METRICS_PORT": self.IRS_METRICS_PORT,
        }

    def validate(self) -> bool:
        """
        설정 검증

        Returns:
            유효성 여부
        """
        # 주기 검증
        if self.IRS_MONITOR_CRITICAL_INTERVAL_HOURS < 1:
            raise ValueError("Critical 주기는 1시간 이상이어야 합니다")

        if self.IRS_MONITOR_CRITICAL_INTERVAL_HOURS > 24:
            raise ValueError("Critical 주기는 24시간 이하여야 합니다")

        # Trinity Score 검증
        if not 0.0 <= self.TRINITY_GATE_MIN_AUTO_RUN_SCORE <= 1.0:
            raise ValueError("AUTO_RUN 점수는 0.0 ~ 1.0 사이여야 합니다")

        if not 0.0 <= self.TRINITY_GATE_MIN_ASK_SCORE <= 1.0:
            raise ValueError("ASK 점수는 0.0 ~ 1.0 사이여야 합니다")

        if self.TRINITY_GATE_MIN_AUTO_RUN_SCORE <= self.TRINITY_GATE_MIN_ASK_SCORE:
            raise ValueError("AUTO_RUN 점수는 ASK 점수보다 높아야 합니다")

        # 캐싱 검증
        if self.IRS_CACHE_MAX_SIZE_MB < 10:
            raise ValueError("캐시 최대 크기는 10MB 이상이어야 합니다")

        return True


class HealthCheckResponse(BaseModel):
    """Health Check 응답"""

    status: str = Field(..., description="health status (healthy/unhealthy)")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    version: str = Field(..., description="service version")
    checks: dict[str, Any] = Field(default_factory=dict)
