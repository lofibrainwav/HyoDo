#!/usr/bin/env python3
"""
AFO 왕국 Sequential Thinking 로그 분석기
각 로그 청크를 단계별로 분석하여 근본 원인과 해결 전략을 제시

Sequential Thinking 단계:
1. 에러 패턴 식별 (Pattern Recognition)
2. 근본 원인 추적 (Root Cause Analysis)
3. 영향 범위 평가 (Impact Assessment)
4. 해결 우선순위 결정 (Priority Setting)
5. 수정 전략 제안 (Solution Strategy)
"""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class SequentialAnalysis:
    """Sequential Thinking 분석 결과"""

    chunk_id: str
    step_1_patterns: List[str]  # 에러 패턴 식별
    step_2_root_causes: List[str]  # 근본 원인 추적
    step_3_impacts: Dict[str, Any]  # 영향 범위 평가
    step_4_priorities: Dict[str, str]  # 해결 우선순위
    step_5_solutions: List[str]  # 수정 전략 제안
    confidence_score: float  # 분석 신뢰도 (0-1)


class SequentialAnalyzer:
    """Sequential Thinking 기반 로그 분석기"""

    def __init__(self, chunks_dir: str = "log_chunks") -> None:
        self.chunks_dir = Path(chunks_dir)
        self.analyses: List[SequentialAnalysis] = []

    def load_chunk(self, chunk_file: str) -> Dict[str, Any]:
        """청크 파일 로드"""
        with open(self.chunks_dir / chunk_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def step_1_identify_patterns(self, lines: List[str]) -> List[str]:
        """단계 1: 에러 패턴 식별"""
        patterns = []

        # Python Syntax 에러 패턴
        syntax_patterns = [
            "Expected an indented block",
            "invalid-syntax",
            "Simple statements must be separated",
            "Expected.*newline",
            "Expected.*semicolon",
        ]

        # Import 에러 패턴
        import_patterns = [
            "is not defined",
            "ImportError",
            "Module level import not at top",
        ]

        # 호환성 에러 패턴
        compatibility_patterns = [
            "Union.*not defined",
            "Optional.*not defined",
            "TypeVar.*not defined",
        ]

        for line in lines:
            for pattern in syntax_patterns + import_patterns + compatibility_patterns:
                if pattern.lower() in line.lower():
                    if pattern not in patterns:
                        patterns.append(pattern)

        return patterns

    def step_2_trace_root_causes(self, patterns: List[str], lines: List[str]) -> List[str]:
        """단계 2: 근본 원인 추적"""
        root_causes = []

        # 패턴 기반 근본 원인 분석
        if any("indented block" in p for p in patterns):
            root_causes.append("Python 호환성 스크립트 실행 실패 - 들여쓰기 규칙 변경")

        if any("not defined" in p for p in patterns):
            # Union/Optional import 누락 확인
            union_errors = [line for line in lines if "Union" in line and "not defined" in line]
            optional_errors = [
                line for line in lines if "Optional" in line and "not defined" in line
            ]

            if union_errors or optional_errors:
                root_causes.append("typing 모듈 import 누락 - Python 3.9+ 호환성 문제")

        if any("invalid-syntax" in p for p in patterns):
            root_causes.append("구문 변환 실패 - Union Syntax → 호환성 코드 변환 오류")

        if any("Module level import" in p for p in patterns):
            root_causes.append("import 순서 변경 - Python 실행 순서 변경으로 인한 import 위치 오류")

        return root_causes

    def step_3_assess_impacts(self, patterns: List[str], lines: List[str]) -> Dict[str, Any]:
        """단계 3: 영향 범위 평가"""
        impacts = {
            "severity": "UNKNOWN",
            "affected_files": 0,
            "affected_lines": len(lines),
            "blocking_deployment": False,
            "affects_core_functionality": False,
        }

        # 심각도 평가
        critical_patterns = ["Expected an indented block", "invalid-syntax"]
        high_patterns = ["is not defined", "ImportError"]

        if any(p in str(patterns) for p in critical_patterns):
            impacts["severity"] = "CRITICAL"
            impacts["blocking_deployment"] = True
            impacts["affects_core_functionality"] = True
        elif any(p in str(patterns) for p in high_patterns):
            impacts["severity"] = "HIGH"
            impacts["blocking_deployment"] = True

        # 파일 영향 범위 계산
        file_paths = set()
        for line in lines:
            # 파일 경로 패턴 찾기
            import re

            file_match = re.search(r"/Users/brnestrm/AFO_Kingdom/([^:]+):", line)
            if file_match:
                file_paths.add(file_match.group(1))

        impacts["affected_files"] = len(file_paths)

        return impacts

    def step_4_set_priorities(self, impacts: Dict[str, Any]) -> Dict[str, str]:
        """단계 4: 해결 우선순위 결정"""
        priorities = {
            "immediate_action": "LOW",
            "timeframe": "days",
            "resources_needed": "minimal",
            "risk_level": "low",
        }

        if impacts["severity"] == "CRITICAL":
            priorities.update(
                {
                    "immediate_action": "CRITICAL",
                    "timeframe": "hours",
                    "resources_needed": "immediate attention",
                    "risk_level": "blocks deployment",
                }
            )
        elif impacts["severity"] == "HIGH":
            priorities.update(
                {
                    "immediate_action": "HIGH",
                    "timeframe": "hours",
                    "resources_needed": "developer attention",
                    "risk_level": "affects functionality",
                }
            )

        return priorities

    def step_5_suggest_solutions(
        self, root_causes: List[str], impacts: Dict[str, Any]
    ) -> List[str]:
        """단계 5: 수정 전략 제안"""
        solutions = []

        # 근본 원인 기반 해결책 제안
        for cause in root_causes:
            if "호환성 스크립트 실행 실패" in cause:
                solutions.extend(
                    [
                        "Python 호환성 변환 스크립트 재실행",
                        "Union Syntax → Optional[Union[...]] 변환 검증",
                        "들여쓰기 규칙 변경사항 적용",
                    ]
                )

            if "typing 모듈 import 누락" in cause:
                solutions.extend(
                    [
                        "from typing import Optional, Union 추가",
                        "Python 버전별 import 조건문 구현",
                        "TYPE_CHECKING 블록 내 import 정리",
                    ]
                )

            if "구문 변환 실패" in cause:
                solutions.extend(
                    [
                        "AST 기반 구문 변환 도구 개발",
                        "수동 검증 후 자동 변환 적용",
                        "Python 버전 매트릭스 테스트 추가",
                    ]
                )

            if "import 순서 변경" in cause:
                solutions.extend(
                    [
                        "import 순서 표준화",
                        "모듈 레벨 import 위치 통일",
                        "PEP 8 import 정렬 적용",
                    ]
                )

        # 영향 범위 기반 추가 해결책
        if impacts["affected_files"] > 10:
            solutions.append("대규모 파일 수정 자동화 스크립트 개발")

        if impacts["blocking_deployment"]:
            solutions.insert(0, "🚨 긴급: 배포 차단 해소 우선")

        return solutions

    def calculate_confidence(self, analysis: SequentialAnalysis) -> float:
        """분석 신뢰도 계산"""
        confidence = 0.5  # 기본 신뢰도

        # 패턴 식별 성공도
        if analysis.step_1_patterns:
            confidence += 0.2

        # 근본 원인 발견
        if analysis.step_2_root_causes:
            confidence += 0.2

        # 영향 평가 정확성
        if analysis.step_3_impacts["severity"] != "UNKNOWN":
            confidence += 0.1

        return min(confidence, 1.0)

    def analyze_chunk(self, chunk_data: Dict[str, Any]) -> SequentialAnalysis:
        """청크에 대한 Sequential Thinking 분석 수행"""
        chunk_id = chunk_data["chunk_id"]
        lines = chunk_data["lines"]

        # 단계별 분석 수행
        step_1_patterns = self.step_1_identify_patterns(lines)
        step_2_root_causes = self.step_2_trace_root_causes(step_1_patterns, lines)
        step_3_impacts = self.step_3_assess_impacts(step_1_patterns, lines)
        step_4_priorities = self.step_4_set_priorities(step_3_impacts)
        step_5_solutions = self.step_5_suggest_solutions(step_2_root_causes, step_3_impacts)

        analysis = SequentialAnalysis(
            chunk_id=chunk_id,
            step_1_patterns=step_1_patterns,
            step_2_root_causes=step_2_root_causes,
            step_3_impacts=step_3_impacts,
            step_4_priorities=step_4_priorities,
            step_5_solutions=step_5_solutions,
            confidence_score=0.0,  # 일단 0으로 설정, 나중에 계산
        )

        analysis.confidence_score = self.calculate_confidence(analysis)

        return analysis

    def analyze_all_chunks(self) -> List[SequentialAnalysis]:
        """모든 청크 분석"""
        # Streaming 방식 활용하여 구현
        return list(self.analyze_stream_chunks())

    def analyze_stream_chunks(self) -> None:
        """Streaming analysis generator for memory efficiency (TICKET-040)"""
        if not self.chunks_dir.exists():
            return

        # 청크 파일들 찾기
        chunk_files = [
            f for f in os.listdir(self.chunks_dir) if f.startswith("chunk_") and f.endswith(".json")
        ]

        for chunk_file in chunk_files:
            chunk_data = self.load_chunk(chunk_file)
            analysis = self.analyze_chunk(chunk_data)
            self.analyses.append(analysis)
            yield analysis

    def generate_report(self, output_file: str = "sequential_analysis_report.md") -> str:
        """종합 보고서 생성"""
        report_path = Path(output_file)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# AFO 왕국 Sequential Thinking 로그 분석 보고서\n\n")
            f.write("## 📊 분석 개요\n\n")
            f.write(f"- 분석된 청크 수: {len(self.analyses)}\n")
            f.write(
                f"- 평균 신뢰도: {sum(a.confidence_score for a in self.analyses) / len(self.analyses):.2f}\n\n"
            )

            for analysis in self.analyses:
                f.write(f"## 🔍 청크 {analysis.chunk_id} 분석 결과\n\n")

                f.write("### 1️⃣ 에러 패턴 식별\n")
                for pattern in analysis.step_1_patterns:
                    f.write(f"- {pattern}\n")
                f.write("\n")

                f.write("### 2️⃣ 근본 원인 추적\n")
                for cause in analysis.step_2_root_causes:
                    f.write(f"- {cause}\n")
                f.write("\n")

                f.write("### 3️⃣ 영향 범위 평가\n")
                impacts = analysis.step_3_impacts
                f.write(f"- 심각도: {impacts['severity']}\n")
                f.write(f"- 영향받은 파일 수: {impacts['affected_files']}\n")
                f.write(f"- 영향받은 라인 수: {impacts['affected_lines']}\n")
                f.write(f"- 배포 차단: {'예' if impacts['blocking_deployment'] else '아니오'}\n")
                f.write("\n")

                f.write("### 4️⃣ 해결 우선순위 결정\n")
                priorities = analysis.step_4_priorities
                f.write(f"- 즉시 조치 수준: {priorities['immediate_action']}\n")
                f.write(f"- 예상 시간: {priorities['timeframe']}\n")
                f.write(f"- 필요 리소스: {priorities['resources_needed']}\n")
                f.write(f"- 위험 수준: {priorities['risk_level']}\n")
                f.write("\n")

                f.write("### 5️⃣ 수정 전략 제안\n")
                for solution in analysis.step_5_solutions:
                    f.write(f"- {solution}\n")
                f.write("\n")

                f.write(f"### 🎯 분석 신뢰도: {analysis.confidence_score:.2f}\n\n")

                f.write("---\n\n")

        return str(report_path)


def main() -> None:
    """CLI 인터페이스"""
    import argparse

    parser = argparse.ArgumentParser(description="AFO 왕국 Sequential Thinking 로그 분석기")
    parser.add_argument("--chunks-dir", default="log_chunks", help="청크 파일들이 있는 디렉토리")
    parser.add_argument(
        "--output", default="sequential_analysis_report.md", help="출력 보고서 파일"
    )

    args = parser.parse_args()

    # 분석기 초기화
    analyzer = SequentialAnalyzer(args.chunks_dir)

    print("🧠 Sequential Thinking 로그 분석 시작...")
    print(f"📁 청크 디렉토리: {args.chunks_dir}")

    # 모든 청크 분석
    analyses = analyzer.analyze_all_chunks()

    print(f"✅ 분석 완료: {len(analyses)}개 청크 처리")

    # 보고서 생성
    report_file = analyzer.generate_report(args.output)
    print(f"📄 보고서 생성: {report_file}")

    # 요약 출력
    sum(a.confidence_score for a in analyses) / len(analyses)
    print(".2f")
    print("\n🎯 주요 해결 전략:")
    for analysis in analyses:
        if analysis.step_4_priorities["immediate_action"] in ["CRITICAL", "HIGH"]:
            print(
                f"  - {analysis.chunk_id}: {analysis.step_5_solutions[0] if analysis.step_5_solutions else '해결책 분석 중'}"
            )


if __name__ == "__main__":
    main()
