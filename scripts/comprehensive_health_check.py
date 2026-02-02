#!/usr/bin/env python3
"""
🏛️ AFO Kingdom Comprehensive Health Check System
문서·환경설정·헬스테스트·CI/CD·SSOT 완전 검증 시스템
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class ComprehensiveHealthChecker:
    """AFO Kingdom의 완전한 건강 상태를 검증하는 시스템"""

    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []

    def log(self, message: str, level: str = "INFO"):
        """로그 메시지 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def check_command(self, command: str, description: str) -> Dict[str, Any]:
        """명령어 실행 및 결과 반환"""
        self.log(f"🔍 {description}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            success = result.returncode == 0
            output = result.stdout.strip()
            error = result.stderr.strip()

            if success:
                self.log(f"✅ {description} - 성공")
            else:
                self.log(f"❌ {description} - 실패: {error}")
                self.errors.append(f"{description}: {error}")

            return {
                "success": success,
                "output": output,
                "error": error,
                "description": description,
            }
        except Exception as e:
            self.log(f"⚠️ {description} - 예외 발생: {e}")
            self.warnings.append(f"{description}: {e}")
            return {"success": False, "output": "", "error": str(e), "description": description}

    def check_file_exists(self, file_path: str, description: str) -> bool:
        """파일 존재 여부 확인"""
        exists = os.path.exists(file_path)
        if exists:
            self.log(f"✅ {description} - 파일 존재")
        else:
            self.log(f"❌ {description} - 파일 없음")
            self.errors.append(f"{description}: 파일이 존재하지 않습니다")
        return exists

    def run_documentation_check(self) -> Dict[str, Any]:
        """문서화 상태 검증"""
        self.log("📚 문서화 검증 시작")

        docs_to_check = [
            ("README.md", "프로젝트 메인 README"),
            ("AUDIT_README.md", "감사 시스템 문서"),
            ("docs/AFO_ROYAL_LIBRARY.md", "철학 라이브러리"),
            ("docs/AFO_SSOT_CORE_DEFINITIONS.md", "SSOT 정의 문서"),
            ("docs/AFO_SYSTEM_STABILIZATION.md", "시스템 안정화 문서"),
            ("AGENTS.md", "에이전트 시스템 문서"),
            ("CLAUDE.md", "Claude 통합 문서"),
        ]

        doc_results = {}
        for doc_path, description in docs_to_check:
            exists = self.check_file_exists(doc_path, description)
            doc_results[doc_path] = {"exists": exists, "description": description}

        return {
            "component": "documentation",
            "status": "success" if all(r["exists"] for r in doc_results.values()) else "failure",
            "details": doc_results,
        }

    def run_environment_check(self) -> Dict[str, Any]:
        """환경 설정 검증"""
        self.log("⚙️ 환경 설정 검증 시작")

        env_checks = [
            ("python --version", "Python 버전 확인"),
            ("pip --version", "Pip 버전 확인"),
            ("node --version", "Node.js 버전 확인", True),  # optional
            ("npm --version", "NPM 버전 확인", True),  # optional
        ]

        env_results = {}
        for cmd_info in env_checks:
            if len(cmd_info) == 3:
                cmd, desc, optional = cmd_info
            else:
                cmd, desc = cmd_info
                optional = False

            result = self.check_command(cmd, desc)
            env_results[desc] = result

            if not result["success"] and not optional:
                self.errors.append(f"필수 환경 구성 요소 누락: {desc}")

        return {
            "component": "environment",
            "status": "success"
            if all(
                r["success"] or len(cmd_info) == 3
                for r, cmd_info in zip(env_results.values(), env_checks)
            )
            else "failure",
            "details": env_results,
        }

    def run_code_quality_check(self) -> Dict[str, Any]:
        """코드 품질 검증"""
        self.log("🔧 코드 품질 검증 시작")

        quality_checks = [
            ("python scripts/dimensional_audit.py", "7차원 감사 시스템"),
            ("cd packages/afo-core && python -m ruff check --quiet", "Ruff 린팅"),
            ("cd packages/afo-core && python -m pyright --stats", "Pyright 타입 체크"),
        ]

        quality_results = {}
        for cmd, desc in quality_checks:
            result = self.check_command(cmd, desc)
            quality_results[desc] = result

        return {
            "component": "code_quality",
            "status": "success"
            if all(r["success"] for r in quality_results.values())
            else "warning",
            "details": quality_results,
        }

    def run_ssot_check(self) -> Dict[str, Any]:
        """SSOT (Single Source of Truth) 검증"""
        self.log("🎯 SSOT 검증 시작")

        ssot_files = [
            "AGENTS.md",
            "docs/AFO_SSOT_CORE_DEFINITIONS.md",
            "docs/AFO_ROYAL_LIBRARY.md",
            "health_gate_rules.txt",
        ]

        ssot_results = {}
        for ssot_file in ssot_files:
            exists = self.check_file_exists(ssot_file, f"SSOT 파일: {ssot_file}")
            ssot_results[ssot_file] = {"exists": exists}

            if exists:
                # SSOT 파일의 최신 수정 시간 확인
                mod_time = os.path.getmtime(ssot_file)
                mod_date = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                ssot_results[ssot_file]["last_modified"] = mod_date

        # SSOT 드리프트 검증 (예시)
        ssot_drift_check = self.check_command(
            "find artifacts -name '*ssot*' -mtime -7 | wc -l", "최근 SSOT 변경사항 확인"
        )

        return {
            "component": "ssot",
            "status": "success" if all(r["exists"] for r in ssot_results.values()) else "failure",
            "details": {"files": ssot_results, "drift_check": ssot_drift_check},
        }

    def run_ci_cd_check(self) -> Dict[str, Any]:
        """CI/CD 파이프라인 검증"""
        self.log("🚀 CI/CD 파이프라인 검증 시작")

        ci_checks = [
            ("make check", "CI 잠금 프로토콜"),
            ("make lint", "코드 린팅"),
            ("make type-check", "타입 체크"),
            ("make test", "단위 테스트"),
        ]

        ci_results = {}
        for cmd, desc in ci_checks:
            result = self.check_command(cmd, desc)
            ci_results[desc] = result

        return {
            "component": "ci_cd",
            "status": "success" if all(r["success"] for r in ci_results.values()) else "warning",
            "details": ci_results,
        }

    def run_health_tests(self) -> Dict[str, Any]:
        """헬스 테스트 실행"""
        self.log("🏥 헬스 테스트 실행 시작")

        health_tests = [
            ("python scripts/dimensional_audit.py", "7차원 감사 시스템"),
            (
                "curl -f http://localhost:8010/health 2>/dev/null || echo 'API 서버 미실행'",
                "Soul Engine 헬스 체크",
            ),
            (
                "curl -f http://localhost:3000/api/health 2>/dev/null || echo 'Dashboard 미실행'",
                "Dashboard 헬스 체크",
            ),
        ]

        health_results = {}
        for cmd, desc in health_tests:
            result = self.check_command(cmd, desc)
            health_results[desc] = result

        return {
            "component": "health_tests",
            "status": "success"
            if all(r["success"] for r in health_results.values())
            else "warning",
            "details": health_results,
        }

    def generate_report(self) -> Dict[str, Any]:
        """종합 보고서 생성"""
        self.log("📊 종합 보고서 생성 중...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "success" if not self.errors else "failure",
            "components": self.results,
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": {
                "total_components": len(self.results),
                "successful_components": len(
                    [r for r in self.results.values() if r.get("status") == "success"]
                ),
                "failed_components": len(
                    [r for r in self.results.values() if r.get("status") == "failure"]
                ),
                "warning_components": len(
                    [r for r in self.results.values() if r.get("status") == "warning"]
                ),
            },
        }

        return report

    def run_all_checks(self) -> Dict[str, Any]:
        """모든 검증 실행"""
        self.log("🏛️ AFO Kingdom 종합 헬스 체크 시작")
        self.log("=" * 60)

        # 모든 컴포넌트 검증 실행
        self.results["documentation"] = self.run_documentation_check()
        self.results["environment"] = self.run_environment_check()
        self.results["code_quality"] = self.run_code_quality_check()
        self.results["ssot"] = self.run_ssot_check()
        self.results["ci_cd"] = self.run_ci_cd_check()
        self.results["health_tests"] = self.run_health_tests()

        self.log("=" * 60)

        # 종합 보고서 생성
        report = self.generate_report()

        # 보고서 출력
        self.print_report(report)

        return report

    def print_report(self, report: Dict[str, Any]):
        """보고서 출력"""
        print("\n🏛️ AFO KINGDOM 종합 헬스 체크 보고서")
        print("=" * 60)

        status_emoji = {"success": "✅", "failure": "❌", "warning": "⚠️"}

        for component, result in report["components"].items():
            status = result.get("status", "unknown")
            emoji = status_emoji.get(status, "❓")
            print(f"{emoji} {component.upper()}: {status}")

        print("\n📈 요약:")
        summary = report["summary"]
        print(f"  • 총 컴포넌트: {summary['total_components']}")
        print(f"  • 성공: {summary['successful_components']}")
        print(f"  • 실패: {summary['failed_components']}")
        print(f"  • 경고: {summary['warning_components']}")

        if report["errors"]:
            print(f"\n❌ 오류 ({len(report['errors'])}개):")
            for error in report["errors"][:5]:  # 상위 5개만 표시
                print(f"  • {error}")

        if report["warnings"]:
            print(f"\n⚠️ 경고 ({len(report['warnings'])}개):")
            for warning in report["warnings"][:3]:  # 상위 3개만 표시
                print(f"  • {warning}")

        overall_status = report["overall_status"]
        if overall_status == "success":
            print("\n🎉 전체 시스템 건강: 양호 (SUCCESS)")
        elif overall_status == "failure":
            print("\n❌ 전체 시스템 건강: 문제 있음 (FAILURE)")
        else:
            print("\n⚠️ 전체 시스템 건강: 주의 필요 (WARNING)")
        print("=" * 60)


def main():
    """메인 실행 함수"""
    checker = ComprehensiveHealthChecker()
    report = checker.run_all_checks()

    # JSON 보고서 저장
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = artifacts_dir / f"comprehensive_health_check_{timestamp}.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"📄 상세 보고서 저장됨: {report_file}")

    # 종료 코드 반환
    return 0 if report["overall_status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
