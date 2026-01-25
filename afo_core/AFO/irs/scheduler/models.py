"""Scheduler Models.

IRS 모니터링 스케줄러를 위한 데이터 모델 및 상태 정의.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SchedulerStatus(str, Enum):
    """스케줄러 상태."""

    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class MonitorJob:
    """개별 모니터링 작업 정보."""

    job_id: str
    document_id: str
    interval_hours: int
    last_run: str | None = None
    last_status: str | None = None
    last_result: dict[str, Any] | None = None
    consecutive_failures: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "document_id": self.document_id,
            "interval_hours": self.interval_hours,
            "last_run": self.last_run,
            "last_status": self.last_status,
            "consecutive_failures": self.consecutive_failures,
        }
