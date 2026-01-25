from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

# Trinity Score: 90.0 (Established by Chancellor)
"""Automation Tools Utilities (야전교범 원칙 준수)
眞善美孝永 철학에 기반한 자동화 도구 통합

眞 (Truth): 정확한 코드 품질 검증
善 (Goodness): 안전한 자동화 프로세스
美 (Beauty): 우아한 자동화 워크플로우
孝 (Serenity): 개발자 경험 최적화
永 (Eternity): 지속 가능한 자동화 시스템
"""


logger = logging.getLogger(__name__)


class AutomationTools:
    """자동화 도구 관리 클래스"""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path.cwd()
        self.tools_status: dict[str, bool] = {}

    def check_tool_available(self, tool_name: str) -> bool:
        """도구 사용 가능 여부 확인"""
        try:
            result = subprocess.run(
                [tool_name, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            available = result.returncode == 0
            self.tools_status[tool_name] = available
            return available
        except Exception as e:
            logger.warning(f"Tool {tool_name} check failed: {e}")
            self.tools_status[tool_name] = False
            return False

    def get_automation_score(self) -> float:
        """자동화 도구 점수 계산 (孝 - Serenity)

        Returns:
            0.0 ~ 100.0 점수

        """
        tools = {
            "black": "코드 포맷팅",
            "isort": "Import 정렬",
            "ruff": "린팅",
            "mypy": "타입 체킹",
            "pytest": "테스트",
            "pre-commit": "Pre-commit 훅",
        }

        available_count = 0
        for tool in tools:
            if self.check_tool_available(tool):
                available_count += 1

        score = (available_count / len(tools)) * 100.0
        return round(score, 1)

    def run_pre_commit(self) -> dict[str, Any]:
        """Pre-commit 실행"""
        try:
            result = subprocess.run(
                ["pre-commit", "run", "--all-files"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }
        except Exception as e:
            logger.error(f"Pre-commit execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_tools_status(self) -> dict[str, Any]:
        """모든 도구 상태 반환"""
        return {
            "tools": self.tools_status,
            "automation_score": self.get_automation_score(),
        }
