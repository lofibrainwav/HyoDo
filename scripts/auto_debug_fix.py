#!/usr/bin/env python3
"""
AFO 왕국 자동 디버깅 시스템
실제 코드 오류들을 자동으로 감지하고 수정
"""

import ast
from pathlib import Path
from typing import Any, Dict, List


class AutoDebugger:
    """자동 디버깅 시스템"""

    def __init__(self) -> None:
        self.fixed_count = 0

    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """파일을 분석하여 오류들 찾기"""
        errors = []

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # AST 파싱으로 구조적 분석
            tree = ast.parse(content, filename=file_path)

            # request 변수 사용 분석
            request_usage = self._find_undefined_variables(content, tree)
            errors.extend(request_usage)

            # async generator 리턴 타입 분석
            generator_issues = self._analyze_async_generators(content, tree)
            errors.extend(generator_issues)

            # import 오류 분석
            import_issues = self._analyze_imports(content)
            errors.extend(import_issues)

        except Exception as e:
            errors.append(
                {
                    "type": "parse_error",
                    "message": f"파일 파싱 실패: {e}",
                    "line": 0,
                    "fixable": False,
                }
            )

        return errors

    def _find_undefined_variables(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """정의되지 않은 변수 찾기"""
        errors = []
        lines = content.split("\n")

        # request 변수 사용 패턴 찾기
        for i, line in enumerate(lines, 1):
            if "request." in line and "def" not in line:
                # 함수 파라미터에 request가 있는지 확인
                func_def = self._find_function_at_line(tree, i)
                if func_def and "request" not in [arg.arg for arg in func_def.args.args]:
                    errors.append(
                        {
                            "type": "undefined_variable",
                            "variable": "request",
                            "line": i,
                            "message": "request 변수가 함수 파라미터에 정의되지 않았습니다",
                            "fixable": True,
                            "fix_type": "add_parameter",
                        }
                    )

        return errors

    def _analyze_async_generators(self, content: str, tree: ast.AST) -> List[Dict[str, Any]]:
        """async generator 리턴 타입 분석"""
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                # 리턴 타입 어노테이션 확인
                if node.returns:
                    returns_str = (
                        ast.unparse(node.returns) if hasattr(ast, "unparse") else str(node.returns)
                    )

                    # async generator인데 dict를 리턴하는 경우
                    if "dict" in returns_str and "AsyncGenerator" not in returns_str:
                        # yield 문이 있는지 확인
                        has_yield = any(isinstance(n, ast.Yield) for n in ast.walk(node))
                        if has_yield:
                            errors.append(
                                {
                                    "type": "wrong_generator_return_type",
                                    "function": node.name,
                                    "line": node.lineno,
                                    "message": f"async generator {node.name}의 리턴 타입이 잘못되었습니다",
                                    "fixable": True,
                                    "fix_type": "fix_generator_return_type",
                                }
                            )

        return errors

    def _analyze_imports(self, content: str) -> List[Dict[str, Any]]:
        """import 오류 분석"""
        errors = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # sse_starlette import 확인
            if "from sse_starlette.sse import" in line:
                errors.append(
                    {
                        "type": "missing_import",
                        "module": "sse_starlette",
                        "line": i,
                        "message": "sse_starlette 모듈 import 실패 가능성",
                        "fixable": False,
                        "fix_type": "check_dependency",
                    }
                )

            # redis import 확인
            if "import redis.asyncio" in line:
                errors.append(
                    {
                        "type": "missing_import",
                        "module": "redis",
                        "line": i,
                        "message": "redis 모듈 import 실패 가능성",
                        "fixable": False,
                        "fix_type": "check_dependency",
                    }
                )

        return errors

    def _find_function_at_line(self, tree: ast.AST, line_no: int) -> ast.FunctionDef | None:
        """특정 라인의 함수 찾기"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.lineno <= line_no <= (node.end_lineno or node.lineno):
                    return node
        return None

    def apply_fixes(self, file_path: str, errors: List[Dict[str, Any]]) -> int:
        """오류들을 자동으로 수정"""
        if not errors:
            return 0

        with open(file_path, "r") as f:
            content = f.read()

        lines = content.split("\n")
        fixes_applied = 0

        for error in errors:
            if not error.get("fixable", False):
                continue

            if error["fix_type"] == "add_parameter":
                # request 파라미터 추가
                if error["variable"] == "request":
                    lines = self._add_request_parameter(lines, error["line"])
                    fixes_applied += 1

            elif error["fix_type"] == "fix_generator_return_type":
                # async generator 리턴 타입 수정
                lines = self._fix_generator_return_type(lines, error["line"])
                fixes_applied += 1

        if fixes_applied > 0:
            with open(file_path, "w") as f:
                f.write("\n".join(lines))

        return fixes_applied

    def _add_request_parameter(self, lines: List[str], line_no: int) -> List[str]:
        """request 파라미터를 함수에 추가"""
        # 해당 라인 근처의 함수 정의 찾기
        for i in range(max(0, line_no - 10), min(len(lines), line_no + 10)):
            line = lines[i]
            if line.strip().startswith("async def") or line.strip().startswith("def"):
                # 함수 시그니처에 request 파라미터 추가
                if "request" not in line:
                    # 파라미터 리스트 찾기
                    paren_start = line.find("(")
                    paren_end = line.find(")", paren_start)

                    if paren_start != -1 and paren_end != -1:
                        before = line[:paren_end]
                        after = line[paren_end:]

                        # 마지막 파라미터 뒤에 request 추가
                        if "," in before:
                            new_before = (
                                before.rsplit(",", 1)[0]
                                + ", request: Request"
                                + before.rsplit(",", 1)[1]
                            )
                        else:
                            new_before = before[:-1] + "request: Request" + before[-1:]

                        lines[i] = new_before + after
                        break

        return lines

    def _fix_generator_return_type(self, lines: List[str], line_no: int) -> List[str]:
        """async generator의 리턴 타입을 올바르게 수정"""
        # 해당 라인 근처에서 함수 정의 찾기
        for i in range(max(0, line_no - 5), min(len(lines), line_no + 5)):
            line = lines[i]
            if ("-> dict" in line or "-> Dict" in line) and ("async def" in line):
                # AsyncGenerator로 변경
                lines[i] = line.replace("-> dict", "-> AsyncGenerator[dict[str, Any], None]")
                lines[i] = lines[i].replace("-> Dict", "-> AsyncGenerator[Dict[str, Any], None]")
                break

        return lines


def main() -> None:
    """메인 실행 함수"""
    debugger = AutoDebugger()

    # 분석할 파일들
    target_files = [
        "packages/afo-core/api/routers/debugging.py",
        "packages/afo-core/api/routers/finance_root.py",
        "packages/afo-core/AFO/rag_rerank.py",
    ]

    total_errors = 0
    total_fixes = 0

    for file_path in target_files:
        if not Path(file_path).exists():
            continue

        print(f"\n🔍 분석 중: {file_path}")

        # 오류 분석
        errors = debugger.analyze_file(file_path)
        total_errors += len(errors)

        print(f"   발견된 오류: {len(errors)}개")

        # 자동 수정 적용
        fixes = debugger.apply_fixes(file_path, errors)
        total_fixes += fixes

        print(f"   적용된 수정: {fixes}개")

        # 수정된 오류들 보고
        for error in errors:
            if error.get("fixable", False):
                print(f"   ✅ {error['type']}: {error['message']}")

    print("\n📊 자동 디버깅 결과:")
    print(f"   총 오류 발견: {total_errors}개")
    print(f"   자동 수정 적용: {total_fixes}개")
    print(f"   수정 성공률: {(total_fixes / total_errors * 100) if total_errors > 0 else 0:.1f}%")


if __name__ == "__main__":
    main()
