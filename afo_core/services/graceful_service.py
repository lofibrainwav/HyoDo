# Trinity Score: 90.0 (Established by Chancellor)
# packages/afo-core/services/graceful_service.py
# (Graceful Degradation 구현 - PDF 에러 처리 기반)
# 🧭 Trinity Score: 眞95% 善99% 美85% 孝99%

import logging
from typing import Any

from AFO.utils.trinity_type_validator import validate_with_trinity

logger = logging.getLogger(__name__)


class GracefulService:
    """
    Graceful Degradation: 점진적 기능 저하 우아함 (PDF 안정성 25/25)

    Ensures that core functionality remains available even when optional components fail.
    Implements the 'Fail Safe' and 'Degrade Gracefully' patterns.
    """

    def __init__(self, dry_run: bool = False) -> None:
        self.core_functional = True  # 핵심 기능 상태
        self.dry_run = dry_run

    @validate_with_trinity
    def execute_core(self, query: str) -> str:
        """
        핵심 기능: 형님 쿼리 응답 (항상 유지)
        Must never fail if at all possible.
        """
        # In a real scenario, this might be a DB query or basic echo
        return f"핵심 응답 (Core Response): {query}"

    @validate_with_trinity
    def execute_optional(self, feature: str) -> str | None:
        """
        선택 기능: 실패 시 폴백 (Graceful Degradation)
        """
        try:
            # Simulate failure in DRY_RUN or if flagged
            if self.dry_run and feature == "risky_operation":
                raise RuntimeError("DRY_RUN: Risky operation simulated failure")

            # Logic for optional feature would go here
            return f"선택 기능 {feature} 실행 성공"

        except Exception as e:
            # Log failure but return None to signal degradation
            logger.warning(
                f"[Graceful Degradation] 선택 기능 저하 ({feature}): {e} - 핵심 기능 유지"
            )
            return None  # 폴백: None 반환 (점진적 저하)

    @validate_with_trinity
    def handle_query(self, query: str, optional_features: list[str]) -> dict[str, Any]:
        """
        통합 실행: 핵심 + 선택 기능 (형님 평온 100%)
        """
        # 1. Execute Core (Unprotected - let it bubble if critical, or wrap if even core needs fallback)
        try:
            core_result = self.execute_core(query)
        except Exception as e:
            logger.error(f"[CRITICAL] Core function failed: {e}")
            core_result = "SYSTEM ERROR - Core Functionality Compromised"
            self.core_functional = False

        # 2. Execute Optionals (Protected)
        optional_results = [self.execute_optional(f) for f in optional_features]

        # 3. Determine Status
        degraded = (
            any(r is None for r in optional_results if r is not None) or not self.core_functional
        )
        status = "Degraded Mode" if degraded else "Full Mode"

        logger.info(
            f"[Graceful Degradation] 상태: {status} - 핵심 기능: {'정상' if self.core_functional else '실패'}"
        )

        return {
            "core": core_result,
            "optional": optional_results,
            "status": status,
            "metadata": {
                "philosophy": "善 (Goodness) - Harm Minimization",
                "strategy": "Graceful Degradation",
            },
        }


# Singleton instance access pattern
_instance = None


def get_graceful_service() -> GracefulService:
    global _instance
    if _instance is None:
        _instance = GracefulService()
    return _instance
