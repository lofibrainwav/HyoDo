#!/usr/bin/env python3
"""
AFO Kingdom - Reporting Validation Checklist
보고 정확성 검증을 위한 체크리스트

Purpose: 보고 전 검증 메커니즘 구축 (SSOT 준수)
Author: AFO Kingdom 승상
Date: 2026-01-12

SSOT 준수:
- Python 인터프리터: python3 단일화 (docs/AFO_SSOT_CORE_DEFINITIONS.md)
- Trinity Score 계산식: 가중치 공식 단일화 (docs/AFO_SSOT_CORE_DEFINITIONS.md)
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class ReportingValidationChecklist:
    """보고 검증 체크리스트 클래스"""

    def __init__(self) -> None:
        self.checklist = {
            "environment_accuracy": {
                "python_version_verified": False,
                "system_info_collected": False,
                "dependencies_validated": False,
            },
            "data_accuracy": {
                "file_counts_verified": False,
                "conversion_counts_checked": False,
                "trinity_score_calculated": False,
            },
            "reporting_integrity": {
                "actual_vs_reported_comparison": False,
                "sources_cited": False,
                "evidence_provided": False,
            },
        }
        self.results = {}

    def validate_python_version(self) -> Dict[str, Any]:
        """Python 버전 검증"""
        result = {
            "status": "pending",
            "python_version": None,
            "python3_version": None,
            "discrepancy_found": False,
            "recommendation": "",
        }

        try:
            import subprocess

            python_ver = subprocess.run(["python", "--version"], capture_output=True, text=True)
            python3_ver = subprocess.run(["python3", "--version"], capture_output=True, text=True)

            result["python_version"] = (
                python_ver.stdout.strip() if python_ver.returncode == 0 else "Not found"
            )
            result["python3_version"] = (
                python3_ver.stdout.strip() if python3_ver.returncode == 0 else "Not found"
            )

            # 버전이 다른지 확인
            if result["python_version"] != result["python3_version"]:
                result["discrepancy_found"] = True
                result["recommendation"] = "보고 시 python과 python3 버전을 모두 명시해야 함"

            result["status"] = "completed"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def validate_file_counts(self) -> Dict[str, Any]:
        """파일 수량 검증"""
        result = {
            "status": "pending",
            "python_files_count": None,
            "conversion_files_count": None,
            "discrepancy_found": False,
            "recommendation": "",
        }

        try:
            project_root = Path(__file__).parent.parent

            # Python 파일 수 세기
            python_files = list(project_root.rglob("*.py"))
            result["python_files_count"] = len(python_files)

            # timezone.utc 변환 파일 수 세기
            import subprocess

            grep_result = subprocess.run(
                [
                    "find",
                    str(project_root / "packages" / "afo-core"),
                    "-name",
                    "*.py",
                    "-exec",
                    "grep",
                    "-l",
                    "timezone.utc",
                    "{}",
                    ";",
                ],
                capture_output=True,
                text=True,
            )

            if grep_result.returncode == 0:
                converted_files = (
                    len(grep_result.stdout.strip().split("\n")) if grep_result.stdout.strip() else 0
                )
                result["conversion_files_count"] = converted_files
            else:
                result["conversion_files_count"] = 0

            # 불일치 확인
            if result["python_files_count"] and result["conversion_files_count"]:
                if result["conversion_files_count"] > result["python_files_count"]:
                    result["discrepancy_found"] = True
                    result["recommendation"] = (
                        "변환 파일 수가 전체 파일 수보다 많을 수 없음 - 재검증 필요"
                    )

            result["status"] = "completed"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def validate_trinity_score(self) -> Dict[str, Any]:
        """Trinity Score 검증 (SSOT 가중치 공식 준수)"""
        result = {
            "status": "pending",
            "calculated_score": None,
            "reported_score": None,
            "discrepancy_found": False,
            "recommendation": "",
        }

        try:
            project_root = Path(__file__).parent.parent
            log_file = project_root / "AFO_EVOLUTION_LOG.md"

            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # SSOT 가중치 공식 적용 (docs/AFO_SSOT_CORE_DEFINITIONS.md)
                WEIGHTS = {
                    "truth": 0.35,  # 眞
                    "goodness": 0.35,  # 善
                    "beauty": 0.20,  # 美
                    "serenity": 0.08,  # 孝
                    "eternity": 0.02,  # 永
                }

                # 최신 Trinity Score 찾기
                import re

                trinity_pattern = r"Trinity Score Achievement.*?\(眞([\d.]+)\s*\+\s*善([\d.]+)\s*\+\s*美([\d.]+)\s*\+\s*孝([\d.]+)\s*\+\s*永([\d.]+)\)"
                matches = re.findall(trinity_pattern, content)

                if matches:
                    # 가장 최근 값 사용
                    latest_match = matches[-1]
                    scores = [float(x) for x in latest_match]

                    # SSOT 가중치 공식 적용
                    calculated = (
                        WEIGHTS["truth"] * scores[0]  # 眞 35%
                        + WEIGHTS["goodness"] * scores[1]  # 善 35%
                        + WEIGHTS["beauty"] * scores[2]  # 美 20%
                        + WEIGHTS["serenity"] * scores[3]  # 孝 8%
                        + WEIGHTS["eternity"] * scores[4]  # 永 2%
                    ) * 100

                    result["calculated_score"] = round(calculated, 1)

                    # 로그에서 보고된 값 찾기 (91.5%)
                    reported_pattern = r"(\d+\.?\d*)%"
                    percentages = re.findall(reported_pattern, content)
                    if percentages:
                        for pct in percentages:
                            if float(pct) == 91.5:
                                result["reported_score"] = 91.5
                                break

                    if result["calculated_score"] and result["reported_score"]:
                        if abs(result["calculated_score"] - result["reported_score"]) > 0.1:
                            result["discrepancy_found"] = True
                            result["recommendation"] = (
                                f"SSOT 가중치 공식 계산값 {result['calculated_score']}% vs 보고값 {result['reported_score']}% 불일치"
                            )

            result["status"] = "completed"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def run_validation(self) -> Dict[str, Any]:
        """전체 검증 실행"""
        print("🛡️ AFO Kingdom - Reporting Validation Checklist")
        print("=" * 55)

        # 각 검증 실행
        self.results["python_version"] = self.validate_python_version()
        self.results["file_counts"] = self.validate_file_counts()
        self.results["trinity_score"] = self.validate_trinity_score()

        # 종합 결과
        all_passed = all(
            result["status"] == "completed" and not result.get("discrepancy_found", False)
            for result in self.results.values()
        )

        self.results["summary"] = {
            "overall_status": "PASSED" if all_passed else "FAILED",
            "validation_timestamp": self._get_timestamp(),
            "recommendations": self._collect_recommendations(),
        }

        return self.results

    def _get_timestamp(self) -> str:
        """현재 타임스탬프"""
        import subprocess

        result = subprocess.run(["date", "+%Y-%m-%d %H:%M:%S"], capture_output=True, text=True)
        return result.stdout.strip()

    def _collect_recommendations(self) -> List[str]:
        """모든 추천사항 수집"""
        recommendations = []
        for category, result in self.results.items():
            if isinstance(result, dict) and result.get("recommendation"):
                recommendations.append(f"{category}: {result['recommendation']}")

        return recommendations

    def print_report(self) -> None:
        """결과 보고 출력"""
        print("\n📋 검증 결과:")
        for category, result in self.results.items():
            if category == "summary":
                continue

            status = (
                "✅"
                if result["status"] == "completed" and not result.get("discrepancy_found", False)
                else "❌"
            )
            print(f"  {status} {category}: {result['status']}")

            if result.get("discrepancy_found"):
                print(f"      ⚠️  불일치 발견: {result.get('recommendation', '')}")

        print(f"\n🎯 종합 결과: {self.results['summary']['overall_status']}")

        if self.results["summary"]["recommendations"]:
            print("\n💡 권장사항:")
            for rec in self.results["summary"]["recommendations"]:
                print(f"  • {rec}")

    def save_report(self, filename: str = "reporting_validation_report.json") -> str:
        """검증 결과를 파일로 저장"""
        project_root = Path(__file__).parent.parent
        report_path = project_root / filename

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        return str(report_path)


def main() -> None:
    """메인 함수"""
    checklist = ReportingValidationChecklist()

    print("🔍 보고 검증 체크리스트 실행...")
    checklist.run_validation()
    checklist.print_report()

    # 결과 저장
    report_file = checklist.save_report()
    print(f"\n💾 검증 결과 저장됨: {report_file}")

    # 최종 결론
    if checklist.results["summary"]["overall_status"] == "PASSED":
        print("\n✅ 보고 검증 통과! 정확한 정보 보고 가능합니다.")
    else:
        print("\n❌ 보고 검증 실패! 문제점 해결 후 다시 시도하세요.")

    return checklist.results


if __name__ == "__main__":
    main()
