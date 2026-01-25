"""IRS Monitoring Pipeline.

문서 하나를 대상으로 크롤링부터 알림까지 이어지는 전체 모니터링 파이프라인.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def run_monitoring_pipeline(
    document_id: str, crawler: Any, updater: Any, integrator: Any, _gate: Any = None
) -> dict[str, Any]:
    """단일 문서에 대해 전체 모니터링 프로세스를 실행합니다."""
    logger.info(f"Starting pipeline for document: {document_id}")

    try:
        # 1. 크롤링 (Crawling)
        crawl_result = await crawler.crawl(document_id)
        if not crawl_result.get("changed"):
            return {"status": "unchanged", "document_id": document_id}

        # 2. 분석 및 SSOT 업데이트 (Analyze & Update)
        update_result = await updater.update(crawl_result)

        # 3. 게이트 평가 (Trinity Gate)
        # 4. 알림 생성 및 전송 (Notify)
        if integrator:
            await integrator.create_and_send_alert(
                change=update_result.get("change"),
                parameters=update_result.get("parameters"),
                trinity_score=update_result.get("trinity_score"),
                gate_result=update_result.get("gate_result"),
            )

        return {"status": "success", "document_id": document_id, "change_detected": True}
    except Exception as e:
        logger.error(f"Pipeline failed for {document_id}: {e!s}")
        return {"status": "error", "error": str(e)}
