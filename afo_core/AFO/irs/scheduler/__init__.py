"""IRS Monitor Scheduler Package.

24/7 IRS 규정 변경 모니터링 시스템.
효(Serenity) 기둥을 담당하며, 시스템의 평온과 연속성을 수호합니다.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import MonitorJob, SchedulerStatus
from .pipeline import run_monitoring_pipeline


class IRSMonitorScheduler:
    """IRS Monitor 스케줄러 (Facade)."""

    def __init__(self, crawler=None, auto_updater=None, notification_manager=None) -> None:
        self.crawler = crawler
        self.auto_updater = auto_updater
        self.notification_manager = notification_manager
        self.jobs: dict[str, MonitorJob] = {}
        self.status = SchedulerStatus.STOPPED
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """스케줄러 시작."""
        self.status = SchedulerStatus.RUNNING
        self.logger.info("IRS Monitor Scheduler started.")

    async def stop(self):
        """스케줄러 정지."""
        self.status = SchedulerStatus.STOPPED
        self.logger.info("IRS Monitor Scheduler stopped.")

    def add_job(self, document_id: str, interval_hours: int = 24) -> str:
        """모니터링 작업 추가."""
        job_id = f"JOB-{document_id}-{datetime.now().timestamp()}"
        job = MonitorJob(job_id=job_id, document_id=document_id, interval_hours=interval_hours)
        self.jobs[job_id] = job
        return job_id

    async def trigger_job(self, job_id: str):
        """특정 작업을 즉시 실행."""
        job = self.jobs.get(job_id)
        if not job:
            return

        result = await run_monitoring_pipeline(
            job.document_id,
            self.crawler,
            self.auto_updater,
            None,  # integrator placeholder
        )

        job.last_run = datetime.now().isoformat()
        job.last_status = result["status"]
        return result

    def get_scheduler_status(self) -> dict[str, Any]:
        """스케줄러 전체 상태 요약 반환."""
        return {
            "status": self.status.value,
            "total_jobs": len(self.jobs),
            "active_jobs": len([j for j in self.jobs.values() if j.last_status == "success"]),
            "failed_jobs": len([j for j in self.jobs.values() if j.last_status == "error"]),
            "timestamp": datetime.now().isoformat(),
        }


__all__ = ["IRSMonitorScheduler", "MonitorJob", "SchedulerStatus"]
