"""validation 패키지 AST Analyzer 테스트

TICKET-046 결과물 검증 - 코드 검증 시스템 모듈화 + AST 분석
"""

from validation import ASTAnalyzer, analyze_code


class TestASTAnalyzer:
    """ASTAnalyzer 클래스 테스트"""

    def test_init_valid_code(self) -> None:
        """유효한 코드로 초기화"""
        code = """
def hello():
    return "world"
"""
        analyzer = ASTAnalyzer(code)
        assert analyzer.tree is not None
        assert len(analyzer.issues) == 0

    def test_init_invalid_code(self) -> None:
        """잘못된 구문으로 초기화"""
        code = """def broken("""
        analyzer = ASTAnalyzer(code)
        assert analyzer.tree is None
        assert len(analyzer.issues) > 0
        assert "Syntax error" in analyzer.issues[0]

    def test_analyze_complexity_simple(self) -> None:
        """단순 코드 복잡도 분석"""
        code = """
def simple():
    return 1
"""
        analyzer = ASTAnalyzer(code)
        complexity = analyzer.analyze_complexity()
        assert complexity == 0.0  # 제어 구조 없음

    def test_analyze_complexity_with_controls(self) -> None:
        """제어 구조가 있는 코드 복잡도"""
        code = """
def complex_func(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                pass
    return x
"""
        analyzer = ASTAnalyzer(code)
        complexity = analyzer.analyze_complexity()
        assert complexity > 0  # if, for, if 구조

    def test_detect_vulnerabilities_eval(self) -> None:
        """eval 함수 취약점 탐지"""
        code = """
def dangerous():
    user_input = input()
    return eval(user_input)
"""
        analyzer = ASTAnalyzer(code)
        vulns = analyzer.detect_vulnerabilities()
        assert any("eval" in v for v in vulns)

    def test_detect_vulnerabilities_exec(self) -> None:
        """exec 함수 취약점 탐지"""
        code = """
def dangerous():
    exec("print('hello')")
"""
        analyzer = ASTAnalyzer(code)
        vulns = analyzer.detect_vulnerabilities()
        assert any("exec" in v for v in vulns)

    def test_detect_vulnerabilities_bare_except(self) -> None:
        """bare except 탐지"""
        code = """
def bad_exception():
    try:
        risky()
    except:
        pass
"""
        analyzer = ASTAnalyzer(code)
        vulns = analyzer.detect_vulnerabilities()
        assert any("Bare except" in v for v in vulns)

    def test_detect_vulnerabilities_assert(self) -> None:
        """assert 문 탐지"""
        code = """
def with_assert():
    x = 5
    assert x > 0, "x must be positive"
"""
        analyzer = ASTAnalyzer(code)
        vulns = analyzer.detect_vulnerabilities()
        assert any("Assert" in v for v in vulns)

    def test_detect_vulnerabilities_clean_code(self) -> None:
        """취약점 없는 코드"""
        code = """
def clean():
    try:
        return 1
    except ValueError as e:
        return 0
"""
        analyzer = ASTAnalyzer(code)
        vulns = analyzer.detect_vulnerabilities()
        assert len(vulns) == 0

    def test_check_duplicates(self) -> None:
        """중복 이름 탐지"""
        code = """
def func():
    x = 1
    y = x + 1
    z = x + y
    return x
"""
        analyzer = ASTAnalyzer(code)
        duplicates = analyzer.check_duplicates()
        assert len(duplicates) > 0  # x가 여러 번 사용됨

    def test_analyze_structure_functions(self) -> None:
        """함수 구조 분석"""
        code = """
def func1(a, b):
    return a + b

def func2(x):
    pass
"""
        analyzer = ASTAnalyzer(code)
        structure = analyzer.analyze_structure()
        assert len(structure["functions"]) == 2
        assert structure["functions"][0]["name"] == "func1"
        assert structure["functions"][0]["args_count"] == 2
        assert structure["functions"][0]["has_return"] is True

    def test_analyze_structure_classes(self) -> None:
        """클래스 구조 분석"""
        code = """
class MyClass:
    def __init__(self):
        pass

    def method1(self):
        pass

    def method2(self):
        pass
"""
        analyzer = ASTAnalyzer(code)
        structure = analyzer.analyze_structure()
        assert len(structure["classes"]) == 1
        assert structure["classes"][0]["name"] == "MyClass"
        assert structure["classes"][0]["methods_count"] == 3

    def test_analyze_structure_imports(self) -> None:
        """임포트 구조 분석"""
        code = """
import os
from typing import Any, List
from pathlib import Path
"""
        analyzer = ASTAnalyzer(code)
        structure = analyzer.analyze_structure()
        imports = structure["imports"]
        assert "os" in imports
        assert "typing.Any" in imports
        assert "typing.List" in imports


class TestAnalyzeCode:
    """analyze_code 함수 테스트"""

    def test_analyze_code_clean(self) -> None:
        """깨끗한 코드 분석"""
        code = """
def add(x: int, y: int) -> int:
    return x + y
"""
        result = analyze_code(code)
        assert result["approved"] is True
        assert result["score"] >= 0.7
        # 단순 이름 중복 (파라미터 재사용)은 허용
        assert result["issues_count"] <= 2

    def test_analyze_code_with_issues(self) -> None:
        """문제가 있는 코드 분석"""
        code = """
def dangerous():
    eval("print('hello')")
    exec("x = 1")
    try:
        pass
    except:
        pass
"""
        result = analyze_code(code)
        assert len(result["vulnerabilities"]) >= 3  # eval, exec, bare except
        assert result["score"] < 1.0  # 페널티 적용됨

    def test_analyze_code_high_complexity(self) -> None:
        """높은 복잡도 코드 분석"""
        code = """
def complex():
    for i in range(10):
        if i > 5:
            for j in range(i):
                if j % 2:
                    for k in range(j):
                        if k > 0:
                            while k > 0:
                                try:
                                    k -= 1
                                except:
                                    pass
                                finally:
                                    pass
    return True
"""
        result = analyze_code(code)
        assert result["complexity_score"] > 5  # 높은 복잡도

    def test_analyze_code_structure(self) -> None:
        """구조 분석 결과 확인"""
        code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
"""
        result = analyze_code(code)
        assert "structure" in result
        assert len(result["structure"]["classes"]) == 1
        assert result["structure"]["classes"][0]["methods_count"] == 2

    def test_analyze_code_syntax_error(self) -> None:
        """구문 오류 코드 분석"""
        code = """def broken("""
        result = analyze_code(code)
        # 구문 오류가 있어도 결과 반환
        assert "structure" in result
        assert result["structure"].get("error") is not None


class TestValidationIntegration:
    """validation 패키지 통합 테스트"""

    def test_import_main_interface(self) -> None:
        """메인 인터페이스 임포트 확인"""
        from validation import analyze_code as analyze_fn, load_review_module

        assert callable(analyze_fn)
        assert callable(load_review_module)

    def test_trinity_score_calculation(self) -> None:
        """Trinity Score 계산 검증 (간접)"""
        code = """
def good_function(x: int) -> int:
    '''잘 작성된 함수'''
    if x > 0:
        return x * 2
    return 0
"""
        result = analyze_code(code)
        # 깨끗한 코드는 높은 점수
        assert result["score"] >= 0.7
        assert result["approved"] is True
