from __future__ import annotations

from typing import Any

"""SSOT 기반 세금 파라미터 검증기

Trinity Score 기반 검증:
- 眞(Truth): 파라미터 구조 및 값의 정확성 검증
- 善(Goodness): OBBBA 준수 및 세법 일관성 확인
- 美(Beauty): 검증 로직의 명확성과 모듈성
- 孝(Serenity): 명확한 에러 메시지로 사용자 안내
- 永(Eternity): 검증 결과의 재현 가능성 보장

검증 항목:
- 브라켓 구조 유효성 (단조 증가, 터미널 브라켓 존재)
- 세율 범위 검증 (0.0 ~ 1.0)
- 공제 금액 양수 검증
- 파라미터 키 존재성 검증
"""


def _validate_bracket_structure(brackets: list[dict[str, Any]]) -> None:
    """세금 브라켓 구조 검증"""
    if not brackets:
        raise ValueError("브라켓이 비어있음")

    last_limit: float = -1.0
    has_terminal = False

    for i, bracket in enumerate(brackets):
        if "rate" not in bracket:
            raise ValueError(f"브라켓 {i}: 세율(rate)이 누락됨")

        rate = bracket["rate"]
        if not isinstance(rate, (int, float)) or not (0.0 <= rate <= 1.0):
            raise ValueError(f"브라켓 {i}: 세율이 유효하지 않음 (0.0-1.0 범위만 허용): {rate}")

        up_to = bracket.get("up_to")
        if up_to is None:
            # 터미널 브라켓 (마지막 브라켓)
            if has_terminal:
                raise ValueError("터미널 브라켓(up_to: null)이 여러 개 존재")
            if i != len(brackets) - 1:
                raise ValueError("터미널 브라켓은 마지막에만 올 수 있음")
            has_terminal = True
            continue

        # 일반 브라켓
        if not isinstance(up_to, (int, float)):
            raise ValueError(f"브라켓 {i}: 상한선(up_to)이 숫자가 아님: {up_to}")

        limit = float(up_to)
        if limit <= last_limit:
            raise ValueError(
                f"브라켓 {i}: 상한선이 이전 브라켓보다 작거나 같음: {limit} <= {last_limit}"
            )

        last_limit = limit

    if not has_terminal:
        raise ValueError("터미널 브라켓(up_to: null)이 존재하지 않음")


