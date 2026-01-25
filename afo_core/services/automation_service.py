from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from AFO.utils.automation_tools import AutomationTools
from AFO.utils.path_utils import get_project_root

# Trinity Score: 95.0 (Automation Service Optimization)
"""
Automation Service with Intelligent Caching

AFO 왕국 철학 준수 최적화:
- 眞(Truth): 성능 측정 기반 캐싱 전략
- 善(Goodness): 안정성 우선, 예외 처리 강화
- 美(Beauty): 클린 코드, 모듈화
- 孝(Serenity): 유지보수성, 디버깅 용이성
- 永(Eternity): 확장성, 미래 호환성

Context7 최적화와 동일한 패턴 적용으로 API 성능 50% 향상 목표
"""


logger = logging.getLogger(__name__)

# 모듈 레벨 캐싱 (싱글톤 패턴)
_automation_cache: dict[str, Any] | None = None
_automation_cache_timestamp: float = 0
_AUTOMATION_CACHE_TTL = 300  # 5분 캐시 (자동화 도구는 자주 변경되지 않음)


def get_automation_health() -> dict[str, Any]:
    """
    AutomationTools 건강 상태 캐싱 및 반환

    Returns:
        건강 상태 딕셔너리
    """
    global _automation_cache, _automation_cache_timestamp

    current_time = time.time()

    # 캐시 유효성 확인
    if (
        _automation_cache is None
        or (current_time - _automation_cache_timestamp) > _AUTOMATION_CACHE_TTL
    ):
        try:
            logger.debug("🔄 AutomationTools 캐시 갱신 시작")

            # 프로젝트 루트 계산
            project_root = get_project_root(
                Path(__file__).parent.parent.parent / "api" / "routes" / "comprehensive_health.py"
            )

            # AutomationTools 실행
            automation = AutomationTools(project_root)
            tools_status = automation.get_tools_status()
            score = automation.get_automation_score()

            # 캐시 업데이트
            _automation_cache = {
                "status": "healthy" if score >= 70.0 else "warning",
                "score": round(score, 1),
                "details": tools_status,
                "cached_at": current_time,
                "cache_hit": False,
            }
            _automation_cache_timestamp = current_time

            logger.debug("✅ AutomationTools 캐시 갱신 완료")

        except Exception as e:
            error_msg = f"AutomationTools 캐시 갱신 실패: {e}"
            logger.warning(error_msg)

            _automation_cache = {
                "status": "error",
                "error": str(e),
                "cached_at": current_time,
                "cache_hit": False,
            }
            _automation_cache_timestamp = current_time

    else:
        # 캐시 히트 표시
        _automation_cache["cache_hit"] = True
        logger.debug("✅ AutomationTools 캐시 히트")

    # 캐시 복사본 반환 (외부 수정 방지)
    result = _automation_cache.copy()
    result["response_time"] = time.time() - current_time

    return result


def reset_automation_cache() -> None:
    """
    Automation 캐시 리셋 (디버깅/테스트용)

    Trinity Score: 孝 (Serenity) - 디버깅 편의성 제공
    """
    global _automation_cache, _automation_cache_timestamp

    _automation_cache = None
    _automation_cache_timestamp = 0

    logger.info("🔄 Automation 캐시 리셋 완료")


# 초기화 시점 로깅
logger.debug("Automation Service 모듈 로드 완료 - 5분 TTL 캐싱 준비됨")
