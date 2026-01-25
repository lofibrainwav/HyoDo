"""2025년 세금 엔진 테스트

SSOT 기반 정확성 검증:
- Trinity Score 기반 테스트 케이스
- OBBBA 준수 검증
- 브라켓 경계값 테스트
- 세금 계산 일관성 검증
"""

import pytest

from AFO.tax_engine.calculator import PersonFlags, TaxCalculator, TaxInput
from AFO.tax_engine.validator import validate_tax_params_2025


def _get_test_params() -> None:
    """테스트용 OBBBA 반영 2025년 세금 파라미터"""
    return {
        "federal": {
            "standard_deduction": {
                "SINGLE": 15750,
                "MARRIED_FILING_SEPARATELY": 15750,
                "MARRIED_FILING_JOINTLY": 31500,
                "QUALIFYING_SURVIVING_SPOUSE": 31500,
                "HEAD_OF_HOUSEHOLD": 23625,
            },
            "dependent_standard_deduction": {"min": 1350, "add_earned_income": 450},
            "additional_std_deduction_aged_blind": {
                "single_or_hoh": 2000,
                "married_or_qss": 1600,
            },
            "senior_bonus_deduction": {
                "amount_per_person": 6000,
                "phaseout_magi_single": 75000,
                "phaseout_magi_joint": 150000,
            },
            "brackets": {
                "SINGLE": [
                    {"up_to": 11925, "rate": 0.10},
                    {"up_to": 48475, "rate": 0.12},
                    {"up_to": 103350, "rate": 0.22},
                    {"up_to": 197300, "rate": 0.24},
                    {"up_to": 250525, "rate": 0.32},
                    {"up_to": 626350, "rate": 0.35},
                    {"up_to": None, "rate": 0.37},
                ],
                "MARRIED_FILING_SEPARATELY": [
                    {"up_to": 11925, "rate": 0.10},
                    {"up_to": 48475, "rate": 0.12},
                    {"up_to": 103350, "rate": 0.22},
                    {"up_to": 197300, "rate": 0.24},
                    {"up_to": 250525, "rate": 0.32},
                    {"up_to": 375800, "rate": 0.35},
                    {"up_to": None, "rate": 0.37},
                ],
                "MARRIED_FILING_JOINTLY": [
                    {"up_to": 23850, "rate": 0.10},
                    {"up_to": 96950, "rate": 0.12},
                    {"up_to": 206700, "rate": 0.22},
                    {"up_to": 394600, "rate": 0.24},
                    {"up_to": 501050, "rate": 0.32},
                    {"up_to": 751600, "rate": 0.35},
                    {"up_to": None, "rate": 0.37},
                ],
                "QUALIFYING_SURVIVING_SPOUSE": [
                    {"up_to": 23850, "rate": 0.10},
                    {"up_to": 96950, "rate": 0.12},
                    {"up_to": 206700, "rate": 0.22},
                    {"up_to": 394600, "rate": 0.24},
                    {"up_to": 501050, "rate": 0.32},
                    {"up_to": 751600, "rate": 0.35},
                    {"up_to": None, "rate": 0.37},
                ],
                "HEAD_OF_HOUSEHOLD": [
                    {"up_to": 17000, "rate": 0.10},
                    {"up_to": 64850, "rate": 0.12},
                    {"up_to": 103350, "rate": 0.22},
                    {"up_to": 197300, "rate": 0.24},
                    {"up_to": 250500, "rate": 0.32},
                    {"up_to": 626350, "rate": 0.35},
                    {"up_to": None, "rate": 0.37},
                ],
            },
        },
        "ca": {
            "standard_deduction": {
                "SINGLE": 5540,
                "MARRIED_FILING_SEPARATELY": 5540,
                "MARRIED_FILING_JOINTLY": 11080,
                "QUALIFYING_SURVIVING_SPOUSE": 11080,
                "HEAD_OF_HOUSEHOLD": 11080,
            },
            "brackets": {
                "SINGLE": [
                    {"up_to": 11079, "rate": 0.01},
                    {"up_to": 26264, "rate": 0.02},
                    {"up_to": 41408, "rate": 0.04},
                    {"up_to": 57411, "rate": 0.06},
                    {"up_to": 72460, "rate": 0.08},
                    {"up_to": 370741, "rate": 0.093},
                    {"up_to": 444889, "rate": 0.103},
                    {"up_to": 741484, "rate": 0.113},
                    {"up_to": None, "rate": 0.123},
                ],
                "MARRIED_FILING_SEPARATELY": [
                    {"up_to": 11079, "rate": 0.01},
                    {"up_to": 26264, "rate": 0.02},
                    {"up_to": 41408, "rate": 0.04},
                    {"up_to": 57411, "rate": 0.06},
                    {"up_to": 72460, "rate": 0.08},
                    {"up_to": 370741, "rate": 0.093},
                    {"up_to": 444889, "rate": 0.103},
                    {"up_to": 741484, "rate": 0.113},
                    {"up_to": None, "rate": 0.123},
                ],
                "MARRIED_FILING_JOINTLY": [
                    {"up_to": 22158, "rate": 0.01},
                    {"up_to": 52529, "rate": 0.02},
                    {"up_to": 82816, "rate": 0.04},
                    {"up_to": 114822, "rate": 0.06},
                    {"up_to": 144920, "rate": 0.08},
                    {"up_to": 741484, "rate": 0.093},
                    {"up_to": 889778, "rate": 0.103},
                    {"up_to": 1482968, "rate": 0.113},
                    {"up_to": None, "rate": 0.123},
                ],
                "QUALIFYING_SURVIVING_SPOUSE": [
                    {"up_to": 22158, "rate": 0.01},
                    {"up_to": 52529, "rate": 0.02},
                    {"up_to": 82816, "rate": 0.04},
                    {"up_to": 114822, "rate": 0.06},
                    {"up_to": 144920, "rate": 0.08},
                    {"up_to": 741484, "rate": 0.093},
                    {"up_to": 889778, "rate": 0.103},
                    {"up_to": 1482968, "rate": 0.113},
                    {"up_to": None, "rate": 0.123},
                ],
                "HEAD_OF_HOUSEHOLD": [
                    {"up_to": 22172, "rate": 0.01},
                    {"up_to": 52542, "rate": 0.02},
                    {"up_to": 67684, "rate": 0.04},
                    {"up_to": 83691, "rate": 0.06},
                    {"up_to": 98731, "rate": 0.08},
                    {"up_to": 504338, "rate": 0.093},
                    {"up_to": 605210, "rate": 0.103},
                    {"up_to": 1008716, "rate": 0.113},
                    {"up_to": None, "rate": 0.123},
                ],
            },
        },
    }


