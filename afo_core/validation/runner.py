"""
실행 로직 모듈 (SOLID: 단일 책임 원칙)

이 모듈은 코드 검증 실행의 전체 흐름을 담당합니다.
- 모듈 로딩 → AST 분석 → 결과 집계 → 반환
"""

import inspect
from typing import Any

from .ast_analyzer import analyze_code
from .loader import load_review_module


async def run_validation(code: str, file_name: str = "test.py") -> dict[str, Any]:
    """
    코드 검증을 종합적으로 실행합니다.

    실행 순서:
    1. 기존 검증 모듈 로딩
    2. Coordinator/기본 검증 실행
    3. AST 심층 분석 실행
    4. 결과 통합 및 반환

    Args:
        code: 검증할 Python 코드
        file_name: 파일명 (로깅용)

    Returns:
        dict: 종합 검증 결과
    """
    result = {
        "ticket": "TICKET-046",
        "source": None,
        "result": {},
        "validation_success": False,
        "trinity_score": {
            "truth": 0.0,  # AST 분석 정확도
            "goodness": 0.0,  # 안정성 검증
            "beauty": 0.0,  # 구조적 우아함
            "serenity": 1.0,  # 형님 평온 (항상 1.0)
            "eternity": 0.0,  # 유지보수성
        },
    }

    try:
        # 1. 기존 검증 모듈 로딩
        mod, path = load_review_module()
        result["source"] = str(path)

        # 2. Coordinator 우선 실행
        coordinator_result = await _run_coordinator(mod, code, file_name)
        if coordinator_result:
            result["result"]["coordinator"] = coordinator_result

        # 3. Fallback 검증 실행
        fallback_result = await _run_fallback(mod, code, file_name)
        if fallback_result:
            result["result"]["fallback"] = fallback_result

        # 4. AST 심층 분석 실행
        ast_result = analyze_code(code)
        result["result"]["ast_analysis"] = ast_result

        # 5. Trinity Score 계산
        result["trinity_score"] = _calculate_trinity_score(result["result"])

        # 6. 종합 승인 판단
        result["validation_success"] = _determine_overall_success(result["result"])

        return result

    except Exception as e:
        result["error"] = str(e)
        result["validation_success"] = False
        return result


async def _run_coordinator(mod, code: str, file_name: str) -> dict[str, Any] | None:
    """
    CodeReviewCoordinator를 우선 실행합니다.

    Returns:
        dict or None: Coordinator 결과 또는 None
    """
    Coordinator = getattr(mod, "CodeReviewCoordinator", None)
    if Coordinator is None:
        return None

    coord = Coordinator()
    methods = ["review", "run", "execute", "validate", "review_code"]

    for method_name in methods:
        if hasattr(coord, method_name):
            method = getattr(coord, method_name)
            try:
                # 파라미터 형식에 따라 호출
                if method_name in ["review", "review_code"]:
                    result = method(code, file_name)
                else:
                    result = method({"review_code": code, "review_file_path": file_name})

                if inspect.isawaitable(result):
                    result = await result

                return {
                    "method": f"CodeReviewCoordinator.{method_name}",
                    "result": result,
                    "success": True,
                }

            except Exception as e:
                return {
                    "method": f"CodeReviewCoordinator.{method_name}",
                    "error": str(e),
                    "success": False,
                }

    return {
        "method": "CodeReviewCoordinator",
        "error": "No suitable method found",
        "success": False,
    }


