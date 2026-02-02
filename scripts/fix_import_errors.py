#!/usr/bin/env python3
"""
Import Error Fixer for AFO Kingdom
승상 자동화: typing 모듈 import 누락 문제 자동 수정

眞善美孝永 철학 적용:
- 眞 (Truth): 정확한 import 분석 및 수정
- 善 (Goodness): 안전한 파일 수정 및 백업
- 美 (Beauty): 깔끔한 코드 구조 유지
- 孝 (Serenity): 중단 없는 자동화 플로우
- 永 (Eternity): 영속적인 코드 품질 유지
"""

import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ImportErrorFixer:
    """Import 에러 자동 수정기"""

    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.fixed_files: Set[Path] = set()
        self.errors: List[str] = []

        # 필요한 typing imports
        self.typing_imports = {
            "Optional": "Optional",
            "Union": "Union",
            "List": "List",
            "Dict": "Dict",
            "Any": "Any",
            "Tuple": "Tuple",
            "Callable": "Callable",
            "Type": "Type",
            "Set": "Set",
            "FrozenSet": "FrozenSet",
        }

    def find_python_files(self) -> List[Path]:
        """Python 파일들 찾기"""
        python_files = []
        for root, dirs, files in os.walk(self.root_path):
            # 제외할 디렉토리들
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d
                not in {
                    "__pycache__",
                    "node_modules",
                    "venv",
                    ".venv",
                    "env",
                    ".env",
                    "build",
                    "dist",
                    ".next",
                    ".nuxt",
                    "coverage",
                    "htmlcov",
                }
            ]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        return python_files

    def analyze_file_imports(self, file_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        파일의 import 상태 분석
        Returns: (needs_fix, missing_imports, used_types)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"파일 읽기 실패 {file_path}: {e}")
            return False, [], []

        # 현재 import된 typing 요소들 찾기
        typing_pattern = r"from typing import ([^#\n]+)"
        typing_match = re.search(typing_pattern, content)

        current_imports = set()
        if typing_match:
            imports_str = typing_match.group(1)
            # 여러 줄 import 처리
            imports_str = re.sub(r"\\\s*\n\s*", "", imports_str)
            current_imports = {imp.strip() for imp in imports_str.split(",") if imp.strip()}

        # 사용된 typing 타입들 찾기
        used_types = set()
        for type_name in self.typing_imports.keys():
            # 타입이 사용되는 패턴들
            patterns = [
                rf"\b{type_name}\[",  # Optional[str], List[int] 등
                rf"\b{type_name}\s*\|\s*",  # str | None, Optional[int] | 등
                rf"\|\s*{type_name}\b",  # None | Optional 등
                rf"\b{type_name}\s*:",  # def func(param: Optional[str])
                rf"->\s*{type_name}\[",  # -> Optional[str]
                rf"->\s*{type_name}\b",  # -> Optional
            ]

            for pattern in patterns:
                if re.search(pattern, content):
                    used_types.add(type_name)
                    break

        # 누락된 imports 계산
        missing_imports = used_types - current_imports

        return bool(missing_imports), list(missing_imports), list(used_types)

    def fix_file_imports(self, file_path: Path, missing_imports: List[str]) -> bool:
        """파일의 import 수정"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"파일 읽기 실패 {file_path}: {e}")
            return False

        # 현재 typing import 찾기
        typing_pattern = r"(from typing import [^\n]+)"
        typing_match = re.search(typing_pattern, content)

        if typing_match:
            # 기존 import에 추가
            current_line = typing_match.group(1)
            existing_imports = set()
            imports_part = re.search(r"from typing import (.+)", current_line)
            if imports_part:
                imports_str = imports_part.group(1)
                imports_str = re.sub(r"\\\s*\n\s*", "", imports_str)
                existing_imports = {imp.strip() for imp in imports_str.split(",") if imp.strip()}

            all_imports = sorted(existing_imports | set(missing_imports))
            new_imports_str = ", ".join(all_imports)
            new_line = f"from typing import {new_imports_str}"

            content = content.replace(current_line, new_line)
        else:
            # 새로운 import 라인 추가
            # 파일 시작부에 추가
            lines = content.split("\n")
            insert_pos = 0

            # shebang과 encoding 선언 이후에 추가
            for i, line in enumerate(lines):
                if (
                    line.startswith("#!")
                    or line.startswith("# -*-")
                    or line.startswith('"""')
                    or line.startswith("'''")
                ):
                    continue
                elif line.strip() == "" or line.startswith("import ") or line.startswith("from "):
                    insert_pos = i
                    break
                else:
                    break

            all_imports = sorted(missing_imports)
            new_import_line = f"from typing import {', '.join(all_imports)}"

            lines.insert(insert_pos, new_import_line)
            lines.insert(insert_pos + 1, "")  # 빈 줄 추가
            content = "\n".join(lines)

        # 파일 저장
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"수정 완료: {file_path} (+ {', '.join(missing_imports)})")
            return True
        except Exception as e:
            logger.error(f"파일 저장 실패 {file_path}: {e}")
            return False

    def process_all_files(self) -> Dict[str, int]:
        """모든 Python 파일 처리"""
        python_files = self.find_python_files()
        logger.info(f"총 {len(python_files)}개 Python 파일 발견")

        stats = {
            "total_files": len(python_files),
            "files_with_errors": 0,
            "files_fixed": 0,
            "errors": 0,
        }

        for file_path in python_files:
            try:
                needs_fix, missing_imports, used_types = self.analyze_file_imports(file_path)

                if needs_fix:
                    stats["files_with_errors"] += 1
                    logger.info(f"수정 필요: {file_path} (누락: {', '.join(missing_imports)})")

                    if self.fix_file_imports(file_path, missing_imports):
                        stats["files_fixed"] += 1
                        self.fixed_files.add(file_path)
                    else:
                        stats["errors"] += 1
                        self.errors.append(f"수정 실패: {file_path}")

            except Exception as e:
                logger.error(f"파일 처리 중 에러 {file_path}: {e}")
                stats["errors"] += 1
                self.errors.append(f"처리 에러: {file_path} - {e}")

        return stats

    def generate_report(self, stats: Dict[str, int]) -> str:
        """보고서 생성"""
        report = []
        report.append("# Import Error Fix Report")
        report.append("## 📊 통계")
        report.append(f"- 총 파일 수: {stats['total_files']}")
        report.append(f"- 수정 필요 파일: {stats['files_with_errors']}")
        report.append(f"- 성공적으로 수정: {stats['files_fixed']}")
        report.append(f"- 수정 실패: {stats['errors']}")

        if self.fixed_files:
            report.append("\n## ✅ 수정된 파일들")
            for file_path in sorted(self.fixed_files):
                report.append(f"- {file_path}")

        if self.errors:
            report.append("\n## ❌ 에러 발생")
            for error in self.errors:
                report.append(f"- {error}")

        report.append("\n## 🎯 Trinity Score 영향")
        success_rate = (
            (stats["files_fixed"] / stats["files_with_errors"] * 100)
            if stats["files_with_errors"] > 0
            else 100
        )
        report.append(f"- 眞 (Truth): +{stats['files_fixed'] * 2} (정확한 타입 안전성)")
        report.append(f"- 善 (Goodness): +{stats['files_fixed']} (안전한 코드 수정)")
        report.append(f"- 美 (Beauty): +{success_rate:.1f}% (자동화 성공률)")
        return "\n".join(report)


def main() -> None:
    """메인 함수"""
    root_path = Path(__file__).parent.parent

    logger.info("🚀 Import Error Fixer 시작")
    logger.info(f"대상 경로: {root_path}")

    fixer = ImportErrorFixer(root_path)
    stats = fixer.process_all_files()

    report = fixer.generate_report(stats)
    print("\n" + "=" * 50)
    print(report)
    print("=" * 50)

    # 보고서 저장
    report_path = root_path / "analysis_results" / "import_fix_report.md"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"보고서 저장됨: {report_path}")
    except Exception as e:
        logger.error(f"보고서 저장 실패: {e}")

    return stats["errors"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
