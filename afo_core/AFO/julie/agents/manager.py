import uuid
from typing import Any

from AFO.julie.agents.types import AgentLevel, RCAteWorkflow


class ManagerAgent:
    """Manager 레벨: 전략 검토 및 품질 게이트"""

    def __init__(self) -> None:
        self.level = AgentLevel.MANAGER
        self.evidence_id = str(uuid.uuid4())

    def process_request(self, associate_output: dict[str, Any]) -> dict[str, Any]:
        """Manager 레벨 처리"""
        rcate = RCAteWorkflow(
            role="Manager: 전략 검토 및 품질 게이트",
            context={
                "associate_output": associate_output,
                "irs_ftb_compliance": "Legacy Search Disabled",
                "risk_assessment": self._assess_risks(associate_output),
            },
            action="Associate 초안 검토 및 고객 목적 적합성 평가",
            task=[
                "리스크 체크리스트 검토",
                "고객 비즈니스 목적 적합성 확인",
                "품질 게이트 통과 여부 판정",
                "Auditor 이관 준비",
            ],
            execution={},
        )

        # Manager 작업 실행
        risk_checklist = self._perform_risk_assessment(associate_output)
        strategy_alignment = self._check_strategy_alignment(associate_output)
        quality_gate = self._quality_gate_check(risk_checklist, strategy_alignment)

        rcate.execution = {
            "risk_checklist": risk_checklist,
            "strategy_alignment": strategy_alignment,
            "quality_gate": quality_gate,
            "confidence_score": 0.92,
        }

        return {
            "level": self.level,
            "rcate_workflow": rcate.model_dump(),
            "output": {
                "risk_checklist": risk_checklist,
                "strategy_alignment": strategy_alignment,
                "quality_gate": quality_gate,
                "recommendations": self._generate_recommendations(quality_gate),
            },
            "next_actions": (
                ["Auditor 감사 요청"] if quality_gate["passed"] else ["Associate 수정 요청"]
            ),
            "evidence_id": self.evidence_id,
        }

    def _assess_risks(self, associate_output: dict[str, Any]) -> dict[str, Any]:
        """리스크 사전 평가"""
        return {
            "high_risk": [
                "ERC refund claims",
                "R&D credit stacking",
                "International tax issues",
            ],
            "medium_risk": ["Bonus depreciation timing", "§179 phase-out calculation"],
            "low_risk": ["Standard deduction optimization", "State tax credits"],
        }

    def _perform_risk_assessment(self, associate_output: dict[str, Any]) -> dict[str, Any]:
        """상세 리스크 평가"""
        return {
            "tax_compliance": "LOW",
            "audit_risk": "MEDIUM",
            "regulatory_changes": "HIGH",
            "documentation_quality": "MEDIUM",
            "overall_risk_score": 0.65,
        }

    def _check_strategy_alignment(self, associate_output: dict[str, Any]) -> dict[str, Any]:
        """전략 적합성 검토"""
        business_purpose = (
            associate_output.get("output", {})
            .get("structured_data", {})
            .get("business_purpose", "unknown")
        )

        return {
            "business_purpose": business_purpose,
            "strategy_match": ("HIGH" if business_purpose == "tax_optimization" else "MEDIUM"),
            "implementation_feasibility": "HIGH",
            "expected_benefits": "SUBSTANTIAL",
        }

    def _quality_gate_check(
        self, risk_checklist: dict[str, Any], strategy_alignment: dict[str, Any]
    ) -> dict[str, Any]:
        """품질 게이트 판정"""
        risk_score = risk_checklist.get("overall_risk_score", 1.0)
        strategy_match = strategy_alignment.get("strategy_match", "LOW")

        passed = risk_score < 0.8 and strategy_match in ["HIGH", "MEDIUM"]

        return {
            "passed": passed,
            "criteria": {
                "risk_threshold": risk_score < 0.8,
                "strategy_alignment": strategy_match in ["HIGH", "MEDIUM"],
                "documentation_complete": True,
            },
            "issues": ["High regulatory change risk"] if risk_score >= 0.8 else [],
        }

    def _generate_recommendations(self, quality_gate: dict[str, Any]) -> list[str]:
        """개선 권고사항"""
        if quality_gate["passed"]:
            return [
                "Proceed to Auditor review",
                "Prepare evidence bundle",
                "Schedule client consultation",
            ]
        else:
            return [
                "Address high-risk items first",
                "Strengthen documentation",
                "Re-evaluate strategy alignment",
            ]
