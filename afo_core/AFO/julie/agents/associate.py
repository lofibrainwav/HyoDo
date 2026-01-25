import uuid
from datetime import datetime
from typing import Any

from AFO.julie.agents.types import AgentLevel, RCAteWorkflow


class AssociateAgent:
    """Associate 레벨: 초안 작성 및 데이터 수집"""

    def __init__(self) -> None:
        self.level = AgentLevel.ASSOCIATE
        self.evidence_id = str(uuid.uuid4())

    def process_request(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Associate 레벨 처리"""
        rcate = RCAteWorkflow(
            role="Associate: 데이터 수집 및 초안 작성",
            context={
                "irs_ssot": "Legacy Search Disabled",
                "customer_data": input_data,
                "business_purpose": input_data.get("purpose", "tax_optimization"),
            },
            action="고객 데이터 정형화 및 초안 리포트 생성",
            task=[
                "입력 데이터 검증 및 카테고리 분류",
                "관련 IRS/FTB 규정 검색",
                "초안 계산 결과 생성",
                "근거 목록 정리",
            ],
            execution={},
        )

        # Associate 작업 실행
        structured_data = self._structure_customer_data(input_data)
        draft_report = self._create_draft_report(structured_data)
        evidence_list = self._collect_evidence_links(structured_data)

        rcate.execution = {
            "structured_data": structured_data,
            "draft_report": draft_report,
            "evidence_list": evidence_list,
            "confidence_score": 0.85,
        }

        return {
            "level": self.level,
            "rcate_workflow": rcate.model_dump(),
            "output": {
                "structured_data": structured_data,
                "draft_report": draft_report,
                "evidence_list": evidence_list,
            },
            "next_actions": ["Manager 검토 요청"],
            "evidence_id": self.evidence_id,
        }

    def _structure_customer_data(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """고객 데이터를 정형화"""
        return {
            "entity_type": input_data.get("entity_type", "C_CORP"),
            "tax_year": input_data.get("tax_year", 2025),
            "assets": input_data.get("assets", []),
            "income": input_data.get("income", 0),
            "prior_returns": input_data.get("prior_returns", []),
            "business_purpose": input_data.get("purpose", "tax_optimization"),
        }

    def _create_draft_report(self, structured_data: dict[str, Any]) -> dict[str, Any]:
        """초안 리포트 생성 (사실만)"""
        return {
            "entity_info": f"{structured_data['entity_type']} for tax year {structured_data['tax_year']}",
            "key_assets": [
                asset.get("description", "Unknown") for asset in structured_data["assets"]
            ],
            "estimated_income": structured_data["income"],
            "potential_strategies": [
                "§179 deduction",
                "Bonus depreciation",
                "R&D credit",
            ],
            "disclaimer": "This is a preliminary analysis. Final determination requires professional review.",
        }

    def _collect_evidence_links(self, structured_data: dict[str, Any]) -> list[str]:
        """근거 링크 수집"""
        return [
            "https://www.irs.gov/pub/irs-pdf/p946.pdf (§179 Instructions)",
            "https://www.irs.gov/newsroom/one-big-beautiful-bill-act-tax-deductions-for-working-americans-and-seniors (OBBBA)",
            "https://www.irs.gov/pub/irs-pdf/i4562.pdf (Form 4562 Instructions)",
            f"artifacts/ticket033_irs_updates_{datetime.now().strftime('%Y%m%d')}.jsonl",
        ]
