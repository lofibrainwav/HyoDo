#!/usr/bin/env python3
"""
AFO 왕국 Context7 로그 분류기
대용량 로그를 Context7 기반으로 분류하여 문제 파악을 쉽게 함

Context7 카테고리:
- SYNTAX: Python 구문 오류 (Expected indented block, invalid-syntax 등)
- IMPORT: 모듈/함수 import 누락 (is not defined, ImportError 등)
- COMPATIBILITY: Python 버전 호환성 문제 (Union/Optional not defined 등)
- TYPE: 타입 시스템 오류 (reportAttributeAccessIssue 등)
- UNKNOWN: 분류되지 않은 기타 오류
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple


class ErrorCategory(Enum):
    """Context7 에러 카테고리"""

    SYNTAX = "SYNTAX"
    IMPORT = "IMPORT"
    COMPATIBILITY = "COMPATIBILITY"
    TYPE = "TYPE"
    UNKNOWN = "UNKNOWN"


@dataclass
class Context7Pattern:
    """Context7 패턴 정의"""

    category: ErrorCategory
    patterns: List[str]
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    examples: List[str]


@dataclass
class ClassifiedError:
    """분류된 에러"""

    line_number: int
    error_text: str
    category: ErrorCategory
    confidence: float
    root_cause: str
    solution_hint: str


class Context7Classifier:
    """Context7 기반 로그 분류기"""

    # Context7 패턴 정의
    PATTERNS = [
        Context7Pattern(
            category=ErrorCategory.SYNTAX,
            patterns=[
                r"Expected an indented block",
                r"invalid-syntax",
                r"Simple statements must be separated",
                r"Expected.*newline",
                r"Expected.*semicolon",
                r"unexpected indent",
                r"unindent does not match",
            ],
            priority="CRITICAL",
            description="Python 구문 및 들여쓰기 오류",
            examples=[
                "Expected an indented block after 'if' statement",
                "invalid-syntax: Simple statements must be separated by newlines or semicolons",
            ],
        ),
        Context7Pattern(
            category=ErrorCategory.IMPORT,
            patterns=[
                r".*is not defined",
                r"ImportError",
                r"Module level import not at top",
                r"reportMissingImports",
                r"reportUndefinedVariable",
                r"No module named",
                r"cannot import name",
            ],
            priority="HIGH",
            description="모듈/함수 import 누락 또는 정의되지 않음",
            examples=[
                "'Optional' is not defined",
                "ImportError: No module named 'typing'",
            ],
        ),
        Context7Pattern(
            category=ErrorCategory.COMPATIBILITY,
            patterns=[
                r"Union.*not defined",
                r"Optional.*not defined",
                r"TypeVar.*not defined",
                r"reportInvalidTypeForm",
                r"PEP 585",
                r"Python 3\.\d+ compatibility",
            ],
            priority="CRITICAL",
            description="Python 버전 호환성 및 타입 힌팅 문제",
            examples=[
                "'Union' is not defined",
                "reportInvalidTypeForm: Variable not allowed in type expression",
            ],
        ),
        Context7Pattern(
            category=ErrorCategory.TYPE,
            patterns=[
                r"reportAttributeAccessIssue",
                r"reportGeneralTypeIssues",
                r"Variable not allowed in type expression",
                r"type annotation",
                r"mypy",
                r"type.*check",
            ],
            priority="MEDIUM",
            description="타입 시스템 관련 오류",
            examples=[
                "reportAttributeAccessIssue: 'Optional' is not a known attribute of module 'ast'",
                "Variable not allowed in type expression",
            ],
        ),
        Context7Pattern(
            category=ErrorCategory.UNKNOWN,
            patterns=[r".*"],
            priority="LOW",
            description="분류되지 않은 기타 오류",
            examples=["기타 모든 오류"],
        ),
    ]

    @classmethod
    def classify_error(cls, error_line: str) -> Tuple[ErrorCategory, float]:
        """
        에러 라인을 Context7 카테고리로 분류

        Returns:
            (카테고리, 신뢰도) 튜플
        """
        for pattern in cls.PATTERNS:
            for regex_pattern in pattern.patterns:
                if re.search(regex_pattern, error_line, re.IGNORECASE):
                    # UNKNOWN 패턴은 마지막에만 매칭되도록
                    if pattern.category == ErrorCategory.UNKNOWN:
                        continue

                    # 신뢰도 계산 (패턴 매칭 강도에 따라)
                    confidence = 0.8  # 기본 신뢰도

                    # 더 구체적인 패턴일수록 신뢰도 높임
                    if (
                        "Expected an indented block" in regex_pattern
                        and "Expected an indented block" in error_line
                    ):
                        confidence = 0.95
                    elif "is not defined" in regex_pattern and "is not defined" in error_line:
                        confidence = 0.90
                    elif "Union" in error_line and "not defined" in error_line:
                        confidence = 0.95

                    return pattern.category, confidence

        # 아무 패턴에도 매칭되지 않으면 UNKNOWN
        return ErrorCategory.UNKNOWN, 0.3

    @classmethod
    def analyze_log_lines(cls, lines: List[str]) -> Dict[str, List[ClassifiedError]]:
        """
        로그 라인들을 분석하여 Context7 기반으로 분류

        Returns:
            카테고리별 ClassifiedError 리스트 딕셔너리
        """
        classified_errors = {
            "SYNTAX": [],
            "IMPORT": [],
            "COMPATIBILITY": [],
            "TYPE": [],
            "UNKNOWN": [],
        }

        for i, line in enumerate(lines, 1):
            if not line.strip() or line.startswith("#"):
                continue

            category, confidence = cls.classify_error(line)
            root_cause = cls._infer_root_cause(category, line)
            solution_hint = cls._suggest_solution(category, line)

            error = ClassifiedError(
                line_number=i,
                error_text=line.strip(),
                category=category,
                confidence=confidence,
                root_cause=root_cause,
                solution_hint=solution_hint,
            )

            classified_errors[category.value].append(error)

        return classified_errors

    @classmethod
    def _infer_root_cause(cls, category: ErrorCategory, error_line: str) -> str:
        """근본 원인 추론"""
        causes = {
            ErrorCategory.SYNTAX: [
                "Python 호환성 스크립트 실행 실패",
                "들여쓰기 규칙 변경으로 인한 구문 오류",
                "코드 포맷터와의 충돌",
            ],
            ErrorCategory.IMPORT: [
                "typing 모듈 import 누락",
                "모듈 경로 변경",
                "서드파티 라이브러리 설치 누락",
            ],
            ErrorCategory.COMPATIBILITY: [
                "Python 버전 업그레이드로 인한 하위호환성 문제",
                "Union Syntax → Optional[Union] 변환 누락",
                "타입 힌팅 방식 변경",
            ],
            ErrorCategory.TYPE: [
                "타입 체커 버전 차이",
                "타입 annotation 방식 변경",
                "mypy 설정 변경",
            ],
            ErrorCategory.UNKNOWN: ["분류되지 않은 오류", "추가 패턴 분석 필요"],
        }

        # 에러 라인 내용에 따라 더 구체적인 원인 추론
        if "indented block" in error_line.lower():
            return "Python 들여쓰기 규칙 변경으로 인한 자동 수정 실패"
        elif "union" in error_line.lower() and "not defined" in error_line.lower():
            return "Union 타입 import 누락 - Python 3.9+ 호환성 문제"
        elif "optional" in error_line.lower() and "not defined" in error_line.lower():
            return "Optional 타입 import 누락 - typing 모듈 import 부족"

        # 기본 원인 반환
        return causes[category][0] if causes[category] else "원인 분석 필요"

    @classmethod
    def _suggest_solution(cls, category: ErrorCategory, error_line: str) -> str:
        """해결 방안 제안"""
        solutions = {
            ErrorCategory.SYNTAX: [
                "Python 호환성 변환 스크립트 재실행",
                "들여쓰기 규칙 수동 검토",
                "코드 포맷터 설정 확인",
            ],
            ErrorCategory.IMPORT: [
                "from typing import Optional, Union 추가",
                "필요한 모듈 import 확인",
                "PYTHONPATH 환경변수 검토",
            ],
            ErrorCategory.COMPATIBILITY: [
                "Python 버전별 조건부 import 구현",
                "TYPE_CHECKING 블록 활용",
                "호환성 라이브러리 사용 (typing_extensions)",
            ],
            ErrorCategory.TYPE: [
                "타입 체커 설정 검토",
                "타입 annotation 방식 통일",
                "mypy.ini 설정 확인",
            ],
            ErrorCategory.UNKNOWN: [
                "에러 로그 상세 분석",
                "커뮤니티/문서 검색",
                "개발팀 문의",
            ],
        }

        # 구체적인 해결책 제시
        if "indented block" in error_line.lower():
            return "자동 들여쓰기 수정 도구 실행 또는 수동 수정"
        elif "union" in error_line.lower():
            return "from typing import Union 추가 또는 typing_extensions 사용"
        elif "optional" in error_line.lower():
            return "from typing import Optional 추가"

        return solutions[category][0] if solutions[category] else "해결 방안 분석 필요"

    @classmethod
    def generate_summary_report(cls, classified_errors: Dict[str, List[ClassifiedError]]) -> str:
        """Context7 기반 요약 보고서 생성"""
        total_errors = sum(len(errors) for errors in classified_errors.values())

        report = []
        report.append("# AFO 왕국 Context7 로그 분류 보고서\n")
        report.append("## 📊 분석 요약\n")
        report.append(f"- 총 에러 수: {total_errors}\n")

        # 카테고리별 통계
        report.append("\n## 🏷️ 카테고리별 분포\n")
        for category, errors in classified_errors.items():
            if errors:
                avg_confidence = sum(e.confidence for e in errors) / len(errors)
                report.append(
                    f"### {category} ({len(errors)}개, 평균 신뢰도: {avg_confidence:.2f})\n"
                )

                # 우선순위별 그룹화
                priorities = {}
                for error in errors:
                    pattern = next((p for p in cls.PATTERNS if p.category.value == category), None)
                    priority = pattern.priority if pattern else "UNKNOWN"
                    if priority not in priorities:
                        priorities[priority] = []
                    priorities[priority].append(error)

                for priority, pri_errors in priorities.items():
                    if pri_errors:
                        report.append(f"#### {priority} 우선순위 ({len(pri_errors)}개)\n")
                        for error in pri_errors[:5]:  # 최대 5개만 표시
                            report.append(
                                f"- **라인 {error.line_number}**: {error.error_text[:100]}...\n"
                            )
                            report.append(f"  - 근본 원인: {error.root_cause}\n")
                            report.append(f"  - 해결 방안: {error.solution_hint}\n")
                        report.append("\n")

        # 우선순위별 조치 권고
        report.append("\n## 🎯 우선순위별 조치 권고\n")

        critical_count = len(classified_errors.get("SYNTAX", [])) + len(
            classified_errors.get("COMPATIBILITY", [])
        )
        high_count = len(classified_errors.get("IMPORT", []))

        if critical_count > 0:
            report.append(f"### 🚨 긴급 조치 필요 (CRITICAL: {critical_count}개)\n")
            report.append("- 배포 차단 가능성 높음\n")
            report.append("- 즉시 수정 권장\n")
            report.append("- 코드 실행 불가 상태일 수 있음\n")

        if high_count > 0:
            report.append(f"### ⚠️ 빠른 조치 필요 (HIGH: {high_count}개)\n")
            report.append("- 기능 동작에 영향 가능\n")
            report.append("- 다음 배포 전 수정 권장\n")

        report.append("\n## 📋 상세 분석 결과\n")
        report.append("각 카테고리의 구체적인 에러 내용과 해결 방안을 위에서 확인하세요.\n")

        return "".join(report)


def main() -> None:
    """CLI 인터페이스"""
    import argparse

    parser = argparse.ArgumentParser(description="AFO 왕국 Context7 로그 분류기")
    parser.add_argument("log_file", help="분석할 로그 파일")
    parser.add_argument("--output", default="context7_analysis_report.md", help="출력 보고서 파일")
    parser.add_argument("--summary-only", action="store_true", help="요약 보고서만 생성")

    args = parser.parse_args()

    # 로그 파일 읽기
    try:
        with open(args.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ 로그 파일을 찾을 수 없습니다: {args.log_file}")
        return

    print(f"🔍 Context7 로그 분석 시작: {args.log_file}")
    print(f"📊 분석할 라인 수: {len(lines)}")

    # Context7 분류 수행
    classified_errors = Context7Classifier.analyze_log_lines(lines)

    # 총 에러 수 계산
    total_errors = sum(len(errors) for errors in classified_errors.values())
    print(f"✅ 분류 완료: {total_errors}개 에러 발견")

    # 카테고리별 통계 출력
    print("\n🏷️ 카테고리별 분포:")
    for category, errors in classified_errors.items():
        if errors:
            avg_confidence = sum(e.confidence for e in errors) / len(errors)
            print(f"  {category}: {len(errors)}개 (평균 신뢰도: {avg_confidence:.2f})")

    # 보고서 생성
    if not args.summary_only:
        report = Context7Classifier.generate_summary_report(classified_errors)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n📄 보고서 생성 완료: {args.output}")

    # 주요 해결 전략 출력
    print("\n🎯 주요 해결 전략:")
    for category, errors in [
        ("SYNTAX", classified_errors.get("SYNTAX", [])),
        ("COMPATIBILITY", classified_errors.get("COMPATIBILITY", [])),
        ("IMPORT", classified_errors.get("IMPORT", [])),
    ]:
        if errors:
            print(f"  {category}: {errors[0].solution_hint}")


if __name__ == "__main__":
    main()
