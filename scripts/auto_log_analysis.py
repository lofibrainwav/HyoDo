#!/usr/bin/env python3
"""
AFO 왕국 자동 로그 분석 파이프라인
단 한 줄의 명령어로 모든 로그 분석을 자동화

파이프라인 단계:
1. 로그 청킹 (Log Chunker)
2. Sequential 분석 (Sequential Analyzer)
3. Context7 분류 (Context7 Classifier)
4. 종합 보고서 생성 (Integrated Report)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class AutoLogAnalyzer:
    """자동 로그 분석 파이프라인"""

    def __init__(self, output_dir: str = "analysis_results") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 시스템 상태 추적
        self.pipeline_status = {
            "start_time": None,
            "end_time": None,
            "steps_completed": [],
            "errors": [],
            "performance": {},
        }

    def run_pipeline(
        self,
        log_file: str,
        chunk_method: str = "error_type",
        chunk_size: int = 100,
        generate_report: bool = True,
    ) -> Dict[str, Any]:
        """
        완전 자동화된 로그 분석 파이프라인 실행

        Args:
            log_file: 분석할 로그 파일 경로
            chunk_method: 청킹 방법 ('error_type' 또는 'file')
            chunk_size: 청크 크기
            generate_report: 종합 보고서 생성 여부

        Returns:
            분석 결과 딕셔너리
        """
        self.pipeline_status["start_time"] = datetime.now().isoformat()

        try:
            print("🚀 AFO 왕국 자동 로그 분석 파이프라인 시작")
            print(f"📁 대상 파일: {log_file}")
            print(f"📊 청킹 방법: {chunk_method}")
            print(f"📏 청크 크기: {chunk_size}")
            print("-" * 50)

            # 단계 1: 로그 청킹
            print("\n1️⃣ 단계 1: 로그 청킹 실행")
            chunk_result = self._run_log_chunker(log_file, chunk_method, chunk_size)

            # 단계 2: Sequential 분석
            print("\n2️⃣ 단계 2: Sequential Thinking 분석")
            sequential_result = self._run_sequential_analyzer()

            # 단계 3: Context7 분류
            print("\n3️⃣ 단계 3: Context7 정밀 분류")
            context7_result = self._run_context7_classifier(log_file)

            # 단계 4: 종합 보고서 생성
            if generate_report:
                print("\n4️⃣ 단계 4: 종합 보고서 생성")
                report_result = self._generate_integrated_report(
                    chunk_result, sequential_result, context7_result
                )
            else:
                report_result = {"status": "skipped"}

            # 파이프라인 완료
            self.pipeline_status["end_time"] = datetime.now().isoformat()
            self.pipeline_status["steps_completed"] = [
                "log_chunking",
                "sequential_analysis",
                "context7_classification",
                "report_generation",
            ]

            # 최종 결과 취합
            final_result = {
                "pipeline_status": "SUCCESS",
                "execution_time": self._calculate_execution_time(),
                "results": {
                    "chunking": chunk_result,
                    "sequential": sequential_result,
                    "context7": context7_result,
                    "report": report_result,
                },
                "output_files": self._get_output_files(),
                "performance_metrics": self._get_performance_metrics(),
            }

            print("\n✅ 파이프라인 실행 완료!")
            print(f"⏱️ 총 실행 시간: {final_result['execution_time']}")
            print(f"📄 생성된 파일 수: {len(final_result['output_files'])}")

            return final_result

        except Exception as e:
            self.pipeline_status["errors"].append(str(e))
            self.pipeline_status["end_time"] = datetime.now().isoformat()

            error_result = {
                "pipeline_status": "FAILED",
                "error": str(e),
            }

            print(f"\n❌ 파이프라인 실행 실패: {e}")
            return error_result

    def _run_log_chunker(self, log_file: str, method: str, chunk_size: int) -> Dict[str, Any]:
        """로그 청킹 단계 실행"""
        start_time = time.time()

        # log_chunker.py 실행
        cmd = f"python3 scripts/log_chunker.py '{log_file}' --method {method} --chunk-size {chunk_size}"
        exit_code = os.system(cmd)

        execution_time = time.time() - start_time

        if exit_code == 0:
            # 청킹 결과 확인
            chunks_dir = Path("log_chunks")
            if chunks_dir.exists():
                chunk_files = list(chunks_dir.glob("chunk_*.json"))
                stats_file = chunks_dir / "statistics.json"

                result = {
                    "status": "success",
                    "chunks_created": len(chunk_files),
                    "execution_time": execution_time,
                    "output_dir": str(chunks_dir),
                }

                # 통계 파일이 있으면 로드
                if stats_file.exists():
                    with open(stats_file, "r") as f:
                        stats = json.load(f)
                    result["statistics"] = stats

                return result
            else:
                return {"status": "error", "message": "청크 디렉토리가 생성되지 않음"}
        else:
            return {"status": "error", "message": f"청킹 실패 (exit code: {exit_code})"}

    def _run_sequential_analyzer(self) -> Dict[str, Any]:
        """Sequential 분석 단계 실행"""
        start_time = time.time()

        # sequential_analyzer.py 실행
        report_file = self.output_dir / "sequential_analysis_report.md"
        cmd = (
            f"python3 scripts/sequential_analyzer.py --chunks-dir log_chunks --output {report_file}"
        )
        exit_code = os.system(cmd)

        execution_time = time.time() - start_time

        if exit_code == 0 and report_file.exists():
            return {
                "status": "success",
                "execution_time": execution_time,
                "report_file": str(report_file),
            }
        else:
            return {
                "status": "error",
                "message": f"Sequential 분석 실패 (exit code: {exit_code})",
            }

    def _run_context7_classifier(self, log_file: str) -> Dict[str, Any]:
        """Context7 분류 단계 실행"""
        start_time = time.time()

        # context7_classifier.py 실행
        report_file = self.output_dir / "context7_analysis_report.md"
        cmd = f"python3 scripts/context7_classifier.py '{log_file}' --output {report_file}"
        exit_code = os.system(cmd)

        execution_time = time.time() - start_time

        if exit_code == 0 and report_file.exists():
            return {
                "status": "success",
                "execution_time": execution_time,
                "report_file": str(report_file),
            }
        else:
            return {
                "status": "error",
                "message": f"Context7 분류 실패 (exit code: {exit_code})",
            }

    def _generate_integrated_report(
        self, chunk_result: Dict, sequential_result: Dict, context7_result: Dict
    ) -> Dict[str, Any]:
        """통합 보고서 생성"""
        report_file = self.output_dir / "integrated_analysis_report.md"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# AFO 왕국 통합 로그 분석 보고서\n\n")
            f.write(f"**생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 실행 요약
            f.write("## 📊 실행 요약\n\n")
            f.write("| 단계 | 상태 | 실행 시간 | 결과 |\n")
            f.write("|------|------|----------|------|\n")

            steps = [
                ("로그 청킹", chunk_result),
                ("Sequential 분석", sequential_result),
                ("Context7 분류", context7_result),
            ]

            for step_name, result in steps:
                status = "✅ 성공" if result["status"] == "success" else "❌ 실패"
                exec_time = f"{result.get('execution_time', 0):.2f}초"
                output = result.get("report_file", result.get("output_dir", "-"))
                f.write(f"| {step_name} | {status} | {exec_time} | {output} |\n")

            f.write("\n")

            # 상세 결과
            f.write("## 📋 상세 분석 결과\n\n")

            # 청킹 결과
            if chunk_result["status"] == "success":
                f.write("### 1️⃣ 로그 청킹 결과\n")
                f.write(f"- 생성된 청크 수: {chunk_result.get('chunks_created', 0)}\n")
                if "statistics" in chunk_result:
                    stats = chunk_result["statistics"]
                    f.write(f"- 총 에러 수: {stats.get('total_errors', 0)}\n")
                    f.write(f"- 평균 에러/청크: {stats.get('avg_errors_per_chunk', 0):.1f}\n")
                f.write("\n")

            # Sequential 결과
            if sequential_result["status"] == "success":
                f.write("### 2️⃣ Sequential Thinking 분석 결과\n")
                f.write("- 5단계 사고 기반 근본 원인 분석 완료\n")
                f.write("- 영향 범위 및 해결 우선순위 분석 완료\n")
                f.write(f"- 보고서: {sequential_result['report_file']}\n")
                f.write("\n")

            # Context7 결과
            if context7_result["status"] == "success":
                f.write("### 3️⃣ Context7 정밀 분류 결과\n")
                f.write("- SYNTAX, IMPORT, COMPATIBILITY, TYPE, UNKNOWN 카테고리 분류 완료\n")
                f.write("- 근본 원인 추론 및 해결 방안 제안 완료\n")
                f.write(f"- 보고서: {context7_result['report_file']}\n")
                f.write("\n")

            # 결론 및 권고사항
            f.write("## 🎯 결론 및 권고사항\n\n")

            all_success = all(
                result["status"] == "success"
                for result in [chunk_result, sequential_result, context7_result]
            )

            if all_success:
                f.write("✅ **모든 분석 단계가 성공적으로 완료되었습니다.**\n\n")
                f.write("**다음 권고사항:**\n")
                f.write("1. 개별 상세 보고서들을 검토하여 우선순위가 높은 이슈부터 해결\n")
                f.write("2. CRITICAL 및 HIGH 우선순위 이슈들을 즉시 조치\n")
                f.write("3. 재발 방지를 위한 자동화 모니터링 시스템 구축 고려\n")
                f.write("4. 분석 결과를 팀 내 공유하여 지식 공유\n")
            else:
                f.write("⚠️ **일부 분석 단계에서 문제가 발생했습니다.**\n\n")
                f.write("**권고사항:**\n")
                f.write("1. 실패한 단계들의 오류 로그를 확인\n")
                f.write("2. 시스템 요구사항(dependencies)을 재확인\n")
                f.write("3. 수동으로 개별 분석 도구들을 실행하여 문제 진단\n")

            f.write("\n---\n")
            f.write("*AFO 왕국 자동 로그 분석 파이프라인에 의해 생성됨*")

        return {
            "status": "success",
            "report_file": str(report_file),
            "all_steps_success": all_success,
        }

    def _calculate_execution_time(self) -> str:
        """총 실행 시간 계산"""
        if not self.pipeline_status["start_time"] or not self.pipeline_status["end_time"]:
            return "N/A"

        start = datetime.fromisoformat(self.pipeline_status["start_time"])
        end = datetime.fromisoformat(self.pipeline_status["end_time"])
        duration = end - start

        return f"{duration.total_seconds():.2f}초"

    def _get_output_files(self) -> List[str]:
        """생성된 모든 출력 파일 목록"""
        output_files = []

        # 보고서 파일들
        for pattern in ["*.md", "*.json"]:
            for file_path in self.output_dir.glob(pattern):
                output_files.append(str(file_path))

        # 청크 파일들
        chunks_dir = Path("log_chunks")
        if chunks_dir.exists():
            for file_path in chunks_dir.glob("*"):
                output_files.append(str(file_path))

        return output_files

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 수집"""
        return {
            "total_steps": len(self.pipeline_status["steps_completed"]),
            "errors_count": len(self.pipeline_status["errors"]),
            "output_files_count": len(self._get_output_files()),
        }


