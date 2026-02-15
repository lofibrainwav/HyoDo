#!/usr/bin/env python3
"""
AFO Kingdom Security Scanner - 통합 보안 스캐닝 도구
======================================================

GitHub CLI (gh)의 dependabot-alerts 확장과 pip-audit를 통합한
왕국 표준 보안 취약점 스캐닝 스크립트

사용법:
    python security_scanner.py [--repo owner/repo] [--format table|json]

주의:
    - gh CLI의 dependabot 명령어는 확장(extensions)으로 제공됩니다
    - core 명령어가 아니므로 `gh extension install`로 설치해야 합니다
    - 이 스크립트는 지피지기 원칙에 따라 설치 및 설정을 자동화합니다

필요한 설정:
    1. gh CLI 로그인: gh auth login
    2. dependabot-alerts 확장: gh extension install kumak1/gh-dependabot-alerts
    3. pip-audit 설치: pip install pip-audit
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class Vulnerability:
    """보안 취약점 데이터 클래스"""

    id: str
    package: str
    severity: str  # critical, high, medium, low
    summary: str
    source: str  # 'pip-audit' 또는 'dependabot'
    fixed_version: str | None = None
    installed_version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SecurityScanner:
    """AFO Kingdom 통합 보안 스캐너"""

    def __init__(self, repo: str | None = None) -> None:
        self.repo = repo
        self.vulnerabilities: list[Vulnerability] = []

    def check_gh_cli(self) -> bool:
        """gh CLI 설치 여부 확인"""
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            version = result.stdout.split()[2] if result.stdout else "unknown"
            logger.info(f"✅ gh CLI 확인됨 (v{version})")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ gh CLI가 설치되지 않았습니다")
            logger.info("   설치: https://cli.github.com/")
            return False

    def check_gh_authenticated(self) -> bool:
        """gh CLI 인증 여부 확인"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info("✅ gh CLI 인증됨")
                return True
            else:
                logger.error("❌ gh CLI 인증되지 않음")
                logger.info("   명령: gh auth login")
                return False
        except Exception as e:
            logger.error(f"❌ gh 인증 확인 실패: {e}")
            return False

    def check_dependabot_extension(self) -> bool:
        """gh dependabot-alerts 확장 설치 여부 확인"""
        try:
            result = subprocess.run(
                ["gh", "extension", "list"],
                capture_output=True,
                text=True,
                check=True,
            )
            if "dependabot-alerts" in result.stdout:
                logger.info("✅ gh dependabot-alerts 확장 확인됨")
                return True
            else:
                logger.warning("⚠️ gh dependabot-alerts 확장이 설치되지 않음")
                logger.info("   설치 명령:")
                logger.info("   gh extension install kumak1/gh-dependabot-alerts")
                return False
        except Exception as e:
            logger.error(f"❌ 확장 확인 실패: {e}")
            return False

    def install_dependabot_extension(self) -> bool:
        """gh dependabot-alerts 확장 설치"""
        logger.info("📦 gh dependabot-alerts 확장 설치 중...")
        try:
            result = subprocess.run(
                ["gh", "extension", "install", "kumak1/gh-dependabot-alerts", "--force"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info("✅ dependabot-alerts 확장 설치 완료")
                return True
            else:
                logger.error(f"❌ 설치 실패: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ 설치 중 오류: {e}")
            return False

    def check_pip_audit(self) -> bool:
        """pip-audit 설치 여부 확인"""
        try:
            result = subprocess.run(
                ["pip-audit", "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"✅ pip-audit 확인됨 ({version})")
                return True
            else:
                logger.warning("⚠️ pip-audit가 설치되지 않음")
                logger.info("   설치: pip install pip-audit")
                return False
        except FileNotFoundError:
            logger.warning("⚠️ pip-audit가 설치되지 않음")
            logger.info("   설치: pip install pip-audit")
            return False

    def scan_with_pip_audit(self, requirements_file: Path | None = None) -> list[Vulnerability]:
        """pip-audit로 로컬 패키지 스캔"""
        logger.info("🔍 pip-audit 스캔 시작...")

        cmd = ["pip-audit", "--format=json", "--desc"]

        if requirements_file and requirements_file.exists():
            cmd.extend(["--requirement", str(requirements_file)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            # pip-audit는 취약점 발견시 exit code 1을 반환
            if result.returncode not in [0, 1]:
                logger.error(f"❌ pip-audit 실행 실패: {result.stderr}")
                return []

            if not result.stdout:
                logger.info("✅ pip-audit: 취약점 없음")
                return []

            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.error("❌ pip-audit 결과 파싱 실패")
                return []

            vulnerabilities = []
            for item in data.get("dependencies", []):
                if "vulns" in item:
                    for vuln in item["vulns"]:
                        vulnerabilities.append(
                            Vulnerability(
                                id=vuln.get("id", "UNKNOWN"),
                                package=item.get("name", "unknown"),
                                severity=vuln.get("fix_versions", ["unknown"])[0]
                                if vuln.get("fix_versions")
                                else "unknown",
                                summary=vuln.get("description", "No description")[:100],
                                source="pip-audit",
                                installed_version=item.get("version"),
                                metadata=vuln,
                            )
                        )

            logger.info(f"🔍 pip-audit: {len(vulnerabilities)}개 취약점 발견")
            return vulnerabilities

        except Exception as e:
            logger.error(f"❌ pip-audit 스캔 실패: {e}")
            return []

    def scan_with_dependabot(self, severity: str = "high,critical") -> list[Vulnerability]:
        """gh dependabot-alerts로 GitHub 저장소 스캔"""
        if not self.repo:
            logger.warning("⚠️ 저장소(--repo)가 지정되지 않아 dependabot 스킵")
            return []

        logger.info(f"🔍 gh dependabot-alerts 스캔 시작 ({self.repo})...")

        try:
            result = subprocess.run(
                [
                    "gh",
                    "dependabot-alerts",
                    "--repo",
                    self.repo,
                    "--severity",
                    severity,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"❌ dependabot-alerts 실패: {result.stderr}")
                return []

            if not result.stdout:
                logger.info("✅ dependabot-alerts: 취약점 없음")
                return []

            # dependabot-alerts는 JSON 라인별 출력
            vulnerabilities = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    alert = json.loads(line)
                    vulnerabilities.append(
                        Vulnerability(
                            id=str(alert.get("number", "UNKNOWN")),
                            package=alert.get("package", {}).get("name", "unknown"),
                            severity=alert.get("security_advisory", {}).get("severity", "unknown"),
                            summary=alert.get("security_advisory", {}).get("summary", "No summary"),
                            source="dependabot",
                            fixed_version=alert.get("security_vulnerability", {}).get(
                                "patched_versions", [None]
                            )[0],
                            metadata=alert,
                        )
                    )
                except json.JSONDecodeError:
                    continue

            logger.info(f"🔍 dependabot-alerts: {len(vulnerabilities)}개 취약점 발견")
            return vulnerabilities

        except Exception as e:
            logger.error(f"❌ dependabot-alerts 스캔 실패: {e}")
            return []

    def generate_report(self, format_type: str = "table") -> str:
        """스캔 결과 보고서 생성"""
        if format_type == "json":
            return json.dumps(
                [v.__dict__ for v in self.vulnerabilities],
                indent=2,
                ensure_ascii=False,
            )

        # Table format
        if not self.vulnerabilities:
            return "✅ 보안 취약점이 발견되지 않았습니다."

        lines = [
            "",
            "=" * 100,
            "🛡️ AFO Kingdom Security Scan Report",
            "=" * 100,
            f"총 취약점: {len(self.vulnerabilities)}개",
            "",
        ]

        # Group by severity
        severity_order = ["critical", "high", "medium", "low"]
        by_severity: dict[str, list[Vulnerability]] = {s: [] for s in severity_order}

        for v in self.vulnerabilities:
            sev = v.severity.lower()
            if sev in by_severity:
                by_severity[sev].append(v)
            else:
                by_severity["low"].append(v)

        for severity in severity_order:
            vulns = by_severity[severity]
            if vulns:
                icon = {"critical": "🚨", "high": "⚠️", "medium": "📋", "low": "📌"}.get(
                    severity, "📌"
                )
                lines.append(f"\n{icon} {severity.upper()} ({len(vulns)}개)")
                lines.append("-" * 100)

                for v in vulns[:10]:  # Show max 10 per severity
                    lines.append(f"  [{v.source}] {v.package}")
                    lines.append(f"    ID: {v.id}")
                    lines.append(f"    설명: {v.summary[:60]}...")
                    if v.fixed_version:
                        lines.append(f"    조치: {v.fixed_version}로 업그레이드")
                    lines.append("")

                if len(vulns) > 10:
                    lines.append(f"  ... 외 {len(vulns) - 10}개")

        lines.extend(
            [
                "",
                "=" * 100,
                "📋 권장 조치:",
                "1. Critical/High 취약점을 즉시 패치하세요",
                "2. pip-audit --fix로 자동 수정을 시도하세요",
                "3. requirements.txt를 업데이트하세요",
                "=" * 100,
            ]
        )

        return "\n".join(lines)

    def scan(self, requirements_file: Path | None = None, severity: str = "high,critical") -> None:
        """전체 스캔 실행"""
        logger.info("🚀 AFO Kingdom Security Scanner 시작")
        logger.info("=" * 60)

        # Setup checks
        gh_ok = self.check_gh_cli()

        if gh_ok:
            self.check_gh_authenticated()

            if not self.check_dependabot_extension():
                self.install_dependabot_extension()

        self.check_pip_audit()

        logger.info("=" * 60)

        # Scan with pip-audit
        pip_vulns = self.scan_with_pip_audit(requirements_file)
        self.vulnerabilities.extend(pip_vulns)

        # Scan with dependabot if repo specified
        if self.repo and gh_ok:
            gh_vulns = self.scan_with_dependabot(severity)
            self.vulnerabilities.extend(gh_vulns)

        logger.info("=" * 60)


def main() -> int:
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="AFO Kingdom Security Scanner - 통합 보안 취약점 스캐너",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    # 로컬 패키지 스캔
    python security_scanner.py
    
    # 특정 requirements 파일 스캔
    python security_scanner.py --req requirements.txt
    
    # GitHub 저장소 dependabot 알림 확인
    python security_scanner.py --repo owner/repo
    
    # JSON 형식으로 출력
    python security_scanner.py --format json

참고:
    gh CLI의 dependabot 명령어는 확장(extension)으로 제공됩니다.
    설치: gh extension install kumak1/gh-dependabot-alerts
        """,
    )
    parser.add_argument(
        "--repo",
        help="GitHub 저장소 (owner/repo 형식). 지정시 dependabot-alerts도 확인",
    )
    parser.add_argument(
        "--req",
        "--requirements",
        type=Path,
        help="requirements.txt 파일 경로",
    )
    parser.add_argument(
        "--severity",
        default="high,critical",
        help="심각도 필터 (기본: high,critical)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="출력 형식 (기본: table)",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="필요한 도구 설치만 수행",
    )

    args = parser.parse_args()

    scanner = SecurityScanner(repo=args.repo)

    if args.setup:
        logger.info("🔧 설정 모드 - 필요한 도구 설치")
        scanner.check_gh_cli()
        scanner.check_gh_authenticated()
        if not scanner.check_dependabot_extension():
            scanner.install_dependabot_extension()
        scanner.check_pip_audit()
        return 0

    # Run scan
    scanner.scan(requirements_file=args.req, severity=args.severity)

    # Generate report
    report = scanner.generate_report(format_type=args.format)
    print(report)

    # Exit code based on findings
    critical_high = [v for v in scanner.vulnerabilities if v.severity in ["critical", "high"]]
    return 1 if critical_high else 0


if __name__ == "__main__":
    sys.exit(main())
