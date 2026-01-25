# Trinity Score: 90.0 (Established by Chancellor)
"""
Antigravity Protocol Officer Bridge - 외부 시스템 통합 모듈
Protocol Officer를 통한 외교적 메시지 포맷팅
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ProtocolOfficerBridge:
    """
    Protocol Officer 통합 브릿지
    외부 메시지 포맷팅을 위한 인터페이스
    """

    def __init__(self) -> None:
        self.protocol_officer = None
        self._load_protocol_officer()

    def _load_protocol_officer(self) -> None:
        """Protocol Officer 동적 로딩 (선택적 의존성)"""
        try:
            from services.protocol_officer import protocol_officer

            self.protocol_officer = protocol_officer
            logger.info("✅ Protocol Officer 통합 성공")
        except ImportError:
            logger.warning("⚠️ Protocol Officer를 찾을 수 없음 - 메시지 포맷팅 비활성화")
            self.protocol_officer = None

    def format_decision_message(self, result: dict[str, Any]) -> str:
        """
        결정 메시지 포맷팅
        Protocol Officer를 통한 외교적 메시지 생성

        Args:
            result: 품질 게이트 평가 결과

        Returns:
            포맷팅된 메시지
        """
        # 기본 메시지 생성
        message = self._create_basic_message(result)

        # Protocol Officer 포맷팅 적용 (선택적)
        if self.protocol_officer:
            try:
                formatted = self.protocol_officer.compose_diplomatic_message(
                    message, audience=self.protocol_officer.AUDIENCE_COMMANDER
                )
                return str(formatted)
            except Exception as e:
                logger.warning(f"Protocol Officer 포맷팅 실패: {e}")

        return message

    def _create_basic_message(self, result: dict[str, Any]) -> str:
        """
        기본 메시지 생성
        Protocol Officer 없이도 작동하는 기본 포맷
        """
        decision = result.get("decision", "UNKNOWN")
        trinity_score = result.get("trinity_score", 0.0)
        risk_score = result.get("risk_score", 0.0)
        confidence = result.get("confidence", 0.0)

        message = "품질 게이트 평가 결과:\n"
        message += f"- 결정: {decision}\n"
        message += f"- Trinity Score: {trinity_score:.1f}\n"
        message += f"- Risk Score: {risk_score:.1f}\n"
        message += f"- 신뢰도: {confidence:.1%}"

        recommendations = result.get("recommendations", [])
        if recommendations:
            message += "\n\n권장사항:\n"
            for rec in recommendations:
                message += f"- {rec}\n"

        return message

    def generate_analysis_report(
        self,
        context: dict[str, Any],
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        next_steps: list[str],
    ) -> str:
        """
        분석 보고서 생성
        Protocol Officer를 통한 외교적 보고서 포맷팅

        Args:
            context: 보고서 맥락
            analysis: 분석 결과
            evidence: 증거 데이터
            next_steps: 다음 단계

        Returns:
            포맷팅된 보고서
        """
        # 기본 보고서 생성
        report = self._create_basic_report(context, analysis, evidence, next_steps)

        # Protocol Officer 포맷팅 적용 (선택적)
        if self.protocol_officer:
            try:
                formatted = self.protocol_officer.compose_diplomatic_message(
                    report, audience=self.protocol_officer.AUDIENCE_COMMANDER
                )
                return str(formatted)
            except Exception as e:
                logger.warning(f"Protocol Officer 보고서 포맷팅 실패: {e}")

        return report

    def _create_basic_report(
        self,
        context: dict[str, Any],
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        next_steps: list[str],
    ) -> str:
        """
        기본 보고서 생성
        Protocol Officer 없이도 작동하는 기본 포맷
        """
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


# 싱글톤 인스턴스
protocol_officer_bridge = ProtocolOfficerBridge()
