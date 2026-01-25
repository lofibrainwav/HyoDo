#!/usr/bin/env python3
"""
AFO 왕국 점진적 오류 수정 시스템
기존 코드의 오류들을 단계적으로 자동 수정
"""

import os
import subprocess
from typing import Any, Dict, List


class GradualErrorFixer:
    """점진적 오류 수정 시스템"""

    def __init__(self) -> None:
        self.error_categories = {
            "critical": [],  # 즉시 수정 필요
            "high": [],  # 중요 오류
            "medium": [],  # 보통 오류
            "low": [],  # 경고 수준
        }
        self.fixed_files = set()

    def analyze_project_errors(self) -> Dict[str, List[Dict[str, Any]]]:
        """프로젝트 전체 오류 분석"""
        print("🔍 프로젝트 전체 오류 분석 중...")

        # Pyright 실행
        pyright_result = subprocess.run(["pyright", "--outputjson"], capture_output=True, text=True)

        # MyPy 실행
        mypy_result = subprocess.run(
            ["mypy", "packages/afo-core", "--no-error-summary"],
            capture_output=True,
            text=True,
        )

        # 오류 분류
        pyright_errors = self._parse_pyright_errors(pyright_result.stdout)
        mypy_errors = self._parse_mypy_errors(mypy_result.stderr)

        return {"pyright": pyright_errors, "mypy": mypy_errors}

    def categorize_errors(
        self, errors: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """오류들을 우선순위별로 분류"""

        for error in errors.get("pyright", []):
            error_type = error.get("type", "")
            message = error.get("message", "")

            # Critical: import 오류, undefined 변수
            if (
                "import" in error_type.lower() and "could not be resolved" in message
            ) or "undefined" in error_type.lower():
                self.error_categories["critical"].append(error)

            # High: 타입 불일치, attribute 오류
            elif "attribute" in error_type.lower() or "type" in error_type.lower():
                self.error_categories["high"].append(error)

            # Medium: 기타 오류
            else:
                self.error_categories["medium"].append(error)

        for error in errors.get("mypy", []):
            if "Function is missing a return type annotation" in error.get("message", ""):
                self.error_categories["medium"].append(error)
            else:
                self.error_categories["low"].append(error)

        return self.error_categories

    def apply_gradual_fixes(self, category: str, batch_size: int = 5) -> Dict[str, Any]:
        """지정된 카테고리의 오류들을 점진적으로 수정"""
        print(f"🔧 {category} 카테고리 오류 점진적 수정 시작 (배치 크기: {batch_size})...")

        errors = self.error_categories.get(category, [])
        if not errors:
            return {
                "status": "no_errors",
                "message": f"{category} 카테고리에 수정할 오류가 없습니다.",
            }

        # 첫 번째 배치만 처리 (점진적 적용)
        batch = errors[:batch_size]
        fixed_count = 0
        failed_count = 0

        for error in batch:
            try:
                if self._apply_single_fix(error):
                    fixed_count += 1
                    print(f"  ✅ {error.get('file', 'unknown')}:{error.get('line', 0)} 수정 완료")
                else:
                    failed_count += 1
                    print(f"  ❌ {error.get('file', 'unknown')}:{error.get('line', 0)} 수정 실패")
            except Exception as e:
                failed_count += 1
                print(f"  ⚠️ {error.get('file', 'unknown')}:{error.get('line', 0)} 예외 발생: {e}")

        return {
            "status": "completed",
            "category": category,
            "batch_size": len(batch),
            "fixed": fixed_count,
            "failed": failed_count,
            "remaining": len(errors) - len(batch),
            "success_rate": (fixed_count / len(batch) * 100) if batch else 0,
        }

    def _apply_single_fix(self, error: Dict[str, Any]) -> bool:
        """단일 오류 수정"""
        file_path = error.get("file", "")
        if not file_path or not os.path.exists(file_path):
            return False

        error.get("type", "")
        message = error.get("message", "")

        # 타입 어노테이션 누락 수정
        if "missing a return type annotation" in message:
            return self._add_return_type_annotation(file_path, error.get("line", 0))

        # AsyncGenerator 타입 수정
        elif "AsyncGenerator" in message and "not defined" in message:
            return self._add_async_generator_import(file_path)

        return False

    def _add_return_type_annotation(self, file_path: str, line_no: int) -> bool:
        """리턴 타입 어노테이션 추가"""
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            # 해당 라인 주변에서 함수 정의 찾기
            for i in range(max(0, line_no - 5), min(len(lines), line_no + 5)):
                line = lines[i].strip()
                if line.startswith("def ") and "->" not in line:
                    # 파라미터 끝에 리턴 타입 추가
                    if ")" in line and not line.endswith(":"):
                        lines[i] = line.replace("):", ") -> Any:")
                        with open(file_path, "w") as f:
                            f.writelines(lines)
                        return True
        except Exception:
            pass
        return False

    def _add_async_generator_import(self, file_path: str) -> bool:
        """AsyncGenerator import 추가"""
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # 이미 import되어 있는지 확인
            if "from typing import" in content and "AsyncGenerator" in content:
                return True

            # typing import 라인 찾기
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("from typing import"):
                    # AsyncGenerator 추가
                    if "AsyncGenerator" not in line:
                        lines[i] = (
                            line.replace(
                                "from typing import ",
                                "from typing import AsyncGenerator, ",
                            )
                            if not line.endswith(" import (")
                            else line
                        )
                        with open(file_path, "w") as f:
                            f.write("\n".join(lines))
                        return True

            # typing import가 없으면 추가
            import_lines = [
                line
                for line in lines
                if line.strip().startswith("import") or line.strip().startswith("from")
            ]
            if import_lines:
                last_import_idx = max(
                    i for i, line in enumerate(lines) if line.strip().startswith(("import", "from"))
                )
                lines.insert(last_import_idx + 1, "from typing import AsyncGenerator")
                with open(file_path, "w") as f:
                    f.write("\n".join(lines))
                return True

        except Exception:
            pass
        return False

    def _parse_pyright_errors(self, output: str) -> List[Dict[str, Any]]:
        """Pyright 출력 파싱"""
        errors = []
        try:
            import json

            data = json.loads(output)
            for file_path, file_errors in data.get("generalDiagnostics", {}).items():
                for error in file_errors:
                    errors.append(
                        {
                            "file": file_path,
                            "line": error.get("range", {}).get("start", {}).get("line", 0),
                            "type": error.get("rule", "unknown"),
                            "message": error.get("message", ""),
                            "severity": error.get("severity", "error"),
                        }
                    )
        except:
            # JSON 파싱 실패 시 텍스트 파싱
            for line in output.split("\n"):
                if ".py:" in line and " - " in line:
                    try:
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            file_part, line_part = parts[0], parts[1]
                            message_part = parts[2]
                            errors.append(
                                {
                                    "file": file_part,
                                    "line": int(line_part.split()[0]),
                                    "type": "pyright_error",
                                    "message": message_part.strip(),
                                    "severity": "error",
                                }
                            )
                    except:
                        continue
        return errors

    def _parse_mypy_errors(self, output: str) -> List[Dict[str, Any]]:
        """MyPy 출력 파싱"""
        errors = []
        for line in output.split("\n"):
            if ".py:" in line and "error:" in line:
                try:
                    file_part, rest = line.split(":", 1)
                    line_part, message_part = rest.split(" error: ", 1)
                    errors.append(
                        {
                            "file": file_part,
                            "line": int(line_part),
                            "type": "mypy_error",
                            "message": message_part.strip(),
                            "severity": "error",
                        }
                    )
                except:
                    continue
        return errors


def main() -> None:
    """메인 실행 함수"""
    fixer = GradualErrorFixer()

    print("🚀 AFO 왕국 점진적 오류 수정 시스템 시작\n")

    # 1. 오류 분석
    print("1️⃣ 오류 분석 단계")
    errors = fixer.analyze_project_errors()
    total_errors = sum(len(err_list) for err_list in errors.values())
    print(f"   발견된 총 오류: {total_errors}개")

    # 2. 오류 분류
    print("\n2️⃣ 오류 분류 단계")
    categories = fixer.categorize_errors(errors)
    for category, cat_errors in categories.items():
        print(f"   {category}: {len(cat_errors)}개")

    # 3. Critical 오류 우선 수정
    print("\n3️⃣ Critical 오류 우선 수정")
    result = fixer.apply_gradual_fixes("critical", batch_size=3)
    print(f"   결과: {result.get('fixed', 0)}/{result.get('batch_size', 0)}개 수정 성공")
    print(f"   남은 오류: {result.get('remaining', 0)}개")

    # 4. 결과 보고
    print("\n4️⃣ 결과 보고")
    print(f"   수정된 파일 수: {len(fixer.fixed_files)}개")
    print(f"   다음 권장 작업: High 우선순위 오류 {len(categories.get('high', []))}개 수정")

    print("\n✅ 점진적 오류 수정 시스템 실행 완료")


if __name__ == "__main__":
    main()
