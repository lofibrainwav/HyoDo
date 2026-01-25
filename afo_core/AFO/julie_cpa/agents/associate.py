"""
Julie CPA Associate Agent - Data Collection & Initial Analysis

첫 번째 티어 에이전트: 세금 분석, 증거 수집 및 초안 작성을 담당합니다.
"""

from datetime import datetime
from typing import Any

from .types import AssociateResult, ClientData, TaxDocument


class JulieAssociateAgent:
    """Julie CPA Associate Agent - Data Collection & Initial Analysis"""

    def __init__(self) -> None:
        self.evidence_required = True
        self.max_draft_iterations = 3
        self.trinity_score_threshold = 0.75

    async def analyze_tax_scenario(
        self,
        client_data: ClientData,
        tax_documents: list[TaxDocument],
        analysis_type: str,
    ) -> AssociateResult:
        """Perform initial tax analysis and draft preparation"""

        # Validate input data
        if not self._validate_client_data(client_data):
            raise ValueError("Invalid client data provided")

        if not tax_documents:
            raise ValueError("Tax documents are required for analysis")

        # Collect and validate evidence
        evidence_links = self._collect_evidence(tax_documents)

        # Perform initial calculations
        calculations = self._perform_calculations(client_data, analysis_type)

        # Generate draft analysis
        draft_analysis = {
            "client_id": client_data.get("client_id"),
            "tax_year": client_data.get("tax_year"),
            "analysis_type": analysis_type,
            "calculations": calculations,
            "assumptions": self._generate_assumptions(client_data, analysis_type),
            "draft_timestamp": datetime.now().isoformat(),
            "confidence_level": self._calculate_confidence(evidence_links),
        }

        # Calculate Trinity Score for draft
        trinity_score = self._calculate_draft_trinity_score(draft_analysis, evidence_links)

        return {
            "draft_analysis": draft_analysis,
            "evidence_links": evidence_links,
            "trinity_score": trinity_score,
            "recommendations": self._generate_draft_recommendations(draft_analysis),
        }

    def _validate_client_data(self, client_data: dict[str, Any]) -> bool:
        """Validate client data completeness"""
        required_fields = ["client_id", "tax_year", "filing_status", "income"]
        return all(field in client_data for field in required_fields)

    def _collect_evidence(self, tax_documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Collect and validate evidence links"""
        evidence_links = []
        for doc in tax_documents:
            evidence_links.append(
                {
                    "type": doc.get("type", "unknown"),
                    "reference": doc.get("reference", ""),
                    "validation_status": "validated",  # Simplified validation
                    "timestamp": datetime.now().isoformat(),
                }
            )
        return evidence_links

    def _perform_calculations(
        self, client_data: dict[str, Any], analysis_type: str
    ) -> dict[str, Any]:
        """Perform tax calculations based on analysis type"""
        if analysis_type == "standard_deduction":
            return self._calculate_standard_deduction(client_data)
        elif analysis_type == "roth_conversion":
            return self._calculate_roth_conversion(client_data)
        else:
            return {"error": f"Unsupported analysis type: {analysis_type}"}

    def _calculate_standard_deduction(self, client_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate standard deduction"""
        filing_status = client_data.get("filing_status", "single")
        tax_year = client_data.get("tax_year", 2025)

        # Simplified standard deduction table
        standard_deductions = {
            "single": 14600,
            "married_filing_jointly": 29200,
            "head_of_household": 21900,
        }

        deduction = standard_deductions.get(filing_status, 14600)
        return {
            "standard_deduction_amount": deduction,
            "filing_status": filing_status,
            "tax_year": tax_year,
        }

    def _calculate_roth_conversion(self, client_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate Roth IRA conversion impact"""
        income = client_data.get("income", 0)
        conversion_amount = min(income * 0.5, 100000)  # Simplified conversion amount

        # Simplified tax calculation
        marginal_rate = 0.22 if income > 50000 else 0.12
        tax_liability = conversion_amount * marginal_rate

        return {
            "conversion_amount": conversion_amount,
            "marginal_rate": marginal_rate,
            "tax_liability": tax_liability,
            "net_benefit": conversion_amount - tax_liability,
        }

    def _generate_assumptions(self, client_data: dict[str, Any], analysis_type: str) -> list[str]:
        """Generate analysis assumptions"""
        assumptions = [
            "All provided information is accurate and complete",
            "Tax laws remain unchanged for the analysis period",
            "No additional income or deductions not disclosed",
        ]

        if analysis_type == "roth_conversion":
            assumptions.extend(
                [
                    "Conversion is completed in current tax year",
                    "No changes in tax bracket after conversion",
                ]
            )

        return assumptions

    def _calculate_confidence(self, evidence_links: list[dict[str, Any]]) -> float:
        """Calculate confidence level based on evidence"""
        base_confidence = 0.7
        evidence_bonus = min(len(evidence_links) * 0.1, 0.3)
        return min(base_confidence + evidence_bonus, 1.0)

    def _calculate_draft_trinity_score(
        self, draft_analysis: dict[str, Any], evidence_links: list[dict[str, Any]]
    ) -> float:
        """Calculate Trinity Score for draft analysis"""
        # Simplified Trinity Score calculation
        truth_score = 0.85 if len(evidence_links) >= 3 else 0.7
        goodness_score = 0.90  # Conservative estimate for Associate level
        beauty_score = 0.80 if draft_analysis.get("calculations") else 0.6
        serenity_score = 0.95  # Associate focuses on clarity
        eternity_score = 0.75  # Basic documentation

        # AFO Kingdom Trinity Score formula
        trinity_score = (
            truth_score * 0.35
            + goodness_score * 0.35
            + beauty_score * 0.20
            + serenity_score * 0.08
            + eternity_score * 0.02
        )

        return trinity_score

    def _generate_draft_recommendations(self, draft_analysis: dict[str, Any]) -> list[str]:
        """Generate recommendations for draft review"""
        recommendations = [
            "Review calculations with Manager Agent for strategic assessment",
            "Validate all evidence links before finalization",
            "Consider alternative scenarios for comprehensive analysis",
        ]
        return recommendations
