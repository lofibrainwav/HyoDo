# Trinity Score: 90.0 (Established by Chancellor)
"""AICPA Tax Engine - 2025 OBBBA 세법 계산

眞 (Truth): IRS 공식 세법 기반 정밀 계산
善 (Goodness): 절세 최적화 전략 제공
永 (Eternity): 장기 부의 증식 (Roth Ladder)

참조: IRS 2025 Tax Brackets + OBBBA 조항
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FilingStatus(Enum):
    SINGLE = "single"
    MFJ = "mfj"  # Married Filing Jointly
    MFS = "mfs"  # Married Filing Separately
    HOH = "hoh"  # Head of Household


# =============================================================================
# 2025 OBBBA Federal Tax Brackets (IRS 기준)
# =============================================================================

FEDERAL_BRACKETS_2025 = {
    FilingStatus.MFJ: [
        (23200, 0.10),  # 10% 구간
        (94300, 0.12),  # 12% 구간 ← OBBBA Sweet Spot!
        (201050, 0.22),  # 22% 구간
        (383900, 0.24),  # 24% 구간
        (487450, 0.32),  # 32% 구간
        (731200, 0.35),  # 35% 구간
        (float("inf"), 0.37),  # 37% 구간
    ],
    FilingStatus.SINGLE: [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (609350, 0.35),
        (float("inf"), 0.37),
    ],
    FilingStatus.HOH: [
        (16550, 0.10),
        (63100, 0.12),
        (100500, 0.22),
        (191950, 0.24),
        (243700, 0.32),
        (609350, 0.35),
        (float("inf"), 0.37),
    ],
}

# 2025 Standard Deductions (OBBBA 증가분 반영)
STANDARD_DEDUCTION_2025 = {
    FilingStatus.MFJ: 31500,  # OBBBA로 상향
    FilingStatus.SINGLE: 15750,
    FilingStatus.HOH: 23625,
}

# California State Tax Brackets (2025)
CA_BRACKETS_2025 = [
    (10412, 0.01),
    (24684, 0.02),
    (38959, 0.04),
    (54081, 0.06),
    (68350, 0.08),
    (349137, 0.093),
    (418961, 0.103),
    (698271, 0.113),
    (float("inf"), 0.123),
]

# IRMAA Thresholds 2025 (Medicare Part B Premium Surcharge)
IRMAA_THRESHOLDS_2025 = {
    FilingStatus.SINGLE: [103000, 129000, 161000, 193000, 500000],
    FilingStatus.MFJ: [206000, 258000, 322000, 386000, 750000],
}


@dataclass
class TaxInput:
    """세금 계산 입력 데이터"""

    filing_status: FilingStatus
    gross_income: int
    traditional_ira_balance: int = 0
    roth_conversion_amount: int = 0
    other_deductions: int = 0
    state: str = "CA"


@dataclass
class TaxResult:
    """세금 계산 결과"""

    # 입력값
    filing_status: str
    gross_income: int
    taxable_income: int

    # 연방세
    federal_tax: int
    effective_federal_rate: float
    marginal_bracket: float

    # 주세
    state_tax: int

    # 총합
    total_tax: int
    after_tax_income: int

    # OBBBA 분석
    sweet_spot_headroom: int  # 12% 구간까지 여유
    roth_conversion_recommendation: int

    # 리스크
    irmaa_warning: bool
    irmaa_tier: int | None = None

    # 제안
    advice: str = ""


def calculate_federal_tax(taxable_income: int, filing_status: FilingStatus) -> tuple[int, float]:
    """연방세 계산"""
    try:
        brackets = FEDERAL_BRACKETS_2025[filing_status]
        tax: float = 0
        prev_threshold: float = 0
        marginal_rate: float = 0.10

        for threshold, rate in brackets:
            if taxable_income <= threshold:
                tax += (taxable_income - prev_threshold) * rate
                marginal_rate = rate
                break
            else:
                tax += (threshold - prev_threshold) * rate
                prev_threshold = threshold
                marginal_rate = rate

        return int(tax), marginal_rate
    except Exception:
        return 0, 0.10


def calculate_ca_state_tax(taxable_income: int) -> int:
    """예리포니아 주세 계산"""
    try:
        tax: float = 0
        prev_threshold: float = 0

        for threshold, rate in CA_BRACKETS_2025:
            if taxable_income <= threshold:
                tax += (taxable_income - prev_threshold) * rate
                break
            else:
                tax += (threshold - prev_threshold) * rate
                prev_threshold = threshold

        return int(tax)
    except Exception:
        return 0


def check_irmaa_risk(magi: int, filing_status: FilingStatus) -> tuple[bool, int | None]:
    """IRMAA 리스크 체크"""
    try:
        thresholds = IRMAA_THRESHOLDS_2025[filing_status]

        for i, threshold in enumerate(thresholds):
            if magi <= threshold:
                if i == 0:
                    return False, None
                return True, i

        return True, len(thresholds)
    except Exception:
        return False, None


def calculate_obbba_sweet_spot(taxable_income: int, filing_status: FilingStatus) -> int:
    """OBBBA Sweet Spot 계산"""
    try:
        if filing_status == FilingStatus.MFJ:
            sweet_spot_ceiling = 94300
        elif filing_status == FilingStatus.SINGLE:
            sweet_spot_ceiling = 47150
        else:
            sweet_spot_ceiling = 63100

        headroom = sweet_spot_ceiling - taxable_income
        return max(0, headroom)
    except Exception:
        return 0


def calculate_tax(input_data: TaxInput) -> TaxResult:
    """종합 세금 계산"""
    try:
        # 1. 과세 소득 계산
        standard_deduction = STANDARD_DEDUCTION_2025[input_data.filing_status]
        taxable_income = max(
            0,
            input_data.gross_income
            + input_data.roth_conversion_amount
            - standard_deduction
            - input_data.other_deductions,
        )

        # 2. 연방세 계산
        federal_tax, marginal_rate = calculate_federal_tax(taxable_income, input_data.filing_status)
        effective_rate = federal_tax / taxable_income if taxable_income > 0 else 0

        # 3. 주세 계산
        state_tax = 0
        if input_data.state == "CA":
            state_tax = calculate_ca_state_tax(taxable_income)

        # 4. 총 세금
        total_tax = federal_tax + state_tax
        after_tax = input_data.gross_income - total_tax

        # 5. OBBBA Sweet Spot 분석
        sweet_spot_headroom = calculate_obbba_sweet_spot(taxable_income, input_data.filing_status)

        # Roth Conversion 추천: Sweet Spot 여유분까지
        roth_recommendation = min(sweet_spot_headroom, input_data.traditional_ira_balance)

        # 6. IRMAA 리스크 체크
        magi = input_data.gross_income + input_data.roth_conversion_amount
        irmaa_warning, irmaa_tier = check_irmaa_risk(magi, input_data.filing_status)

        # 7. 조언 생성
        advice = generate_advice(
            marginal_rate,
            sweet_spot_headroom,
            roth_recommendation,
            irmaa_warning,
            input_data.traditional_ira_balance,
        )

        logger.info(
            f"[TaxEngine] 계산 완료: Income=${input_data.gross_income:,}, Tax=${total_tax:,}"
        )

        return TaxResult(
            filing_status=input_data.filing_status.value,
            gross_income=input_data.gross_income,
            taxable_income=taxable_income,
            federal_tax=federal_tax,
            effective_federal_rate=round(effective_rate * 100, 2),
            marginal_bracket=marginal_rate,
            state_tax=state_tax,
            total_tax=total_tax,
            after_tax_income=after_tax,
            sweet_spot_headroom=sweet_spot_headroom,
            roth_conversion_recommendation=roth_recommendation,
            irmaa_warning=irmaa_warning,
            irmaa_tier=irmaa_tier,
            advice=advice,
        )
    except Exception as e:
        logger.error(f"[TaxEngine] 계산 실패: {e!s}")
        # Provide a fallback TaxResult instead of raising, or re-raise if fatal
        raise


def generate_advice(
    marginal_rate: float, headroom: int, roth_rec: int, irmaa: bool, ira_balance: int
) -> str:
    """Julie CPA 스타일의 조언 생성"""
    try:
        advice_parts = []

        # 1. Sweet Spot 활용
        if marginal_rate <= 0.12 and headroom > 0:
            advice_parts.append(
                f"✨ OBBBA Sweet Spot 활용 가능! 12% 구간까지 ${headroom:,} 여유가 있습니다."
            )

        # 2. Roth Conversion 추천
        if roth_rec > 0 and ira_balance > 0:
            advice_parts.append(
                f"💰 Roth Conversion 추천: ${roth_rec:,} 변환 시 "
                f"저세율(12%) 혜택을 최대로 활용할 수 있습니다."
            )

        # 3. IRMAA 경고
        if irmaa:
            advice_parts.append(
                "⚠️ IRMAA 주의: 현재 소득 수준에서 Medicare 프리미엄 "
                "과부담이 발생할 수 있습니다. 소득 조절을 고려하세요."
            )

        # 4. 기본 조언
        if not advice_parts:
            advice_parts.append(
                "📊 현재 세금 상태는 안정적입니다. "
                "추가 절세 전략이 필요하시면 Julie CPA에게 문의하세요."
            )

        return " | ".join(advice_parts)
    except Exception:
        return "📊 절세 전략 로우딩 중..."


# =============================================================================
# Roth Ladder 시뮬레이터
# =============================================================================


def simulate_roth_ladder(
    ira_balance: int, filing_status: FilingStatus, current_income: int, years: int = 5
) -> dict:
    """다년간 Roth Ladder 시뮬레이션"""
    try:
        results = []
        remaining_ira = ira_balance

        for year in range(years):
            if remaining_ira <= 0:
                break

            # 해당 연도 Sweet Spot 계산
            input_data = TaxInput(
                filing_status=filing_status,
                gross_income=current_income,
                traditional_ira_balance=remaining_ira,
            )

            tax_result = calculate_tax(input_data)
            optimal_conversion = min(tax_result.sweet_spot_headroom, remaining_ira)

            # 변환 시 세금
            conversion_tax = int(optimal_conversion * tax_result.marginal_bracket)

            results.append(
                {
                    "year": 2025 + year,
                    "conversion_amount": optimal_conversion,
                    "tax_paid": conversion_tax,
                    "remaining_ira": remaining_ira - optimal_conversion,
                    "marginal_rate": tax_result.marginal_bracket,
                }
            )

            remaining_ira -= optimal_conversion

        # 총 절세액 계산 (vs 일괄 변환)
        total_paid = sum(r["tax_paid"] for r in results)
        one_time_tax = int(ira_balance * 0.22)  # 22% 구간 가정
        savings = one_time_tax - total_paid

        logger.info(f"[RothLadder] 시뮬레이션 완료: {len(results)}년, 절세 ${savings:,}")

        return {
            "strategy": "Roth Ladder",
            "years": results,
            "total_converted": ira_balance - remaining_ira,
            "total_tax_paid": total_paid,
            "estimated_savings": savings,
            "summary": f"OBBBA 기간 활용 시 약 ${savings:,} 절세 예상",
        }
    except Exception as e:
        return {"error": str(e), "strategy": "Roth Ladder", "years": []}