def main() -> None:
    """CLI 인터페이스"""
    parser = argparse.ArgumentParser(
        description="AFO 왕국 자동 로그 분석 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python3 scripts/auto_log_analysis.py error.log
  python3 scripts/auto_log_analysis.py large_log.txt --chunk-method file --chunk-size 200
  python3 scripts/auto_log_analysis.py debug.log --no-report
        """,
    )

    parser.add_argument("log_file", help="분석할 로그 파일 경로")
    parser.add_argument(
        "--chunk-method",
        choices=["error_type", "file"],
        default="error_type",
        help="청킹 방법 (기본: error_type)",
    )
    parser.add_argument(
        "--chunk-size", type=int, default=100, help="청크 크기 (라인 수, 기본: 100)"
    )
    parser.add_argument(
        "--output-dir",
        default="analysis_results",
        help="출력 디렉토리 (기본: analysis_results)",
    )
    parser.add_argument("--no-report", action="store_true", help="종합 보고서 생성하지 않음")

    args = parser.parse_args()

    # 분석기 초기화 및 실행
    analyzer = AutoLogAnalyzer(args.output_dir)
    result = analyzer.run_pipeline(
        args.log_file, args.chunk_method, args.chunk_size, not args.no_report
    )

    # 결과 출력
    if result["pipeline_status"] == "SUCCESS":
        print(f"\n🎉 분석 완료! 결과 파일들이 {args.output_dir} 디렉토리에 저장되었습니다.")
        sys.exit(0)
    else:
        print(f"\n💥 분석 실패: {result.get('error', '알 수 없는 오류')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
