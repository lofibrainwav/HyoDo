# Trinity Score: 90.0 (Established by Chancellor)
"""
Antigravity Reporting Module - 보고서 생성 모듈
완료 보고서와 분석 보고서 생성 기능
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    보고서 생성기
    분석 보고서와 완료 보고서 생성
    """

    def __init__(self) -> None:
        self.reports_dir = Path("docs/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_completion_report(
        self,
        context: dict[str, Any],
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        next_steps: list[str],
    ) -> str | None:
        """
        완료 보고서 생성 (SSOT 증거 필수)
        증거가 없으면 None 반환 (생성 금지)

        Args:
            context: 보고서 맥락
            analysis: 분석 결과
            evidence: 증거 데이터
            next_steps: 다음 단계

        Returns:
            완료 보고서 또는 None (증거 부족 시)
        """
        # SSOT 증거 검증
        if not self._validate_ssot_evidence(evidence):
            logger.warning("[SSOT] 완료 보고서 생성 차단: 필수 증거 부족")
            return None

        # SSOT Report Gate 검증
        if not self._validate_report_gate(context, analysis, evidence, next_steps):
            logger.warning("[SSOT] Report Gate 실패: 완료 보고서 생성 차단")
            return None

        # 완료 보고서 생성
        report = self._create_completion_report(context, analysis, evidence, next_steps)
        return report

    def generate_analysis_report(
        self,
        context: dict[str, Any],
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        next_steps: list[str],
    ) -> str:
        """
        분석 보고서 생성 (증거 검증 없음)
        항상 생성 가능

        Args:
            context: 보고서 맥락
            analysis: 분석 결과
            evidence: 증거 데이터
            next_steps: 다음 단계

        Returns:
            분석 보고서
        """
        return self._create_analysis_report(context, analysis, evidence, next_steps)

    def _validate_ssot_evidence(self, evidence: dict[str, Any]) -> bool:
        """
        SSOT 증거 검증
        commit, files, command 증거가 모두 있는지 확인
        """
        # 1. commit 검증
        has_commit = self._check_commit_evidence(evidence)

        # 2. files 검증
        has_files = self._check_files_evidence(evidence)

        # 3. command 검증
        has_command = self._check_command_evidence(evidence)

        return has_commit and has_files and has_command

    def _check_commit_evidence(self, evidence: dict[str, Any]) -> bool:
        """commit 증거 확인"""
        commit_keys = ["commit", "git_commit", "commit_hash", "commit_id"]
        has_commit = any(key in evidence and evidence[key] for key in commit_keys)

        if not has_commit:
            evidence_str = str(evidence).lower()
            has_commit = "commit" in evidence_str or "git" in evidence_str

        return has_commit

    def _check_files_evidence(self, evidence: dict[str, Any]) -> bool:
        """files 증거 확인"""
        file_keys = ["file", "files", "file_path", "file_paths", "path", "paths"]
        has_files = any(key in evidence and evidence[key] for key in file_keys)

        if not has_files:
            evidence_str = str(evidence).lower()
            has_files = "file" in evidence_str or "path" in evidence_str

        return has_files

    def _check_command_evidence(self, evidence: dict[str, Any]) -> bool:
        """command 증거 확인"""
        command_keys = ["command", "commands", "cmd", "exec", "result", "output"]
        has_command = any(key in evidence and evidence[key] for key in command_keys)

        if not has_command:
            evidence_str = str(evidence).lower()
            has_command = (
                "command" in evidence_str
                or "cmd" in evidence_str
                or "exec" in evidence_str
                or "result" in evidence_str
            )

        return has_command

    def _validate_report_gate(
        self,
        context: dict[str, Any],
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        next_steps: list[str],
    ) -> bool:
        """
        SSOT Report Gate 검증
        scripts/ssot_report_gate.py를 통한 검증
        """
        try:
            import subprocess
            import sys
            from pathlib import Path

            # 임시 리포트 생성
            temp_report = self._create_analysis_report(context, analysis, evidence, next_steps)

            # ssot_report_gate.py 경로
            script_path = (
                Path(__file__).parent.parent.parent.parent / "scripts" / "ssot_report_gate.py"
            )

            if script_path.exists():
                result = subprocess.run(
                    [sys.executable, str(script_path), temp_report],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return result.returncode == 0
            else:
                logger.warning(f"SSOT Report Gate 스크립트 없음: {script_path}")
                return False

        except Exception as e:
            logger.warning(f"SSOT Report Gate 검증 실패: {e}")
            return False

    def _create_analysis_report(
        self,
        context: dict[str, Any],
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        next_steps: list[str],
    ) -> str:
        """분석 보고서 생성"""
        from datetime import datetime

        report = f"# {context.get('title', '분석 보고서')}\n\n"
        report += "## Context\n"
        report += f"- 상황: {context.get('situation', 'N/A')}\n"
        report += f"- 위치: {context.get('location', 'N/A')}\n"
        report += f"- 시점: {context.get('timestamp', datetime.now().isoformat())}\n"
        report += f"- 영향: {context.get('impact', 'N/A')}\n\n"

        report += "## Analysis\n"
        report += f"{analysis.get('observation', 'N/A')}\n\n"
        report += f"추정: {analysis.get('assumption', 'N/A')}\n\n"

        report += "## Evidence\n"
        for key, value in evidence.items():
            report += f"- {key}: {value}\n"
        report += "\n"

        report += "## Next Steps\n"
        for step in next_steps:
            report += f"- {step}\n"
        report += "\n"

        report += "---\n\n"
        report += "### Reporting Rules\n"
        report += "- 분석 결과만 제공 (완료 선언 없음)\n"
        report += "- SSOT 증거 기반 보고\n"

        return report

    def _create_completion_report(
        self,
        context: dict[str, Any],
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        next_steps: list[str],
    ) -> str:
        """완료 보고서 생성"""
        report = self._create_analysis_report(context, analysis, evidence, next_steps)

        # 완료 상태 추가
        report += "\n\n### 완료 상태\n"
        report += "- ✅ SSOT 증거 확인 완료\n"
        report += "- ✅ Report Gate 통과\n"

        return report

    def save_report(self, report: str, filename: str) -> Path:
        """
        보고서를 docs/reports/에 저장

        Args:
            report: 보고서 내용
            filename: 파일명

        Returns:
            저장된 파일 경로
        """
        report_file: Path = self.reports_dir / filename
        report_file.write_text(report, encoding="utf-8")
        logger.info(f"✅ 보고서 저장: {report_file}")

        return report_file


# 싱글톤 인스턴스
report_generator = ReportGenerator()
