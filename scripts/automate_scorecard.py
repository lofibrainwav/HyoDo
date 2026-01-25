#!/usr/bin/env python3
"""
AFO Kingdom - Automated Scorecard
眞善美孝永 자동 스코어링 스크립트

사령관님 철학 SSOT: 眞35% + 善35% + 美30% = 100%
"""

from __future__ import annotations

import ast
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScoreResult:
    """점수 결과"""

    score: float
    max_score: float
    details: str


class AutomatedScorecard:
    """眞善美孝永 자동 스코어링"""

    def __init__(self, project_dir: str = "packages/afo-core") -> None:
        self.project_dir = Path(project_dir)
        self.weights = {
            "truth": 0.35,
            "goodness": 0.35,
            "beauty": 0.30,
        }

    def run_all(self) -> dict:
        """모든 메트릭 실행"""
        results = {
            "truth": self._calculate_truth(),
            "goodness": self._calculate_goodness(),
            "beauty": self._calculate_beauty(),
            "serenity": self._calculate_serenity(),  # ε 메타 원리
            "eternity": self._calculate_eternity(),  # ε 메타 원리
        }

        # 가중 총점 (眞善美만)
        total = sum(
            results[k].score / results[k].max_score * self.weights.get(k, 0) * 100
            for k in ["truth", "goodness", "beauty"]
        )

        return {"scores": results, "total": round(total, 1), "max": 100}

    def _calculate_truth(self) -> ScoreResult:
        """眞 (Truth) - 타입 안전성, 테스트 커버리지"""
        score: float = 0.0
        details: list[str] = []

        # 1. MyPy 검사 (40점)
        mypy_score = self._run_mypy()
        score += mypy_score
        details.append(f"MyPy: {mypy_score}/40")

        # 2. 타입 힌트 비율 (35점)
        type_score = self._check_type_hints()
        score += type_score
        details.append(f"타입힌트: {type_score}/35")

        # 3. 테스트 파일 존재 (25점)
        test_score = self._check_tests()
        score += test_score
        details.append(f"테스트: {test_score}/25")

        return ScoreResult(score, 100, " | ".join(details))

    def _calculate_goodness(self) -> ScoreResult:
        """善 (Goodness) - 에러 처리, 보안 패턴"""
        score = 0
        details = []

        # 1. Try/Except 비율 (40점)
        error_score = self._check_error_handling()
        score += error_score
        details.append(f"에러처리: {error_score}/40")

        # 2. 로깅 패턴 (35점)
        logging_score = self._check_logging()
        score += logging_score
        details.append(f"로깅: {logging_score}/35")

        # 3. 검증 패턴 (25점)
        validation_score = self._check_validation()
        score += validation_score
        details.append(f"검증: {validation_score}/25")

        return ScoreResult(score, 100, " | ".join(details))

    def _calculate_beauty(self) -> ScoreResult:
        """美 (Beauty) - 모듈화, 네이밍 일관성"""
        score = 0
        details = []

        # 1. 함수당 라인 수 (40점)
        modularity_score = self._check_modularity()
        score += modularity_score
        details.append(f"모듈화: {modularity_score}/40")

        # 2. 네이밍 일관성 (35점)
        naming_score = self._check_naming()
        score += naming_score
        details.append(f"네이밍: {naming_score}/35")

        # 3. 코드 구조 (25점)
        structure_score = self._check_structure()
        score += structure_score
        details.append(f"구조: {structure_score}/25")

        return ScoreResult(score, 100, " | ".join(details))

    def _calculate_serenity(self) -> ScoreResult:
        """孝 (Serenity) - 비동기, 자동화 (ε 메타 원리)"""
        score = 0
        details = []

        # 비동기 패턴 검사 (50점)
        async_score = self._check_async()
        score += async_score
        details.append(f"비동기: {async_score}/50")

        # 자동화 패턴 (50점)
        auto_score = self._check_automation()
        score += auto_score
        details.append(f"자동화: {auto_score}/50")

        return ScoreResult(score, 100, " | ".join(details))

    def _calculate_eternity(self) -> ScoreResult:
        """永 (Eternity) - 문서화, 버전 관리 (ε 메타 원리)"""
        score = 0
        details = []

        # Docstring 비율 (50점)
        doc_score = self._check_docstrings()
        score += doc_score
        details.append(f"문서화: {doc_score}/50")

        # 주석 밀도 (50점)
        comment_score = self._check_comments()
        score += comment_score
        details.append(f"주석: {comment_score}/50")

        return ScoreResult(score, 100, " | ".join(details))

    # === Helper Methods ===

    def _get_python_files(self) -> list[Path]:
        """Python 파일 목록"""
        if not self.project_dir.exists():
            return []
        return list(self.project_dir.rglob("*.py"))

    def _parse_file(self, path: Path) -> ast.AST | None:
        """AST 파싱"""
        try:
            return ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def _run_mypy(self) -> float:
        """MyPy 실행 (0-40점) - venv 환경 사용"""
        try:
            # MyPy needs packages/afo-core for proper import resolution
            mypy_path = self.project_dir
            if self.project_dir.name == "AFO":
                mypy_path = self.project_dir.parent  # Go up to packages/afo-core

            # Use absolute path for venv (script may run from different cwd)
            script_dir = Path(__file__).parent.parent  # Go up from scripts/ to repo root
            venv_activate = script_dir / ".venv" / "bin" / "activate"

            if venv_activate.exists():
                cmd = f"source {venv_activate} && mypy {mypy_path} --ignore-missing-imports"
                result = subprocess.run(
                    cmd,
                    check=False,
                    shell=True,
                    executable="/bin/bash",
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=str(script_dir),  # Run from repo root
                )
            else:
                # Fallback to system mypy
                result = subprocess.run(
                    ["mypy", str(mypy_path), "--ignore-missing-imports"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

            error_count = result.stdout.count("error:")
            if error_count == 0:
                return 40
            return max(0, 40 - error_count * 2)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return 20  # MyPy 없으면 기본점

    def _check_type_hints(self) -> float:
        """타입 힌트 비율 (0-35점)"""
        total_funcs = 0
        typed_funcs = 0

        for path in self._get_python_files():
            tree = self._parse_file(path)
            if not tree:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    total_funcs += 1
                    if node.returns or any(arg.annotation for arg in node.args.args):
                        typed_funcs += 1

        ratio = typed_funcs / max(1, total_funcs)
        return round(ratio * 35, 1)

    def _check_tests(self) -> float:
        """테스트 파일 존재 (0-25점)"""
        test_files = list(self.project_dir.rglob("test_*.py"))
        test_files += list(self.project_dir.rglob("*_test.py"))
        if len(test_files) >= 10:
            return 25
        return min(25, len(test_files) * 2.5)

    def _check_error_handling(self) -> float:
        """Try/Except 비율 (0-40점)"""
        total_funcs = 0
        error_handling = 0

        for path in self._get_python_files():
            tree = self._parse_file(path)
            if not tree:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    total_funcs += 1
                    if any(isinstance(n, ast.Try) for n in ast.walk(node)):
                        error_handling += 1

        ratio = error_handling / max(1, total_funcs)
        return round(min(1.0, ratio * 2) * 40, 1)  # 50% 커버시 만점

    def _check_logging(self) -> float:
        """로깅 패턴 (0-35점)"""
        logging_count = 0
        for path in self._get_python_files():
            content = path.read_text(encoding="utf-8", errors="ignore")
            logging_count += content.count("logging") + content.count("logger")

        return min(35, logging_count * 0.5)

    def _check_validation(self) -> float:
        """검증 패턴 (0-25점)"""
        validation_count = 0
        for path in self._get_python_files():
            content = path.read_text(encoding="utf-8", errors="ignore")
            validation_count += (
                content.count("pydantic")
                + content.count("BaseModel")
                + content.count("validate")
                + content.count("dataclass")
            )
        return min(25, validation_count * 0.5)

    def _check_modularity(self) -> float:
        """함수당 라인 수 (0-40점)"""
        total_lines = 0
        func_count = 0

        for path in self._get_python_files():
            tree = self._parse_file(path)
            if not tree:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            total_lines += len(content.splitlines())
            func_count += sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))

        if func_count == 0:
            return 20

        avg_lines = total_lines / func_count
        # 30줄이 이상적, 100줄 이상은 나쁨
        if avg_lines <= 30:
            return 40
        return max(0, 40 - (avg_lines - 30) * 0.5)

    def _check_naming(self) -> float:
        """네이밍 일관성 (0-35점)"""
        snake_case = 0
        camel_case = 0

        for path in self._get_python_files():
            tree = self._parse_file(path)
            if not tree:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if "_" in node.id and node.id.islower():
                        snake_case += 1
                    elif node.id[0].islower() and any(c.isupper() for c in node.id[1:]):
                        # Only count lowerCamelCase as violation
                        camel_case += 1

        total = snake_case + camel_case
        ratio = snake_case / max(1, total)
        return round(ratio * 35, 1)

    def _check_structure(self) -> float:
        """코드 구조 (0-25점)"""
        func_count = 0
        class_count = 0

        for path in self._get_python_files():
            tree = self._parse_file(path)
            if not tree:
                continue
            func_count += sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
            class_count += sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))

        # 함수와 클래스가 적절히 있으면 좋음
        if func_count >= 10 and class_count >= 3:
            return 25
        return min(25, func_count * 0.5 + class_count * 2)

    def _check_async(self) -> float:
        """비동기 패턴 (0-50점)"""
        async_count = 0
        for path in self._get_python_files():
            content = path.read_text(encoding="utf-8", errors="ignore")
            async_count += content.count("async def") + content.count("await")
        return min(50, async_count * 0.5)

    def _check_automation(self) -> float:
        """자동화 패턴 (0-50점)"""
        auto_count = 0
        for path in self._get_python_files():
            content = path.read_text(encoding="utf-8", errors="ignore")
            auto_count += (
                content.count("schedule")
                + content.count("automate")
                + content.count("AntiGravity")
                + content.count("rollback")
            )
        return min(50, auto_count * 2)

    def _check_docstrings(self) -> float:
        """Docstring 비율 (0-50점)"""
        total_funcs = 0
        documented = 0

        for path in self._get_python_files():
            tree = self._parse_file(path)
            if not tree:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    total_funcs += 1
                    if ast.get_docstring(node):
                        documented += 1

        ratio = documented / max(1, total_funcs)
        return round(ratio * 50, 1)

    def _check_comments(self) -> float:
        """주석 밀도 (0-50점)"""
        total_lines = 0
        comment_lines = 0

        for path in self._get_python_files():
            content = path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            total_lines += len(lines)
            comment_lines += sum(1 for line in lines if line.strip().startswith("#"))

        ratio = comment_lines / max(1, total_lines)
        # 10% 주석이면 만점
        return min(50, ratio * 500)


def main() -> None:
    """메인 함수"""
    project_dir = sys.argv[1] if len(sys.argv) > 1 else "packages/afo-core"

    scorer = AutomatedScorecard(project_dir)
    results = scorer.run_all()

    print("🏰 AFO 왕국 자동 스코어카드")
    print("眞善美孝永 (Truth·Goodness·Beauty·Serenity·Eternity)")
    print("=" * 60)
    print(f"총점: {results['total']}/{results['max']}")
    print()

    pillar_names = {
        "truth": ("眞 (Truth)", "타입 안전성, 정확성"),
        "goodness": ("善 (Goodness)", "안전성, 윤리성"),
        "beauty": ("美 (Beauty)", "코드 품질, 모듈화"),
        "serenity": ("孝 (Serenity)", "운영 안정성 [ε]"),
        "eternity": ("永 (Eternity)", "문서화 [ε]"),
    }

    for key, result in results["scores"].items():
        name, desc = pillar_names[key]
        pct = result.score / result.max_score * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"{name:<12} {pct:5.1f}% [{bar}] {desc}")
        print(f"             └─ {result.details}")
    print()


if __name__ == "__main__":
    main()