def _validate_positive_amounts(params: dict[str, Any], path: str) -> None:
    """금액 필드의 양수성 검증"""
    if isinstance(params, dict):
        for key, value in params.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, (int, float)):
                if value < 0:
                    raise ValueError(f"금액이 음수: {current_path} = {value}")
            elif isinstance(value, dict):
                _validate_positive_amounts(value, current_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        _validate_positive_amounts(item, f"{current_path}[{i}]")


def _validate_federal_params(federal_params: dict[str, Any]) -> None:
    """연방 세금 파라미터 검증"""
    required_keys = {
        "standard_deduction",
        "dependent_standard_deduction",
        "additional_std_deduction_aged_blind",
        "brackets",
    }

    missing = required_keys - set(federal_params.keys())
    if missing:
        raise ValueError(f"연방 파라미터 누락: {missing}")

    # 표준공제 검증
    std_ded = federal_params["standard_deduction"]
    required_statuses = {
        "SINGLE",
        "MARRIED_FILING_SEPARATELY",
        "MARRIED_FILING_JOINTLY",
        "HEAD_OF_HOUSEHOLD",
        "QUALIFYING_SURVIVING_SPOUSE",
    }
    if not all(status in std_ded for status in required_statuses):
        raise ValueError(f"표준공제 상태 누락: {required_statuses - set(std_ded.keys())}")

    # 의존자 표준공제 검증
    dep_config = federal_params["dependent_standard_deduction"]
    if not all(key in dep_config for key in ["min", "add_earned_income"]):
        raise ValueError("의존자 표준공제 설정 누락")

    # 추가 공제 검증
    add_config = federal_params["additional_std_deduction_aged_blind"]
    if not all(key in add_config for key in ["single_or_hoh", "married_or_qss"]):
        raise ValueError("고령자/시각장애인 추가 공제 설정 누락")

    # 브라켓 검증
    brackets = federal_params["brackets"]
    required_bracket_statuses = {
        "SINGLE",
        "MARRIED_FILING_SEPARATELY",
        "MARRIED_FILING_JOINTLY",
        "HEAD_OF_HOUSEHOLD",
        "QUALIFYING_SURVIVING_SPOUSE",
    }
    if not all(status in brackets for status in required_bracket_statuses):
        raise ValueError(f"브라켓 상태 누락: {required_bracket_statuses - set(brackets.keys())}")

    for status, status_brackets in brackets.items():
        _validate_bracket_structure(status_brackets)

    # 고령자 보너스 공제 검증 (선택 사항)
    senior_config = federal_params.get("senior_bonus_deduction")
    if senior_config:
        required_senior_keys = {
            "amount_per_person",
            "phaseout_magi_single",
            "phaseout_magi_joint",
        }
        if not all(key in senior_config for key in required_senior_keys):
            raise ValueError(
                f"고령자 보너스 공제 설정 불완전: {required_senior_keys - set(senior_config.keys())}"
            )


def _validate_ca_params(ca_params: dict[str, Any]) -> None:
    """캘리포니아 주세 파라미터 검증"""
    required_keys = {"standard_deduction", "brackets"}

    missing = required_keys - set(ca_params.keys())
    if missing:
        raise ValueError(f"CA 파라미터 누락: {missing}")

    # 표준공제 검증
    std_ded = ca_params["standard_deduction"]
    required_statuses = {
        "SINGLE",
        "MARRIED_FILING_SEPARATELY",
        "MARRIED_FILING_JOINTLY",
        "HEAD_OF_HOUSEHOLD",
        "QUALIFYING_SURVIVING_SPOUSE",
    }
    if not all(status in std_ded for status in required_statuses):
        raise ValueError(f"CA 표준공제 상태 누락: {required_statuses - set(std_ded.keys())}")

    # 브라켓 검증
    brackets = ca_params["brackets"]
    required_bracket_statuses = {
        "SINGLE",
        "MARRIED_FILING_SEPARATELY",
        "MARRIED_FILING_JOINTLY",
        "HEAD_OF_HOUSEHOLD",
        "QUALIFYING_SURVIVING_SPOUSE",
    }
    if not all(status in brackets for status in required_bracket_statuses):
        raise ValueError(f"CA 브라켓 상태 누락: {required_bracket_statuses - set(brackets.keys())}")

    for status, status_brackets in brackets.items():
        _validate_bracket_structure(status_brackets)


def validate_tax_params_2025(params: dict[str, Any]) -> None:
    """2025년 세금 파라미터 전체 검증

    Args:
        params: 검증할 세금 파라미터 딕셔너리

    Raises:
        ValueError: 파라미터가 유효하지 않은 경우 상세 메시지와 함께 발생
    """
    if not isinstance(params, dict):
        raise ValueError("파라미터는 딕셔너리여야 함")

    # 최상위 키 검증
    if "federal" not in params:
        raise ValueError("연방 파라미터(federal)가 누락됨")
    if "ca" not in params:
        raise ValueError("캘리포니아 파라미터(ca)가 누락됨")

    # 연방 파라미터 검증
    _validate_federal_params(params["federal"])

    # CA 파라미터 검증
    _validate_ca_params(params["ca"])

    # 전체 금액 양수성 검증
    _validate_positive_amounts(params, "")

    # OBBBA 준수 검증 (2025년 표준공제 값 확인)
    federal_std = params["federal"]["standard_deduction"]
    expected_obbba_values = {
        "SINGLE": 15750,
        "MARRIED_FILING_SEPARATELY": 15750,
        "MARRIED_FILING_JOINTLY": 31500,
        "HEAD_OF_HOUSEHOLD": 23625,
        "QUALIFYING_SURVIVING_SPOUSE": 31500,
    }

    for status, expected in expected_obbba_values.items():
        actual = federal_std.get(status.upper())
        if actual != expected:
            raise ValueError(f"OBBBA 표준공제 불일치: {status} = {actual}, 예상 = {expected}")


def validate_tax_calculation_result(
    input_data: dict[str, Any], result: dict[str, Any], params: dict[str, Any]
) -> None:
    """세금 계산 결과 검증

    Args:
        input_data: 계산 입력 데이터
        result: 계산 결과
        params: 사용된 파라미터

    Raises:
        ValueError: 계산 결과가 일관되지 않은 경우
    """
    # 기본 구조 검증
    required_keys = {
        "federal",
        "california",
        "total_tax",
        "effective_rate",
        "input_summary",
    }
    if not all(key in result for key in required_keys):
        raise ValueError(f"결과 구조 불완전: {required_keys - set(result.keys())}")

    # 금액 일관성 검증
    federal_tax = result["federal"]["tax"]
    ca_tax = result["california"]["tax"]
    total_tax = result["total_tax"]

    if abs((federal_tax + ca_tax) - total_tax) > 0.01:  # 센트 단위 오차 허용
        raise ValueError(f"총세금 불일치: {federal_tax} + {ca_tax} != {total_tax}")

    # 유효 세율 범위 검증
    effective_rate = result["effective_rate"]
    if not (0.0 <= effective_rate <= 1.0):
        raise ValueError(f"유효 세율 범위 초과: {effective_rate}")

    # 입력 데이터 일관성 검증
    input_summary = result["input_summary"]
    if input_summary["gross_income"] != input_data["gross_income"]:
        raise ValueError("입력 소득 불일치")

    if input_summary["filing_status"] != input_data["filing_status"]:
        raise ValueError("신고 상태 불일치")
