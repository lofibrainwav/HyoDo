from __future__ import annotations

from dataclasses import dataclass
from typing import Any

"""SSOT 기반 세금 계산기 (2025년 미국 세법)

Trinity Score 기반 정확성 검증:
- 眞(Truth): SSOT 문서 기반 정확한 계산 로직
- 善(Goodness): OBBBA 반영 최신 세법 준수
- 美(Beauty): 구조화된 모듈식 설계
- 孝(Serenity): 명확한 에러 메시지와 안전한 계산
- 永(Eternity): SSOT 해시 검증으로 변경 추적

지원 기능:
- 연방 소득세 계산 (7개 브라켓, 표준공제, 항목별 공제)
- 캘리포니아 주세 계산 (9개 브라켓, 주 표준공제)
- 65세 이상 추가 공제 (OBBBA)
- 의존자 표준공제
- 시각장애인 추가 공제
"""


@dataclass(frozen=True)
class PersonFlags:
    """개인 플래그 (나이, 장애 등)"""

    is_dependent: bool = False
    age_65_or_over: bool = False
    blind: bool = False


@dataclass(frozen=True)
class TaxInput:
    """세금 계산 입력 데이터"""

    filing_status: str
    gross_income: float
    adjustments: float = 0.0
    itemized_deductions: float | None = None
    flags: PersonFlags = PersonFlags()
    spouse_flags: PersonFlags | None = None
    magi: float | None = None  # Modified AGI (65세 이상 공제 계산용)


def _progressive_tax(taxable_income: float, brackets: list[dict[str, Any]]) -> float:
    """프로그레시브 세금 계산 (브라켓 기반)"""
    if taxable_income <= 0:
        return 0.0

    tax = 0.0
    prev_limit = 0.0

    for bracket in brackets:
        rate = float(bracket["rate"])
        up_to = bracket.get("up_to", bracket.get("max", None))

        if up_to is None:  # 마지막 브라켓 (무제한)
            span = taxable_income - prev_limit
            if span > 0:
                tax += span * rate
            break

        limit = float(up_to)
        if taxable_income <= limit:
            span = taxable_income - prev_limit
            if span > 0:
                tax += span * rate
            break

        span = limit - prev_limit
        if span > 0:
            tax += span * rate
        prev_limit = limit

    return round(tax, 2)  # 센트 단위 정확성


def _count_eligibility_boxes(flags: PersonFlags) -> int:
    """추가 공제 자격 박스 수 계산 (65세 이상 + 시각장애)"""
    return (1 if flags.age_65_or_over else 0) + (1 if flags.blind else 0)


def _calculate_federal_standard_deduction_2025(
    params: dict[str, Any], tax_input: TaxInput
) -> float:
    """연방 표준공제 계산 (OBBBA 반영 2025년 값)"""
    federal_params = params["federal"]
    base_deductions = federal_params["standard_deduction"]
    status = tax_input.filing_status.lower()

    # 기본 표준공제
    base_deduction = float(base_deductions.get(status, base_deductions.get(status.upper(), 0.0)))

    # 의존자 표준공제 (미성년 자녀 등)
    if tax_input.flags.is_dependent:
        dep_config = federal_params["dependent_standard_deduction"]
        min_deduction = float(dep_config["min"])
        earned_income_addition = float(dep_config["add_earned_income"])

        earned_income = max(0.0, tax_input.gross_income - tax_input.adjustments)
        dependent_deduction = max(min_deduction, earned_income + earned_income_addition)

        return min(dependent_deduction, base_deduction)

    # 고령자/시각장애인 추가 공제
    additional_config = federal_params.get(
        "additional_std_deduction_aged_blind",
        federal_params.get("additional_deduction_65_blind", {}),
    )
    boxes = _count_eligibility_boxes(tax_input.flags)

    spouse_boxes = 0
    if tax_input.spouse_flags is not None:
        spouse_boxes = _count_eligibility_boxes(tax_input.spouse_flags)

    if status in ("single", "head_of_household", "SINGLE", "HEAD_OF_HOUSEHOLD"):
        per_box_amount = float(
            additional_config.get("single_or_hoh", additional_config.get("single", 0.0))
        )
        base_deduction += per_box_amount * boxes
    else:  # MARRIED_FILING_JOINTLY, etc.
        per_box_amount = float(
            additional_config.get("married_or_qss", additional_config.get("married", 0.0))
        )
        base_deduction += per_box_amount * (boxes + spouse_boxes)

    # OBBBA 고령자 보너스 공제 (65세 이상)
    senior_config = federal_params.get("senior_bonus_deduction")
    if senior_config and tax_input.magi is not None:
        bonus_per_person = float(senior_config["amount_per_person"])
        phaseout_single = float(senior_config["phaseout_magi_single"])
        phaseout_joint = float(senior_config["phaseout_magi_joint"])

        # 자격자 수 계산
        eligible_count = 0
        if tax_input.flags.age_65_or_over:
            eligible_count += 1
        if tax_input.spouse_flags and tax_input.spouse_flags.age_65_or_over:
            eligible_count += 1

        if eligible_count > 0:
            total_bonus = bonus_per_person * eligible_count

            # 단계적 축소 적용
            phaseout_threshold = (
                phaseout_joint
                if status in ("MARRIED_FILING_JOINTLY", "QUALIFYING_SURVIVING_SPOUSE")
                else phaseout_single
            )

            excess_magi = max(0.0, float(tax_input.magi) - phaseout_threshold)
            reduction = min(total_bonus, excess_magi)
            final_bonus = max(0.0, total_bonus - reduction)

            base_deduction += final_bonus

    return base_deduction


