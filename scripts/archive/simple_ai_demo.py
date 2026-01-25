#!/usr/bin/env python3
"""
단순한 AI 타입 추론 데모 - Ollama 사용
AFO Kingdom 방식으로 차근차근 실행
"""

import ast


def simple_type_inference_demo() -> None:
    """
    간단한 타입 추론 데모
    """
    print("🤖 AFO Kingdom AI 타입 추론 데모")
    print("=" * 50)

    # 테스트 함수들
    test_functions = [
        """
def process_data(data):
    if isinstance(data, list):
        return [item.upper() for item in data if isinstance(item, str)]
    elif isinstance(data, dict):
        return {k: v.upper() for k, v in data.items() if isinstance(v, str)}
    else:
        return str(data).upper()
""",
        """
def calculate_score(values):
    if not values:
        return 0
    return sum(values) / len(values)
""",
        """
def validate_input(value, min_val, max_val):
    if not isinstance(value, (int, float)):
        return False
    return min_val <= value <= max_val
""",
    ]

    for i, func_code in enumerate(test_functions, 1):
        print(f"\n🔍 함수 {i} 분석:")
        print("-" * 30)

        # AST 파싱
        tree = ast.parse(func_code)
        func_node = tree.body[0]

        print(f"함수명: {func_node.name}")
        print(f"파라미터: {[arg.arg for arg in func_node.args.args]}")

        # 간단한 휴리스틱 기반 타입 추론
        inferred_types = infer_types_simple(func_node)

        print("추론된 타입:")
        for param, types in inferred_types.items():
            print(f"  {param}: {types}")

        # Trinity Score 계산 (단순 버전)
        calculate_simple_trinity_score(func_node, inferred_types)
        print(".1f")

    print(f"\n✅ 데모 완료! 총 {len(test_functions)}개 함수 분석")
    print("💡 실제 AI 타입 추론은 더 정교한 알고리즘 사용")


def infer_types_simple(func_node: ast.FunctionDef) -> dict:
    """
    간단한 휴리스틱 기반 타입 추론
    """
    types = {}

    # 함수 내용 분석
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name == "isinstance":
                # isinstance 체크 분석
                if len(node.args) >= 2:
                    var_name = None
                    type_checks = []

                    # 첫 번째 인자 (변수명)
                    if isinstance(node.args[0], ast.Name):
                        var_name = node.args[0].id

                    # 두 번째 인자 (타입)
                    if isinstance(node.args[1], ast.Tuple):
                        # tuple 타입 (int, float) 등
                        type_checks.extend(
                            elt.id for elt in node.args[1].elts if isinstance(elt, ast.Name)
                        )
                    elif isinstance(node.args[1], ast.Name):
                        type_checks.append(node.args[1].id)

                    if var_name and type_checks:
                        if var_name not in types:
                            types[var_name] = set()
                        types[var_name].update(type_checks)

    # 기본 타입 추론
    for arg in func_node.args.args:
        arg_name = arg.arg
        if arg_name not in types:
            types[arg_name] = {"Any"}  # 기본값

    return types


def calculate_simple_trinity_score(func_node: ast.FunctionDef, inferred_types: dict) -> float:
    """
    단순한 Trinity Score 계산
    """
    score = 50.0  # 기본 점수

    # 파라미터 타입 힌트 점수
    param_count = len(func_node.args.args)
    typed_params = sum(1 for types in inferred_types.values() if "Any" not in types)
    score += (typed_params / param_count) * 20 if param_count > 0 else 0

    # 함수 복잡도 점수 (라인 수 기반)
    func_source = ast.get_source_segment(
        ast.parse(ast.get_source_segment(ast.parse(""), func_node)), func_node
    )
    lines = len(func_source.split("\n")) if func_source else 0
    if lines < 10:
        score += 10  # 간단한 함수
    elif lines < 20:
        score += 5  # 중간 복잡도

    # 예외 처리 점수
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(func_node))
    if has_try:
        score += 10

    return min(100.0, max(0.0, score))


if __name__ == "__main__":
    simple_type_inference_demo()