async def _run_fallback(mod, code: str, file_name: str) -> dict[str, Any] | None:
    """
    Coordinator 실패 시 fallback 검증을 실행합니다.

    Returns:
        dict or None: Fallback 결과 또는 None
    """
    # 1. code_review_node 객체 확인
    node_obj = getattr(mod, "code_review_node", None)
    if node_obj and hasattr(node_obj, "execute"):
        try:
            result = node_obj.execute({"review_code": code, "review_file_path": file_name})
            if inspect.isawaitable(result):
                result = await result
            return {
                "method": "code_review_node.execute",
                "result": result,
                "success": True,
            }
        except Exception as e:
            return {
                "method": "code_review_node.execute",
                "error": str(e),
                "success": False,
            }

    # 2. 모듈 레벨 execute 함수 확인
    exec_fn = getattr(mod, "execute", None)
    if exec_fn:
        try:
            result = exec_fn({"review_code": code, "review_file_path": file_name})
            if inspect.isawaitable(result):
                result = await result
            return {"method": "module.execute", "result": result, "success": True}
        except Exception as e:
            return {"method": "module.execute", "error": str(e), "success": False}

    # 3. simple_syntax_check 함수 확인
    simple_check = getattr(mod, "simple_syntax_check", None)
    if callable(simple_check):
        try:
            result = simple_check(code)
            if inspect.isawaitable(result):
                result = await result
            return {"method": "simple_syntax_check", "result": result, "success": True}
        except Exception as e:
            return {"method": "simple_syntax_check", "error": str(e), "success": False}

    return None


def _calculate_trinity_score(results: dict[str, Any]) -> dict[str, float]:
    """
    검증 결과를 바탕으로 Trinity Score를 계산합니다.

    Args:
        results: 검증 결과 딕셔너리

    Returns:
        dict: Trinity Score
    """
    score = {
        "truth": 0.0,  # AST 분석 정확도
        "goodness": 0.0,  # 안정성 검증
        "beauty": 0.0,  # 구조적 우아함
        "serenity": 1.0,  # 형님 평온 (항상 최대)
        "eternity": 0.0,  # 유지보수성
    }

    # AST 분석 점수 (Truth)
    ast_result = results.get("ast_analysis", {})
    if ast_result:
        ast_score = ast_result.get("score", 0.0)
        issues_count = ast_result.get("issues_count", 0)

        # AST 분석 정확도
        if issues_count == 0 and ast_score >= 0.8:
            score["truth"] = 1.0
        elif issues_count <= 2 and ast_score >= 0.6:
            score["truth"] = 0.8
        elif ast_score >= 0.4:
            score["truth"] = 0.6
        else:
            score["truth"] = 0.4

    # 기존 검증 성공률 (Goodness)
    coordinator_success = results.get("coordinator", {}).get("success", False)
    fallback_success = results.get("fallback", {}).get("success", False)

    if coordinator_success:
        score["goodness"] = 1.0
    elif fallback_success:
        score["goodness"] = 0.8
    elif ast_result:
        score["goodness"] = 0.6
    else:
        score["goodness"] = 0.3

    # 모듈화 구조 점수 (Beauty)
    # 패키지 구조, 단일 책임 분리 등으로 평가
    has_ast = bool(ast_result)
    has_multiple_results = len(results) >= 2

    if has_ast and has_multiple_results:
        score["beauty"] = 1.0
    elif has_ast:
        score["beauty"] = 0.8
    else:
        score["beauty"] = 0.6

    # 유지보수성 점수 (Eternity)
    # 모듈화, 재사용성 등으로 평가
    structure = ast_result.get("structure", {}) if ast_result else {}
    functions_count = len(structure.get("functions", []))
    classes_count = len(structure.get("classes", []))

    if functions_count > 0 and classes_count >= 0:
        score["eternity"] = 0.9
    elif functions_count > 0:
        score["eternity"] = 0.7
    else:
        score["eternity"] = 0.5

    return score


def _determine_overall_success(results: dict[str, Any]) -> bool:
    """
    종합 검증 성공 여부를 결정합니다.

    Args:
        results: 검증 결과 딕셔너리

    Returns:
        bool: 종합 성공 여부
    """
    # AST 분석 결과 확인
    ast_result = results.get("ast_analysis", {})
    ast_approved = ast_result.get("approved", False)

    # 기존 검증 결과 확인
    coord_success = results.get("coordinator", {}).get("success", False)
    fallback_success = results.get("fallback", {}).get("success", False)

    # 최소 하나 이상의 검증이 성공해야 함
    validation_success = coord_success or fallback_success or ast_approved

    # AST 분석이 있고 점수가 0.5 이상이어야 함
    ast_score = ast_result.get("score", 0.0)
    ast_threshold_met = ast_score >= 0.5 if ast_result else True

    return validation_success and ast_threshold_met
