"""IRS Monitor Router (Phase 78)

IRS 변경 자동 감지 및 적용 API 엔드포인트
TICKET: IRS 변경 자동 감지 및 적용

Features:
- IRS 변경 감지 상태 조회
- 수동 변경 감지 트리거
- 변경 히스토리 조회
- Auto-updater 트리거 (DRY_RUN 기본)
"""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from AFO.utils.standard_shield import shield

router = APIRouter(prefix="/irs", tags=["IRS Monitor"])

logger = logging.getLogger(__name__)

# Global service instance (lazy init)
_irs_service: Any = None
_auto_updater: Any = None


def get_irs_service() -> Any:
    """Lazy load IRS Monitor Service"""
    global _irs_service
    if _irs_service is None:
        try:
            from services.irs_monitor_service import IRSMonitorService

            _irs_service = IRSMonitorService(dry_run=True, mock_mode=False)
            logger.info("IRSMonitorService initialized (DRY_RUN=True)")
        except ImportError as e:
            logger.warning(f"IRSMonitorService not available: {e}")
            _irs_service = None
    return _irs_service


def get_auto_updater() -> Any:
    """Lazy load IRS Auto Updater"""
    global _auto_updater
    if _auto_updater is None:
        try:
            from AFO.irs.auto_updater import IRSAutoUpdater

            _auto_updater = IRSAutoUpdater()
            logger.info("IRSAutoUpdater initialized")
        except ImportError as e:
            logger.warning(f"IRSAutoUpdater not available: {e}")
            _auto_updater = None
    return _auto_updater


class CheckRequest(BaseModel):
    """변경 감지 요청"""

    mock_mode: bool = False
    force: bool = False


class UpdateRequest(BaseModel):
    """SSOT 업데이트 요청"""

    document_id: str
    dry_run: bool = True
    min_trinity_score: float = 0.90


@shield(pillar="善", log_error=True)
@router.get("/status")
async def get_irs_status() -> dict[str, Any]:
    """IRS 모니터링 상태 조회"""
    service = get_irs_service()

    if service is None:
        return {
            "status": "unavailable",
            "message": "IRSMonitorService not initialized",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    return {
        "status": "active" if service._is_running else "idle",
        "dry_run": service.dry_run,
        "mock_mode": service.mock_mode,
        "detected_changes_count": len(service.detected_changes),
        "listeners_count": len(service.listeners),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@shield(pillar="眞", log_error=True)
@router.get("/changes")
async def get_detected_changes() -> dict[str, Any]:
    """감지된 변경 사항 목록 조회"""
    service = get_irs_service()

    if service is None:
        return {
            "changes": [],
            "count": 0,
            "message": "Service not available",
        }

    changes = []
    for change in service.detected_changes[-50:]:  # 최근 50개
        changes.append(
            {
                "id": str(change.change_id) if hasattr(change, "change_id") else "unknown",
                "change_type": change.change_type.value
                if hasattr(change, "change_type")
                else "unknown",
                "detected_at": change.detected_at.isoformat()
                if hasattr(change, "detected_at")
                else None,
                "summary": change.summary if hasattr(change, "summary") else str(change),
            }
        )

    return {
        "changes": changes,
        "count": len(changes),
        "total": len(service.detected_changes),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@shield(pillar="眞", log_error=True)
@router.post("/check")
async def trigger_check(
    request: CheckRequest,
) -> dict[str, Any]:
    """수동 변경 감지 트리거"""
    service = get_irs_service()

    if service is None:
        raise HTTPException(status_code=503, detail="IRSMonitorService not available")

    # Mock 모드 일시 변경
    original_mock = service.mock_mode
    if request.mock_mode:
        service.mock_mode = True

    try:
        changes = await service.check_for_updates()

        return {
            "triggered": True,
            "changes_detected": len(changes),
            "changes": [
                {
                    "id": str(c.change_id) if hasattr(c, "change_id") else "unknown",
                    "type": c.change_type.value if hasattr(c, "change_type") else "unknown",
                }
                for c in changes
            ],
            "mock_mode": request.mock_mode,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    finally:
        service.mock_mode = original_mock


@shield(pillar="善", log_error=True)
@router.post("/start")
async def start_monitoring(interval_seconds: int = 300) -> dict[str, Any]:
    """모니터링 시작"""
    service = get_irs_service()

    if service is None:
        raise HTTPException(status_code=503, detail="IRSMonitorService not available")

    if service._is_running:
        return {
            "status": "already_running",
            "message": "Monitoring is already active",
        }

    await service.start(interval_seconds=interval_seconds)

    return {
        "status": "started",
        "interval_seconds": interval_seconds,
        "dry_run": service.dry_run,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@shield(pillar="善", log_error=True)
@router.post("/stop")
async def stop_monitoring() -> dict[str, Any]:
    """모니터링 중지"""
    service = get_irs_service()

    if service is None:
        raise HTTPException(status_code=503, detail="IRSMonitorService not available")

    await service.stop()

    return {
        "status": "stopped",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@shield(pillar="眞", log_error=True)
@router.get("/config")
async def get_irs_config() -> dict[str, Any]:
    """IRS 모니터링 설정 조회"""
    try:
        from AFO.irs.irs_config import get_irs_config as get_config

        config = get_config()
        return {
            "critical_interval_hours": config.critical_interval_hours,
            "regular_interval_hours": config.regular_interval_hours,
            "hash_algorithm": config.hash_algorithm,
            "critical_documents": list(config.critical_documents.keys()),
            "regular_documents": list(config.regular_documents.keys()),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except ImportError:
        return {
            "status": "config_unavailable",
            "message": "IRS config module not found",
        }


@shield(pillar="永", log_error=True)
@router.get("/history")
async def get_update_history(limit: int = 20) -> dict[str, Any]:
    """SSOT 업데이트 히스토리 조회"""
    updater = get_auto_updater()

    if updater is None:
        return {
            "history": [],
            "message": "AutoUpdater not available",
        }

    try:
        history = updater.get_version_history(limit=limit)
        return {
            "history": history,
            "count": len(history),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return {
            "history": [],
            "error": str(e),
        }


@shield(pillar="眞", log_error=True)
@router.post("/update")
async def trigger_ssot_update(request: UpdateRequest) -> dict[str, Any]:
    """SSOT 업데이트 트리거 (DRY_RUN 기본)"""
    updater = get_auto_updater()

    if updater is None:
        raise HTTPException(status_code=503, detail="IRSAutoUpdater not available")

    if not request.dry_run:
        # WET RUN은 추가 검증 필요
        raise HTTPException(
            status_code=403,
            detail="WET_RUN requires explicit Commander approval. Use dry_run=true first.",
        )

    try:
        result = await updater.process_update(
            document_id=request.document_id,
            dry_run=request.dry_run,
            min_trinity_score=request.min_trinity_score,
        )

        return {
            "status": "completed" if result else "no_changes",
            "document_id": request.document_id,
            "dry_run": request.dry_run,
            "trinity_gate": request.min_trinity_score,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