def test_validate_tax_params() -> None:
    """세금 파라미터 검증 테스트"""
    params = _get_test_params()
    # 검증 함수가 에러 없이 통과해야 함
    validate_tax_params_2025(params)


def test_federal_tax_basic_calculation() -> None:
    """기본 연방 세금 계산 테스트"""
    params = _get_test_params()
    calc = TaxCalculator(params)

    # $50,000 소득, 싱글 파일러
    tax_input = TaxInput(
        filing_status="SINGLE",
        gross_income=50000,
        adjustments=0,
        itemized_deductions=None,
        flags=PersonFlags(),
        magi=50000,
    )

    result = calc.calculate_federal_tax_2025(tax_input)
    tax = result["tax"]
    taxable = result["taxable_income"]
    deduction = result["deduction"]

    # 기본 검증
    assert tax > 0
    assert taxable > 0
    assert deduction == 15750  # 2025 OBBBA 표준공제
    assert taxable == 50000 - 15750  # 조정총소득 - 공제


def test_ca_tax_basic_calculation() -> None:
    """기본 CA 주세 계산 테스트"""
    params = _get_test_params()
    calc = TaxCalculator(params)

    # $50,000 소득, 싱글 파일러
    tax_input = TaxInput(
        filing_status="SINGLE",
        gross_income=50000,
        adjustments=0,
        itemized_deductions=None,
        flags=PersonFlags(),
    )

    result = calc.calculate_ca_tax_2025(tax_input)
    tax = result["tax"]
    taxable = result["taxable_income"]
    deduction = result["deduction"]

    # 기본 검증
    assert tax > 0
    assert taxable > 0
    assert deduction == 5540  # CA 표준공제


def test_total_tax_calculation() -> None:
    """연방 + CA 총 세금 계산 테스트"""
    params = _get_test_params()
    calc = TaxCalculator(params)

    tax_input = TaxInput(
        filing_status="SINGLE",
        gross_income=75000,
        adjustments=0,
        itemized_deductions=None,
        flags=PersonFlags(),
        magi=75000,
    )

    result = calc.calculate_total_tax_2025(tax_input)

    # 구조 검증
    assert "federal" in result
    assert "california" in result
    assert "total_tax" in result
    assert "effective_rate" in result

    # 금액 일관성 검증
    expected_total = result["federal"]["tax"] + result["california"]["tax"]
    assert abs(result["total_tax"] - expected_total) < 0.01

    # 유효 세율 범위 검증
    assert 0.0 <= result["effective_rate"] <= 1.0


def test_bracket_boundary_consistency() -> None:
    """브라켓 경계에서 세금 일관성 테스트 (단조 증가 검증)"""
    params = _get_test_params()
    calc = TaxCalculator(params)

    # 다양한 소득 수준 테스트
    incomes = [30000, 50000, 75000, 100000, 150000, 200000]

    prev_tax = 0
    for income in incomes:
        tax_input = TaxInput(
            filing_status="SINGLE",
            gross_income=income,
            adjustments=0,
            itemized_deductions=None,
            flags=PersonFlags(),
            magi=income,
        )

        result = calc.calculate_federal_tax_2025(tax_input)
        tax = result["tax"]

        # 세금이 소득 증가에 따라 단조 증가하는지 검증
        assert tax >= prev_tax, f"세금이 감소함: {prev_tax} -> {tax} (소득: {income})"
        prev_tax = tax


