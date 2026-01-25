"""E2E Simulation Engine.

전체 테스트 케이스를 오케스트레이션하고 요약 결과를 생성하는 엔진.
"""

from __future__ import annotations

from typing import Any

from .scenarios import (
    test_change_detection,
    test_rollback,
    test_ssot_update,
    test_trinity_evaluation,
)
from .utils import log_test_result, setup_simulation_paths


class E2ESimulator:
    """IRS Monitor Agent 전체 시스템 시뮬레이터."""

    def __init__(self) -> None:
        self.paths = setup_simulation_paths()
        self.results = []

    async def run_all_tests(self) -> dict[str, Any]:
        """모든 정의된 테스트 케이스를 실행합니다."""
        # 1. Change Detection
        res1 = await test_change_detection()
        self.results.append(res1)
        log_test_result("Change Detection", res1["status"], res1["details"])

        # 2. Trinity Evaluation
        res2 = await test_trinity_evaluation()
        self.results.append(res2)
        log_test_result("Trinity Evaluation", res2["status"], res2["details"])

        # 3. SSOT Update
        res3 = await test_ssot_update()
        self.results.append(res3)
        log_test_result("SSOT Update", res3["status"], res3["details"])

        # 5. Rollback
        res5 = await test_rollback()
        self.results.append(res5)
        log_test_result("Rollback", res5["status"], res5["details"])

        passed = len([r for r in self.results if r["status"] == "passed"])

        return {
            "total_tests": len(self.results),
            "passed_tests": passed,
            "failed_tests": len(self.results) - passed,
            "results": self.results,
        }
