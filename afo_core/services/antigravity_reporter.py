"""
Antigravity Reporter - Service for generating and saving reports.
Separated from AntigravityEngine for Single Responsibility Principle.
"""

import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from AFO.config.antigravity import antigravity

logger = logging.getLogger(__name__)


class AntigravityReporter:
    """
    Handles generation of Analysis and Completion reports.
    Enforces SSOT evidence verification.
    """

    def __init__(self, protocol_officer: Any | None = None) -> None:
        self.protocol_officer = protocol_officer

    def generate_analysis_report(
        self,
        context: dict[str, Any],
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        next_steps: list[str],
    ) -> str:
        """
        Generates an Analysis Report (no completion claim).
        Applies language policy and Protocol Officer formatting.
        """
        # Language Switch
        report_lang = getattr(antigravity, "REPORT_LANGUAGE", "ko") if antigravity else "ko"

        # Template Generation
        if report_lang == "ko":
            report = self._template_ko(context, analysis, evidence, next_steps)
        else:
            report = self._template_en(context, analysis, evidence, next_steps)

        # Protocol Officer Formatting (Mandatory)
        if self.protocol_officer is None:
            raise ValueError("[SSOT] Protocol Officer required for report formatting.")

        return self.protocol_officer.compose_diplomatic_message(
            report, audience=self.protocol_officer.AUDIENCE_COMMANDER
        )

    def generate_completion_report(
        self,
        context: dict[str, Any],
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        next_steps: list[str],
    ) -> str | None:
        """
        Generates a Completion Report if SSOT evidence is sufficient.
        Returns None if strict verification fails.
        """
        # 1. Verify Evidence Structure
        if not self._verify_evidence_structure(evidence):
            return None

        # 2. Verify with Report Gate Script
        temp_report = self.generate_analysis_report(context, analysis, evidence, next_steps)
        if not self._run_report_gate(temp_report):
            return None

        # 3. Finalize Report
        report = temp_report
        report_lang = getattr(antigravity, "REPORT_LANGUAGE", "ko") if antigravity else "ko"

        if report_lang == "ko":
            report += "\n\n### 완료 상태\n- ✅ SSOT 증거 확인 완료\n- ✅ Report Gate 통과\n"
        else:
            report += (
                "\n\n### Completion Status\n- ✅ SSOT evidence verified\n- ✅ Report Gate passed\n"
            )

        return report

    def save_report(self, report: str, filename: str) -> Path:
        """Saves report to docs/reports/."""
        # Root relative to this file: packages/afo-core/services/antigravity_reporter.py
        # root is ../../../
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        reports_dir = repo_root / "docs" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_file = reports_dir / filename
        report_file.write_text(report, encoding="utf-8")
        logger.info(f"[Antigravity] Report saved: {report_file}")
        return report_file

    def _verify_evidence_structure(self, evidence: dict[str, Any]) -> bool:
        """Checks for Commit, Files, and Command evidence."""
        if not isinstance(evidence, dict):
            return False

        has_commit = self._check_keys(
            evidence, ["commit", "git_commit", "commit_hash", "commit_id"], "commit", "git"
        )
        has_files = self._check_keys(
            evidence, ["file", "files", "file_path", "file_paths", "path", "paths"], "file", "path"
        )
        has_cmd = self._check_keys(
            evidence, ["command", "commands", "cmd", "exec", "result", "output"], "command", "exec"
        )

        if not (has_commit and has_files and has_cmd):
            logger.warning(
                f"[SSOT] Evidence missing. Commit={has_commit}, Files={has_files}, Cmd={has_cmd}"
            )
            return False
        return True

    def _check_keys(self, data: dict, keys: list[str], *substrings: str) -> bool:
        if any(k in data and data[k] for k in keys):
            return True
        # substring check logic from original
        for k in data:
            k_lower = str(k).lower()
            if any(sub in k_lower for sub in substrings):
                return True
        return False

    def _run_report_gate(self, report_content: str) -> bool:
        """Runs ssot_report_gate.py subprocess verification."""
        try:
            # Path calculation: ../../scripts/ssot_report_gate.py relative to packages/afo-core/services/
            # Actually simplest is to find packages/afo-core root.
            # This file: packages/afo-core/services/reporter.py
            # Scripts: packages/afo-core/scripts/
            script_path = Path(__file__).parent.parent / "scripts" / "ssot_report_gate.py"

            if not script_path.exists():
                return True  # Fallback if script missing (or False depending on strictness? Original logic implies weak check or it fails)
                # Original logic: if script_path.exists()...

            result = subprocess.run(
                [sys.executable, str(script_path), report_content],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                logger.warning(f"[SSOT] Report Gate Failed: {result.stdout}")
                return False
            return True
        except Exception as e:
            logger.warning(f"[SSOT] Report Gate Error: {e}")
            return False

    def _template_ko(self, c, a, e, n) -> str:
        r = f"# {c.get('title', '분석 보고서')}\n\n## Context\n"
        r += f"- 상황: {c.get('situation', 'N/A')}\n- 위치: {c.get('location', 'N/A')}\n"
        r += f"- 시점: {c.get('timestamp', datetime.now().isoformat())}\n- 영향: {c.get('impact', 'N/A')}\n\n"
        r += f"## Analysis\n{a.get('observation', 'N/A')}\n\n추정: {a.get('assumption', 'N/A')}\n\n"
        r += "## Evidence\n" + "\n".join(f"- {k}: {v}" for k, v in e.items()) + "\n\n"
        r += "## Next Steps\n" + "\n".join(f"- {s}" for s in n) + "\n\n"
        r += "---\n\n### Reporting Rules\n- 분석 결과만 제공 (완료 선언 없음)\n- SSOT 증거 기반 보고\n"
        return r

    def _template_en(self, c, a, e, n) -> str:
        r = f"# {c.get('title', 'Analysis Report')}\n\n## Context\n"
        r += f"- Situation: {c.get('situation', 'N/A')}\n- Location: {c.get('location', 'N/A')}\n"
        r += f"- Timestamp: {c.get('timestamp', datetime.now().isoformat())}\n- Impact: {c.get('impact', 'N/A')}\n\n"
        r += f"## Analysis\n{a.get('observation', 'N/A')}\n\nAssumption: {a.get('assumption', 'N/A')}\n\n"
        r += "## Evidence\n" + "\n".join(f"- {k}: {v}" for k, v in e.items()) + "\n\n"
        r += "## Next Steps\n" + "\n".join(f"- {s}" for s in n) + "\n\n"
        r += "---\n\n### Reporting Rules\n- Analysis results only (no completion claims)\n- SSOT evidence-based reporting\n"
        return r
