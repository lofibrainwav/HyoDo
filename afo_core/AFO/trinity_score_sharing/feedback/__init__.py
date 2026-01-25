"""Trinity Score Sharing Feedback

피드백 루프 및 동적 최적화 함수들.
"""

import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def cleanup_expired_feedback_loops(
    feedback_tasks: dict[str, asyncio.Task], sharing_stats: dict[str, int]
):
    """만료된 피드백 루프 정리"""

    while True:
        try:
            # 완료된 태스크 정리
            expired_tasks = [name for name, task in feedback_tasks.items() if task.done()]

            for task_name in expired_tasks:
                del feedback_tasks[task_name]

            # 통계 업데이트
            sharing_stats["feedback_loops_active"] = len(feedback_tasks)

            # 5분마다 정리
            await asyncio.sleep(300)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in feedback loop cleanup: {e}")
            await asyncio.sleep(60)


def generate_adjustment_reason(adjustment: float, context: dict[str, Any]) -> str:
    """조정 이유 생성"""

    if adjustment > 0.05:
        return "Strong collaborative performance boost"
    elif adjustment > 0.01:
        return "Moderate collaboration enhancement"
    elif adjustment < -0.05:
        return "Score alignment for better consensus"
    elif adjustment < -0.01:
        return "Minor consensus adjustment"
    else:
        return "Score maintained at optimal level"


def should_optimize_scores(
    session_id: str,
    score_pools: dict[str, dict[str, float]],
    score_history: dict[str, list],
    _datetime_module,
) -> bool:
    """점수 최적화 필요 여부 판단"""

    if session_id not in score_pools:
        return False

    scores = score_pools[session_id]
    history = score_history.get(session_id, [])

    # 최소 조건 체크
    if len(scores) < 2:
        return False  # 최소 2개 에이전트 필요

    if len(history) < 5:
        return False  # 최소 5개 업데이트 필요

    # 최근 업데이트 확인 (1시간 이내)
    from datetime import datetime

    recent_updates = [
        update
        for update in history
        if (datetime.now() - datetime.fromisoformat(update.timestamp)).seconds < 3600
    ]

    return len(recent_updates) >= 3  # 최근 3개 업데이트 필요
