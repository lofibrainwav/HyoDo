"""세금 계산 API 라우터

SSOT 기반 세금 엔진 API:
- /api/tax/estimate: 세금 추정 엔드포인트
- Trinity Score 기반 정확성 보장
- Evidence Bundle ID를 통한 감사 추적
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from AFO.tax_engine.calculator import PersonFlags, TaxCalculator, TaxInput
from AFO.tax_engine.loader import TaxParameterLoader
from AFO.tax_engine.validator import validate_tax_calculation_result

router = APIRouter()


class TaxEstimateRequest(BaseModel):
    """세금 추정 요청 모델"""

    filing_status: str = Field(
        ...,
        description="신고 상태",
        examples=["SINGLE", "MARRIED_FILING_JOINTLY", "HEAD_OF_HOUSEHOLD"],
    )
    gross_income: float = Field(..., gt=0, description="총 소득", examples=[75000.0])
    adjustments: float = Field(default=0.0, ge=0, description="조정액", examples=[5000.0])
    itemized_deductions: float | None = Field(
        default=None,
        ge=0,
        description="항목별 공제 (없으면 표준공제 자동 적용)",
        examples=[15000.0],
    )

    # 개인 플래그
    is_dependent: bool = Field(default=False, description="부양가족 여부", examples=[False])
    age_65_or_over: bool = Field(
        default=False,
        description="65세 이상 여부 (OBBBA 고령자 공제 적용)",
        examples=[True],
    )
    blind: bool = Field(default=False, description="시각장애인 여부", examples=[False])

    # 배우자 플래그 (기혼 신고 시)
    spouse_age_65_or_over: bool | None = Field(
        default=None, description="배우자 65세 이상 여부", examples=[False]
    )
    spouse_blind: bool | None = Field(
        default=None, description="배우자 시각장애 여부", examples=[False]
    )

    # MAGI (고령자 보너스 공제 계산용)
    magi: float | None = Field(
        default=None,
        ge=0,
        description="Modified AGI (65세 이상 공제 계산용)",
        examples=[75000.0],
    )


class TaxEstimateResponse(BaseModel):
    """세금 추정 응답 모델"""

    federal: dict[str, Any] = Field(..., description="연방 세금 세부 정보")
    california: dict[str, Any] = Field(..., description="캘리포니아 주세 세부 정보")
    total_tax: float = Field(..., description="총 세금 (연방 + CA)")
    effective_rate: float = Field(..., description="유효 세율 (%)")
    evidence_bundle_id: str = Field(..., description="증거 번들 ID (감사 추적용)")
    calculated_at: str = Field(..., description="계산 시각")
    ssot_version: str = Field(..., description="SSOT 버전 정보")
    input_summary: dict[str, Any] = Field(..., description="입력 요약")


@router.post(
    "/estimate",
    response_model=TaxEstimateResponse,
    summary="세금 추정",
    description="""
    SSOT 기반 2025년 미국 세금 계산 (연방 + 캘리포니아 주세)

    **Trinity Score 보장:**
    - 眞(Truth): IRS/FTB 공식 문서 기반 정확 계산
    - 善(Goodness): OBBBA 준수 최신 세법 적용
    - 美(Beauty): 구조화된 API 응답
    - 孝(Serenity): 명확한 에러 메시지
    - 永(Eternity): Evidence Bundle ID로 계산 결과 추적

    **지원 기능:**
    - 연방 7브라켓 + CA 9브라켓 프로그레시브 세금
    - OBBBA 65세 이상 보너스 공제
    - 의존자/시각장애인 추가 공제
    - 표준공제 vs 항목별 공제 자동 선택
    """,
)
async def estimate_tax(request: TaxEstimateRequest) -> TaxEstimateResponse:
    """
    세금 추정 엔드포인트

    SSOT 기반으로 연방 및 캘리포니아 주세를 계산합니다.
    """
    try:
        # SSOT 파라미터 로드
        loader = TaxParameterLoader()
        params = loader.load_parameters()

        # 계산기 초기화
        calculator = TaxCalculator(params)

        # 요청을 TaxInput으로 변환
        tax_input = TaxInput(
            filing_status=request.filing_status,
            gross_income=request.gross_income,
            adjustments=request.adjustments,
            itemized_deductions=request.itemized_deductions,
            flags=PersonFlags(
                is_dependent=request.is_dependent,
                age_65_or_over=request.age_65_or_over,
                blind=request.blind,
            ),
            spouse_flags=(
                PersonFlags(
                    age_65_or_over=request.spouse_age_65_or_over or False,
                    blind=request.spouse_blind or False,
                )
                if request.filing_status in ("MARRIED_FILING_JOINTLY", "MARRIED_FILING_SEPARATELY")
                else None
            ),
            magi=request.magi,
        )

        # 세금 계산
        result = calculator.calculate_total_tax_2025(tax_input)

        # 계산 결과 검증
        input_data = {
            "gross_income": request.gross_income,
            "filing_status": request.filing_status,
        }
        validate_tax_calculation_result(input_data, result, params)

        # Evidence Bundle ID 생성
        evidence_bundle_id = str(uuid.uuid4())

        # SSOT 버전 정보
        ssot_version = "2025-01-01-OOBBA"

        # 응답 생성
        response = TaxEstimateResponse(
            federal=result["federal"],
            california=result["california"],
            total_tax=result["total_tax"],
            effective_rate=round(result["effective_rate"] * 100, 2),  # %로 변환
            evidence_bundle_id=evidence_bundle_id,
            calculated_at=datetime.now(UTC).isoformat() + "Z",
            ssot_version=ssot_version,
            input_summary=result["input_summary"],
        )

        return response

    except ValueError as e:
        # 검증 에러 (잘못된 입력)
        raise HTTPException(status_code=400, detail=f"입력 검증 오류: {e!s}")
    except Exception as e:
        # 기타 시스템 에러
        raise HTTPException(status_code=500, detail=f"세금 계산 중 오류 발생: {e!s}")
