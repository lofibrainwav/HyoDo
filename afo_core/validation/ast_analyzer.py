"""
AST 심층 분석 모듈 (SOLID: 단일 책임 원칙)

이 모듈은 Python AST(Abstract Syntax Tree)를 활용하여
코드의 복잡도, 보안 취약점, 중복 등을 심층 분석합니다.

Trinity Score 목표: 眞 (Truth) 0.9 달성
"""

import ast
from typing import Any


class ASTAnalyzer:
    """
    Python AST 기반 코드 분석기

    분석 기능:
    - 코드 복잡도 계산 (Cyclomatic Complexity)
    - 보안 취약점 탐지 (eval, exec, open 등)
    - 코드 중복 분석 (이름 기반)
    - 함수/클래스 구조 분석
    """

    def __init__(self, code: str) -> None:
        """
        AST 분석기 초기화

        Args:
            code: 분석할 Python 코드 문자열
        """
        self.code = code
        self.issues: list[str] = []
        self.tree: ast.Module | None = None

        try:
            self.tree = ast.parse(code)
        except SyntaxError as e:
            self.tree = None
            self.issues.append(f"Syntax error: {e}")

    def analyze_complexity(self) -> float:
        """
        코드 복잡도를 계산합니다 (Cyclomatic Complexity).

        복잡도 요소:
        - if/elif 문
        - for/while 루프
        - try/except 블록
        - 함수/클래스 정의

        Returns:
            float: 계산된 복잡도 점수
        """
        if self.tree is None:
            return 0.0

        complexity = 0

        for node in ast.walk(self.tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.FunctionDef):
                # 함수 내부의 제어 구조도 고려
                inner_complexity = sum(
                    1
                    for n in ast.walk(node)
                    if isinstance(n, (ast.If, ast.For, ast.While, ast.Try))
                )
                complexity += inner_complexity

        return float(complexity)

    def detect_vulnerabilities(self) -> list[str]:
        """
        보안 취약점을 탐지합니다.

        탐지 대상:
        - eval(), exec() 함수 호출
        - 안전하지 않은 file open
        - assert 문 (프로덕션 환경)
        - bare except 절

        Returns:
            List[str]: 발견된 취약점 목록
        """
        if self.tree is None:
            return ["Cannot analyze due to syntax errors"]

        vulnerabilities = []

        for node in ast.walk(self.tree):
            # eval/exec 탐지
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("eval", "exec"):
                    vulnerabilities.append(f"Security risk: {func.id}() detected")

                # open() 함수의 안전하지 않은 사용
                elif isinstance(func, ast.Attribute) and func.attr == "open":
                    # mode 파라미터 확인
                    has_mode = any(
                        isinstance(kw.arg, str) and kw.arg == "mode" for kw in node.keywords
                    )
                    if not has_mode:
                        vulnerabilities.append("Potential unsafe file open without explicit mode")

            # assert 문 탐지
            elif isinstance(node, ast.Assert):
                vulnerabilities.append("Assert statement found - consider removing for production")

            # bare except 탐지
            elif isinstance(node, ast.ExceptHandler) and node.type is None:
                vulnerabilities.append("Bare except clause found - specify exception types")

        return vulnerabilities

    def check_duplicates(self) -> list[str]:
        """
        코드 중복을 분석합니다 (간단한 이름 기반 분석).

        Returns:
            List[str]: 중복된 이름 목록
        """
        if self.tree is None:
            return ["Cannot analyze due to syntax errors"]

        names = []
        duplicates = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name):
                name = node.id
                if name in names and name not in duplicates:
                    duplicates.append(name)
                names.append(name)

        return [f"Duplicate name: {name}" for name in duplicates]

    def analyze_structure(self) -> dict[str, Any]:
        """
        코드 구조를 분석합니다.

        Returns:
            Dict: 구조 분석 결과
        """
        if self.tree is None:
            return {"error": "Cannot analyze due to syntax errors"}

        functions = []
        classes = []
        imports: list[str] = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(
                    {
                        "name": node.name,
                        "args_count": len(node.args.args),
                        "has_return": any(isinstance(n, ast.Return) for n in ast.walk(node)),
                        "line_start": node.lineno,
                    }
                )
            elif isinstance(node, ast.ClassDef):
                classes.append(
                    {
                        "name": node.name,
                        "methods_count": sum(
                            1 for n in node.body if isinstance(n, ast.FunctionDef)
                        ),
                        "line_start": node.lineno,
                    }
                )
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                else:
                    module = node.module or ""
                    imports.extend(
                        f"{module}.{alias.name}" if module else alias.name for alias in node.names
                    )

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "total_lines": len(self.code.splitlines()),
        }


def analyze_code(code: str) -> dict[str, Any]:
    """
    코드를 종합적으로 분석합니다.

    Args:
        code: 분석할 Python 코드

    Returns:
        Dict: 종합 분석 결과
    """
    analyzer = ASTAnalyzer(code)

    # 기본 분석
    complexity = analyzer.analyze_complexity()
    vulnerabilities = analyzer.detect_vulnerabilities()
    duplicates = analyzer.check_duplicates()
    structure = analyzer.analyze_structure()

    # 종합 점수 계산
    base_score = 1.0

    # 복잡도 페널티
    if complexity > 10:
        base_score -= 0.2
    elif complexity > 5:
        base_score -= 0.1

    # 취약점 페널티
    vulnerability_penalty = len(vulnerabilities) * 0.1
    base_score -= vulnerability_penalty

    # 중복 페널티
    duplicate_penalty = len(duplicates) * 0.05
    base_score -= duplicate_penalty

    final_score = max(0.0, base_score)
    approved = final_score >= 0.7

    return {
        "complexity_score": complexity,
        "vulnerabilities": vulnerabilities,
        "duplicates": duplicates,
        "structure": structure,
        "score": final_score,
        "approved": approved,
        "issues_count": len(vulnerabilities) + len(duplicates),
    }