def _calculate_ca_standard_deduction_2025(params: dict[str, Any], tax_input: TaxInput) -> float:
    """캘리포니아 주 표준공제 계산"""
    ca_params = params.get("ca", params.get("california", {}))
    deductions = ca_params.get("standard_deduction", {})
    status = tax_input.filing_status.lower()

    return float(deductions.get(status, deductions.get(status.upper(), 0.0)))


class TaxCalculator:
    """SSOT 기반 세금 계산기"""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def calculate_federal_tax_2025(self, tax_input: TaxInput) -> dict[str, Any]:
        """연방 소득세 계산 (상세 결과 반환)"""
        # 조정총소득 계산
        agi = max(0.0, float(tax_input.gross_income) - float(tax_input.adjustments))

        # 공제액 결정 (표준공제 vs 항목별 공제)
        standard_deduction = _calculate_federal_standard_deduction_2025(self.params, tax_input)
        deduction = (
            standard_deduction
            if tax_input.itemized_deductions is None
            else max(standard_deduction, float(tax_input.itemized_deductions))
        )

        # 과세소득 계산
        taxable_income = max(0.0, agi - deduction)

        # 세금 계산
        filing_status = tax_input.filing_status.lower()
        federal_config = self.params.get("federal", {})
        brackets_map = federal_config.get("brackets", {})

        # 브래킷이 리스트인 경우 (테스트 케이스 호환성 용)
        if isinstance(brackets_map, list):
            brackets = brackets_map
        else:
            brackets = brackets_map.get(filing_status, brackets_map.get(filing_status.upper(), []))

        tax = _progressive_tax(taxable_income, brackets)

        return {"tax": tax, "taxable_income": taxable_income, "deduction": deduction}

    def calculate_ca_tax_2025(self, tax_input: TaxInput) -> dict[str, Any]:
        """캘리포니아 주세 계산 (상세 결과 반환)"""
        # CA 조정총소득 (간단화: 연방과 동일 가정)
        ca_agi = max(0.0, float(tax_input.gross_income) - float(tax_input.adjustments))

        # CA 표준공제
        deduction = _calculate_ca_standard_deduction_2025(self.params, tax_input)

        # CA 과세소득
        taxable_income = max(0.0, ca_agi - deduction)

        # CA 세금 계산
        filing_status = tax_input.filing_status.lower()
        ca_params = self.params.get("ca", self.params.get("california", {}))
        brackets_map = ca_params.get("brackets", {})

        # 브래켓이 리스트인 경우
        if isinstance(brackets_map, list):
            brackets = brackets_map
        else:
            brackets = brackets_map.get(filing_status, brackets_map.get(filing_status.upper(), []))

        tax = _progressive_tax(taxable_income, brackets)

        return {"tax": tax, "taxable_income": taxable_income, "deduction": deduction}

    def calculate_total_tax_2025(self, tax_input: TaxInput) -> dict[str, Any]:
        """연방 + CA 총 세금 계산 (상세 결과 반환)"""
        fed_res = self.calculate_federal_tax_2025(tax_input)
        ca_res = self.calculate_ca_tax_2025(tax_input)

        fed_tax = fed_res["tax"]
        ca_tax = ca_res["tax"]

        return {
            "federal": fed_res,
            "california": ca_res,
            "total_tax": fed_tax + ca_tax,
            "effective_rate": (
                (fed_tax + ca_tax) / tax_input.gross_income if tax_input.gross_income > 0 else 0.0
            ),
            "input_summary": {
                "filing_status": tax_input.filing_status,
                "gross_income": tax_input.gross_income,
                "adjustments": tax_input.adjustments,
                "has_itemized_deductions": tax_input.itemized_deductions is not None,
            },
        }
