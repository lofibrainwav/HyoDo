# Trinity Score: 90.0 (Established by Chancellor)
"""
AICPA API Router - 에이전트 군단 API

AFO Kingdom AICPA 엔드포인트
- /execute: 전체 미션 실행
- /tax-simulate: 세금 시뮬레이션
- /roth-ladder: Roth Ladder 전략
- /generate-report: 보고서 생성

眞善美孝永 영원히!
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from AFO.aicpa import get_aicpa_service
from AFO.utils.standard_shield import shield

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["AICPA Agent Army"])


# =============================================================================
# Request/Response Models
# =============================================================================


class MissionRequest(BaseModel):
    """전체 미션 실행 요청"""

    client_name: str = Field(..., description="고객 이름")
    command: str | None = Field(None, description="추가 명령 (자연어)")


class TaxSimulationRequest(BaseModel):
    """세금 시뮬레이션 요청"""

    filing_status: str = Field("single", description="신고 상태: single, mfj, mfs, hoh")
    gross_income: int = Field(..., description="총소득 (USD)")
    ira_balance: int = Field(0, description="Traditional IRA 잔액")
    roth_conversion: int = Field(0, description="올해 Roth 변환 금액")
    state: str = Field("CA", description="거주 주")


class RothLadderRequest(BaseModel):
    """Roth Ladder 시뮬레이션 요청"""

    ira_balance: int = Field(..., description="Traditional IRA 잔액")
    filing_status: str = Field("single", description="신고 상태")
    current_income: int = Field(..., description="현재 연 소득")
    years: int = Field(4, description="시뮬레이션 기간 (년)")


class ReportRequest(BaseModel):
    """보고서 생성 요청"""

    client_name: str
    include_roth_simulation: bool = Field(True, description="Roth Ladder 분석 포함")


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/execute")
@shield(pillar="善", log_error=True, reraise=False)
async def execute_aicpa_mission(request: MissionRequest) -> dict[str, Any]:
    """
    AICPA 에이전트 군단에게 전체 미션 실행

    1. Data Scouter: 고객 데이터 수집
    2. Tax Calculator: 세금 계산
    3. Strategy Advisor: 전략 수립
    4. Form Filler: 문서 생성

    眞 (Truth): 정확한 세금 계산
    善 (Goodness): 최적의 절세 전략
    孝 (Serenity): 버튼 하나로 모든 작업 완료
    """
    try:
        service = get_aicpa_service()
        result = service.execute_full_mission(request.client_name)

        logger.info(f"[AICPA] Full mission completed for: {request.client_name}")

        return {"success": True, "mission": "complete", **result}

    except Exception as e:
        logger.error(f"[AICPA] Mission failed: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/tax-simulate")
@shield(pillar="善", log_error=True, reraise=False)
async def simulate_tax(request: TaxSimulationRequest) -> dict[str, Any]:
    """
    2025 OBBBA 세금 시뮬레이션

    실시간으로 세금 계산 결과 반환
    - Federal Tax
    - CA State Tax
    - OBBBA Sweet Spot 분석
    - IRMAA 리스크 경고
    """
    try:
        service = get_aicpa_service()

        result = service.calculate_tax_scenario(
            filing_status=request.filing_status,
            gross_income=request.gross_income,
            ira_balance=request.ira_balance,
            roth_conversion=request.roth_conversion,
            state=request.state,
        )

        return {
            "success": True,
            "simulation": result,
            "timestamp": "2025-12-19T13:20:00Z",
        }

    except Exception as e:
        logger.error(f"[AICPA] Tax simulation failed: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/roth-ladder")
@shield(pillar="善", log_error=True, reraise=False)
async def simulate_roth_ladder_strategy(request: RothLadderRequest) -> dict[str, Any]:
    """
    Roth Ladder 전략 시뮬레이션

    OBBBA 기간(2025-2028) 동안 단계적 Roth 변환 전략

    永 (Eternity): 장기 부의 증식
    """
    try:
        service = get_aicpa_service()

        result = service.generate_roth_strategy(
            ira_balance=request.ira_balance,
            filing_status=request.filing_status,
            current_income=request.current_income,
            years=request.years,
        )

        return {
            "success": True,
            "strategy": result,
        }

    except Exception as e:
        logger.error(f"[AICPA] Roth Ladder simulation failed: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/generate-report")
@shield(pillar="善", log_error=True, reraise=False)
async def generate_client_report(request: ReportRequest) -> dict[str, Any]:
    """
    클라이언트 보고서 생성

    - Word 전략 보고서 (.docx)
    - TurboTax 입력 CSV
    - QuickBooks 트랜잭션 CSV
    - 이메일 초안

    美 (Beauty): 전문적인 문서 생성
    """
    try:
        service = get_aicpa_service()

        # 먼저 세금 계산
        client_data = service.get_client_data(request.client_name)
        tax_result = service.calculate_tax_scenario(
            filing_status=client_data.get("filing_status", "single"),
            gross_income=client_data.get("gross_income", 100000),
            ira_balance=client_data.get("traditional_ira_balance", 0),
        )

        # Roth 시뮬레이션 (옵션)
        roth_sim = None
        if request.include_roth_simulation and client_data.get("traditional_ira_balance", 0) > 0:
            roth_sim = service.generate_roth_strategy(
                ira_balance=client_data.get("traditional_ira_balance", 0),
                filing_status=client_data.get("filing_status", "single"),
                current_income=client_data.get("gross_income", 100000),
            )

        # 문서 생성
        documents = service.generate_all_documents(
            client_name=request.client_name,
            tax_result=tax_result,
        )

        return {
            "success": True,
            "generated_files": documents,
            "client": request.client_name,
        }

    except Exception as e:
        logger.error(f"[AICPA] Report generation failed: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/client/{client_name}")
@shield(pillar="善", log_error=True, reraise=False)
async def get_client_data(client_name: str) -> dict[str, Any]:
    """
    고객 데이터 조회

    현재: Mock 데이터
    추후: Google Sheets API 연동
    """
    try:
        service = get_aicpa_service()
        client = service.get_client_data(client_name)

        return {
            "success": True,
            "client": client,
        }

    except Exception as e:
        logger.error(f"[AICPA] Client lookup failed: {e!s}")
        raise HTTPException(status_code=404, detail=f"Client not found: {client_name}") from e


@router.get("/status")
@shield(pillar="善", log_error=True, reraise=False)
async def get_aicpa_status() -> dict[str, Any]:
    """
    AICPA 에이전트 군단 상태 확인
    """
    return {
        "status": "Online",
        "agents": {
            "data_scouter": "활성화 ✅",
            "tax_calculator": "활성화 ✅",
            "strategy_advisor": "활성화 ✅",
            "form_filler": "활성화 ✅",
        },
        "tax_year": 2025,
        "regulations": "OBBBA",
        "message": "AICPA 에이전트 군단이 형님의 명령을 기다리고 있습니다! ⚔️",
    }
