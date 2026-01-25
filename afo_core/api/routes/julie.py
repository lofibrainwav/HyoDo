"""
Julie CPA API Routes
TICKET-042: Professional Tax Calculation Services

FastAPI endpoints for Julie CPA Engine:
- /api/julie/depreciation: 감가상각 계산
- Trinity Score 기반 검증
- Evidence Bundle 자동 생성

SSOT Integration: IRS/FTB 실시간 동기화 (TICKET-033)
"""

import logging

from fastapi import APIRouter, BackgroundTasks

from AFO.julie import DepInput, DepOutput, julie_depreciation_calc
from AFO.utils.standard_shield import shield

# Configure logging
logger = logging.getLogger(__name__)

# Create router
julie_router = APIRouter(
    prefix="/julie",
    tags=["julie-cpa"],
)


@julie_router.post(
    "/depreciation",
    response_model=DepOutput,
    summary="감가상각 계산",
    description="""
    Julie CPA 감가상각 계산기 - OBBBA 2025/2026 §179 + Bonus Depreciation
    """,
    response_description="감가상각 계산 결과 및 Trinity Score",
)
@shield(pillar="善", reraise=True)
async def calculate_depreciation(
    input_data: DepInput, background_tasks: BackgroundTasks
) -> DepOutput:
    """
    감가상각 계산 API
    """
    logger.info(f"Starting depreciation calculation for cost: ${input_data.total_cost:,.0f}")

    # Julie CPA 계산 실행
    result = julie_depreciation_calc(input_data)

    # 백그라운드 로깅 (증거 번들 저장)
    background_tasks.add_task(
        _log_calculation_evidence, input_data.model_dump(), result.model_dump()
    )

    logger.info(
        f"Depreciation calculation completed. Net saving: ${result.net_saving:,.0f}, "
        f"Evidence ID: {result.evidence_id[:8]}..."
    )

    return result


@julie_router.get(
    "/health",
    summary="Julie CPA 엔진 상태 확인",
    description="Julie CPA 엔진의 건강 상태 및 Trinity Score 확인",
)
@shield(pillar="善", default_return={"status": "unhealthy", "engine_version": "1.0.0"})
async def get_julie_health() -> dict[str, str | float | dict | None]:
    """Julie CPA 엔진 건강 상태 확인"""
    # 간단한 계산 테스트로 건강 상태 확인
    test_input = DepInput(total_cost=100000, state="CA", business_income=150000)

    result = julie_depreciation_calc(test_input)

    return {
        "status": "healthy",
        "engine_version": "1.0.0",
        "trinity_score": result.trinity_score,
        "evidence_id": result.evidence_id,
        "test_calculation": {
            "input_cost": 100000,
            "net_saving": result.net_saving,
            "fed_saving": result.fed_saving,
            "ca_addback": result.ca_addback,
        },
    }


async def _log_calculation_evidence(input_data: dict[str, object], result_data: dict[str, object]):
    """계산 증거 로깅 (백그라운드 태스크)"""
    try:
        import json
        from datetime import UTC, datetime
        from pathlib import Path

        # 증거 번들 생성
        evidence_bundle = {
            "timestamp": datetime.now(UTC).isoformat(),
            "ticket": "TICKET-042",
            "input": input_data,
            "output": result_data,
            "evidence_id": result_data.get("evidence_id"),
            "trinity_score": result_data.get("trinity_score"),
        }

        # 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"artifacts/julie_calculation_{timestamp}.json"

        Path("artifacts").mkdir(exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(evidence_bundle, f, indent=2, ensure_ascii=False)

        logger.info(f"Calculation evidence saved: {filename}")

    except Exception as e:
        logger.error(
            f"Failed to log calculation evidence: {e}",
            extra={"pillar": "善", "error_type": type(e).__name__},
        )


# Export router for main API server
__all__ = ["julie_router"]
