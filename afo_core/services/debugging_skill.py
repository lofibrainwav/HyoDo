from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..services.automated_debugging_system import AutomatedDebuggingSystem

# Trinity Score: 90.0 (Established by Chancellor)
"""
Automated Debugging Skill
자동화 디버깅 스킬 - Skills Registry에 등록

眞善美孝永 철학에 기반한 디버깅 스킬
"""


logger = logging.getLogger(__name__)


async def execute_automated_debugging(params: dict[str, Any]) -> dict[str, Any]:
    """
    자동화 디버깅 스킬 실행 함수

    Args:
        params: 스킬 파라미터
            - project_root: 프로젝트 루트 경로 (선택적)
            - auto_fix: 자동 수정 여부 (기본값: True)

    Returns:
        디버깅 결과
    """
    try:
        project_root = params.get("project_root")
        project_root = Path(project_root) if project_root else None

        system = AutomatedDebuggingSystem(project_root)
        report = await system.run_full_debugging_cycle()

        return {
            "success": True,
            "report_id": report.report_id,
            "total_errors": report.total_errors,
            "auto_fixed": report.auto_fixed,
            "manual_required": report.manual_required,
            "trinity_score": report.trinity_score,
            "recommendations": report.recommendations,
        }

    except Exception as e:
        logger.error(f"자동화 디버깅 스킬 실행 실패: {e}")
        return {
            "success": False,
            "error": str(e),
        }
