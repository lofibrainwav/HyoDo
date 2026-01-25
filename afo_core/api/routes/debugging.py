from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from AFO.services.automated_debugging_system import (
    AutomatedDebuggingSystem,
    run_automated_debugging,
)

# Trinity Score: 90.0 (Established by Chancellor)
"""
Automated Debugging API Routes
자동화 디버깅 시스템 API 엔드포인트

眞善美孝永 철학에 기반한 디버깅 API
"""


router = APIRouter(prefix="/api/debugging", tags=["Automated Debugging"])

logger = logging.getLogger(__name__)


@router.post("/run")
async def run_debugging() -> dict[str, Any]:
    """
    자동화 디버깅 실행 (Sequential Thinking Phase 7)

    Returns:
        디버깅 리포트
    """
    try:
        logger.info("🏰 자동화 디버깅 시스템 실행 요청")

        report = await run_automated_debugging()

        return {
            "status": "success",
            "report": {
                "report_id": report.report_id,
                "timestamp": report.timestamp.isoformat(),
                "total_errors": report.total_errors,
                "errors_by_severity": report.errors_by_severity,
                "errors_by_category": report.errors_by_category,
                "auto_fixed": report.auto_fixed,
                "manual_required": report.manual_required,
                "trinity_score": report.trinity_score,
                "recommendations": report.recommendations,
                "execution_time": report.execution_time,
            },
        }

    except Exception as e:
        logger.error(f"❌ 디버깅 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/status")
async def get_debugging_status() -> dict[str, Any]:
    """
    디버깅 시스템 상태 조회

    Returns:
        시스템 상태
    """
    try:
        system = AutomatedDebuggingSystem()

        return {
            "status": "ready",
            "project_root": str(system.project_root),
            "components": {
                "error_detector": "ready",
                "error_classifier": "ready",
                "auto_diagnostic": "ready",
                "solution_suggester": "ready",
                "auto_fixer": "ready",
                "debug_tracker": "ready",
            },
        }

    except Exception as e:
        logger.error(f"❌ 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/history")
async def get_debugging_history(limit: int = 10) -> dict[str, Any]:
    """
    디버깅 히스토리 조회

    Args:
        limit: 조회할 최대 개수

    Returns:
        디버깅 히스토리
    """
    try:
        system = AutomatedDebuggingSystem()

        # 추적 데이터 파일 읽기
        tracking_file = (
            system.project_root
            / "logs"
            / f"debug_tracking_{datetime.now().strftime('%Y%m%d')}.json"
        )

        if tracking_file.exists():
            with open(tracking_file, encoding="utf-8") as f:
                tracking_data = json.load(f)

            return {
                "status": "success",
                "total_sessions": len(tracking_data),
                "sessions": tracking_data[-limit:],  # 최근 N개
            }
        else:
            return {
                "status": "success",
                "total_sessions": 0,
                "sessions": [],
            }

    except Exception as e:
        logger.error(f"❌ 히스토리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