def test_senior_bonus_deduction() -> None:
    """65세 이상 보너스 공제 테스트 (OBBBA)"""
    params = _get_test_params()
    calc = TaxCalculator(params)

    # 65세 이상, MAGI 60,000 (보너스 공제 가능)
    tax_input_senior = TaxInput(
        filing_status="SINGLE",
        gross_income=80000,
        adjustments=0,
        itemized_deductions=None,
        flags=PersonFlags(age_65_or_over=True),
        magi=60000,  # 보너스 공제 threshold 이내
    )

    # 일반인
    tax_input_regular = TaxInput(
        filing_status="SINGLE",
        gross_income=80000,
        adjustments=0,
        itemized_deductions=None,
        flags=PersonFlags(),
        magi=60000,
    )

    senior_result = calc.calculate_federal_tax_2025(tax_input_senior)
    deduction_senior = senior_result["deduction"]

    regular_result = calc.calculate_federal_tax_2025(tax_input_regular)
    deduction_regular = regular_result["deduction"]

    # 고령자 보너스 공제로 공제액이 더 커야 함
    assert deduction_senior > deduction_regular


def test_itemized_vs_standard_deduction() -> None:
    """항목별 공제 vs 표준공제 선택 테스트"""
    params = _get_test_params()
    calc = TaxCalculator(params)

    base_input = TaxInput(
        filing_status="SINGLE",
        gross_income=100000,
        adjustments=0,
        flags=PersonFlags(),
        magi=100000,
    )

    # 표준공제 사용
    standard_input = base_input
    std_result = calc.calculate_federal_tax_2025(standard_input)
    tax_std = std_result["tax"]
    taxable_std = std_result["taxable_income"]
    deduction_std = std_result["deduction"]

    # 항목별 공제 사용 ($20,000)
    itemized_input = TaxInput(
        filing_status="SINGLE",
        gross_income=100000,
        adjustments=0,
        itemized_deductions=20000,  # 표준공제보다 큰 값
        flags=PersonFlags(),
        magi=100000,
    )
    item_result = calc.calculate_federal_tax_2025(itemized_input)
    tax_item = item_result["tax"]
    taxable_item = item_result["taxable_income"]
    deduction_item = item_result["deduction"]

    # 항목별 공제가 선택되어야 함
    assert deduction_item == 20000
    assert deduction_std == 15750  # 표준공제
    assert deduction_item > deduction_std

    # 더 큰 공제로 과세소득이 적어야 함
    assert taxable_item < taxable_std
    assert tax_item < tax_std


def test_zero_income_edge_case() -> None:
    """극단적인 케이스 테스트: 0 소득"""
    params = _get_test_params()
    calc = TaxCalculator(params)

    tax_input = TaxInput(
        filing_status="SINGLE",
        gross_income=0,
        adjustments=0,
        itemized_deductions=None,
        flags=PersonFlags(),
    )

    federal_result = calc.calculate_federal_tax_2025(tax_input)
    federal_tax = federal_result["tax"]
    federal_taxable = federal_result["taxable_income"]
    federal_deduction = federal_result["deduction"]

    ca_result = calc.calculate_ca_tax_2025(tax_input)
    ca_tax = ca_result["tax"]
    ca_taxable = ca_result["taxable_income"]
    ca_deduction = ca_result["deduction"]
    result = calc.calculate_total_tax_2025(tax_input)

    # 모든 값이 0이거나 적절한 최소값이어야 함
    assert federal_tax == 0.0
    assert ca_tax == 0.0
    assert result["total_tax"] == 0.0
    assert result["effective_rate"] == 0.0


def test_high_income_bracket() -> None:
    """고소득 브라켓 테스트 (37% 세율 적용)"""
    params = _get_test_params()
    calc = TaxCalculator(params)

    # 매우 높은 소득 (1M)
    tax_input = TaxInput(
        filing_status="SINGLE",
        gross_income=1000000,
        adjustments=0,
        itemized_deductions=None,
        flags=PersonFlags(),
        magi=1000000,
    )

    result = calc.calculate_federal_tax_2025(tax_input)
    tax = result["tax"]
    taxable = result["taxable_income"]
    deduction = result["deduction"]

    # 고소득 브라켓 적용 검증
    assert tax > 0
    assert taxable == 1000000 - 15750  # 표준공제 적용
    # 37% 브라켓에 해당하는 금액이 포함되어야 함
    assert tax > 100000  # 최소 10만 달러 이상 세금
