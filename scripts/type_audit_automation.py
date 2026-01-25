#!/usr/bin/env python3
# Trinity Score: 90.0 (Established by Chancellor)
"""Phase 11: 지속적 개선 체계 구축 - 타입 감사 자동화 스크립트

주기적 타입 품질 감사 및 자동화 도구
- MyPy 에러 추세 분석
- 타입 커버리지 측정
- 자동화된 개선 제안
"""

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class TypeAuditResult:
    """타입 감사 결과 데이터 클래스"""

    timestamp: str
    total_errors: int
    errors_by_file: Dict[str, int]
    errors_by_type: Dict[str, int]
    coverage_score: float
    trend_direction: str  # 'improving', 'stable', 'declining'
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TypeAuditor:
    """타입 감사 자동화 클래스"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.mypy_config = project_root / "pyproject.toml"
        self.results_dir = project_root / "reports" / "type_audits"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def run_mypy_analysis(self) -> Dict[str, Any]:
        """MyPy 분석 실행 및 결과 파싱"""

        try:
            # MyPy 실행
            cmd = [
                sys.executable,
                "-m",
                "mypy",
                str(self.project_root / "packages" / "afo-core"),
                "--config-file",
                str(self.mypy_config),
                "--no-error-summary",
                "--show-error-codes",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)

            # 에러 파싱
            errors_by_file = {}
            errors_by_type = {}
            total_errors = 0

            for line in result.stdout.split("\n"):
                if "error:" in line and not line.startswith("Success:"):
                    total_errors += 1

                    # 파일별 에러 카운트
                    parts = line.split(":")
                    if len(parts) >= 2:
                        file_path = parts[0].strip()
                        errors_by_file[file_path] = errors_by_file.get(file_path, 0) + 1

                    # 에러 타입별 카운트
                    if "[" in line and "]" in line:
                        error_type = line.split("[")[-1].split("]")[0]
                        errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1

            return {
                "total_errors": total_errors,
                "errors_by_file": errors_by_file,
                "errors_by_type": errors_by_type,
                "raw_output": result.stdout,
            }

        except Exception as e:
            print(f"MyPy 분석 실패: {e}")
            return {
                "total_errors": -1,
                "errors_by_file": {},
                "errors_by_type": {},
                "error": str(e),
            }

    def calculate_coverage_score(self, total_errors: int) -> float:
        """타입 커버리지 점수 계산 (간소화 버전)"""

        # 기준: 100개 에러 = 0점, 0개 에러 = 100점
        if total_errors <= 0:
            return 100.0
        elif total_errors >= 100:
            return 0.0
        else:
            return max(0.0, 100.0 - (total_errors * 1.0))

    def analyze_trend(self, current_errors: int, previous_results: List[TypeAuditResult]) -> str:
        """에러 추세 분석"""

        if len(previous_results) < 2:
            return "insufficient_data"

        # 최근 3개 결과의 평균 에러 수 계산
        recent_errors = [r.total_errors for r in previous_results[-3:]]
        avg_recent = sum(recent_errors) / len(recent_errors)

        if current_errors < avg_recent * 0.9:
            return "improving"
        elif current_errors > avg_recent * 1.1:
            return "declining"
        else:
            return "stable"

    def generate_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """개선 권장사항 생성"""

        recommendations = []
        errors_by_type = result.get("errors_by_type", {})
        errors_by_file = result.get("errors_by_file", {})

        # 에러 타입별 권장사항
        if errors_by_type.get("attr-defined", 0) > 5:
            recommendations.append(
                "속성 정의 에러가 많습니다. 클래스의 __init__ 메소드를 확인하세요."
            )

        if errors_by_type.get("assignment", 0) > 3:
            recommendations.append("타입 할당 에러가 있습니다. 변수 타입 힌트를 명확히 지정하세요.")

        if errors_by_type.get("call-overload", 0) > 2:
            recommendations.append(
                "함수 호출 오버로드 에러가 있습니다. 함수 시그니처를 확인하세요."
            )

        # 파일별 권장사항
        max_errors_file = max(errors_by_file.items(), key=lambda x: x[1], default=("", 0))
        if max_errors_file[1] > 10:
            recommendations.append(
                f"'{max_errors_file[0]}' 파일에 에러가 집중되어 있습니다. 우선 이 파일부터 개선하세요."
            )

        # 일반 권장사항
        if result.get("total_errors", 0) > 50:
            recommendations.append(
                "전체 에러 수가 많습니다. Phase별 접근으로 점진적 개선을 고려하세요."
            )

        if not recommendations:
            recommendations.append("타입 품질이 양호합니다. 정기적인 감사를 유지하세요.")

        return recommendations

    def load_previous_results(self) -> List[TypeAuditResult]:
        """이전 감사 결과 로드"""

        results = []
        try:
            for result_file in sorted(self.results_dir.glob("*.json")):
                with open(result_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append(TypeAuditResult(**data))
        except Exception as e:
            print(f"이전 결과 로드 실패: {e}")

        return results[-10:]  # 최근 10개만 유지

    def save_result(self, result: TypeAuditResult) -> None:
        """감사 결과 저장"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.results_dir / f"type_audit_{timestamp}.json"

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    def run_audit(self) -> TypeAuditResult:
        """전체 타입 감사 실행"""

        print("🔍 타입 감사 시작...")

        # MyPy 분석
        mypy_result = self.run_mypy_analysis()
        print(f"📊 MyPy 분석 완료: {mypy_result.get('total_errors', 'N/A')}개 에러 발견")

        # 커버리지 점수 계산
        coverage_score = self.calculate_coverage_score(mypy_result.get("total_errors", 0))
        print(f"🎯 커버리지 점수: {coverage_score:.1f}/100")
        # 추세 분석
        previous_results = self.load_previous_results()
        trend = self.analyze_trend(mypy_result.get("total_errors", 0), previous_results)
        print(f"📈 추세 분석: {trend}")

        # 권장사항 생성
        recommendations = self.generate_recommendations(mypy_result)
        print(f"💡 {len(recommendations)}개 개선 권장사항 생성")

        # 결과 생성
        result = TypeAuditResult(
            timestamp=datetime.now().isoformat(),
            total_errors=mypy_result.get("total_errors", 0),
            errors_by_file=mypy_result.get("errors_by_file", {}),
            errors_by_type=mypy_result.get("errors_by_type", {}),
            coverage_score=coverage_score,
            trend_direction=trend,
            recommendations=recommendations,
        )

        # 결과 저장
        self.save_result(result)
        print(f"💾 감사 결과 저장: {self.results_dir}")

        return result

    def generate_report(self, result: TypeAuditResult) -> str:
        """감사 보고서 생성"""

        report = f"""
# AFO Kingdom 타입 품질 감사 보고서
**감사 일시:** {result.timestamp}

## 📊 현재 상태
- **총 에러 수:** {result.total_errors}개
- **커버리지 점수:** {result.coverage_score:.1f}/100
- **추세:** {result.trend_direction}

## 📁 파일별 에러 분포
"""

        for file_path, count in sorted(
            result.errors_by_file.items(), key=lambda x: x[1], reverse=True
        ):
            report += f"- `{file_path}`: {count}개\n"

        report += "\n## 🏷️ 에러 타입별 분포\n"

        for error_type, count in sorted(
            result.errors_by_type.items(), key=lambda x: x[1], reverse=True
        ):
            report += f"- `{error_type}`: {count}개\n"

        report += "\n## 💡 개선 권장사항\n"

        for i, rec in enumerate(result.recommendations, 1):
            report += f"{i}. {rec}\n"

        return report


def main() -> None:
    """메인 함수"""

    print("🚀 AFO Kingdom 타입 감사 자동화 시작")
    print("=" * 50)

    auditor = TypeAuditor(PROJECT_ROOT)
    result = auditor.run_audit()

    print("\n" + "=" * 50)
    print("📋 감사 보고서")
    print("=" * 50)

    report = auditor.generate_report(result)
    print(report)

    # 보고서 파일로 저장
    report_file = (
        PROJECT_ROOT
        / "reports"
        / f"type_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    report_file.parent.mkdir(parents=True, exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 보고서 저장됨: {report_file}")

    # 종료 상태 코드 (CI/CD용)
    exit_code = 0 if result.coverage_score >= 70 else 1
    print(f"\n🏁 감사 완료 (종료 코드: {exit_code})")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
