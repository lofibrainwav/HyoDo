"""
AI Enhanced Julie CPA Workflow - Phase 1 Complete Integration

기존 Julie CPA 3-tier 시스템을 Claude + Gemini AI로 완전 증강
단일 진입점으로 AI 증강 세무 분석 워크플로우 제공
"""

from datetime import datetime
from typing import Any

from .associate import JulieAssociateAgent
from .auditor import JulieAuditorAgent
from .claude_tax_assistant import ClaudeTaxAssistant
from .gemini_financial_predictor import GeminiFinancialPredictor
from .manager import JulieManagerAgent
from .types import (
    AssociateResult,
    ClaudeResult,
    ClientData,
    DraftAnalysis,
    FinalResults,
    GeminiResult,
    HistoricalDataPoint,
    ManagerResult,
    PredictionSummary,
    TaxDocument,
    WorkflowResult,
)


class AIEnhancedJulieCPAWorkflow:
    """
    AI 증강 Julie CPA 워크플로우 오케스트레이터

    Phase 1: Claude + Gemini AI 완전 통합
    기존 3-tier 시스템을 AI로 증강하면서 호환성 유지
    """

    def __init__(self) -> None:
        # 기존 Julie CPA 에이전트
        self.associate = JulieAssociateAgent()
        self.manager = JulieManagerAgent()
        self.auditor = JulieAuditorAgent()

        # AI 증강 에이전트 (Phase 1)
        self.claude_assistant = ClaudeTaxAssistant()
        self.gemini_predictor = GeminiFinancialPredictor()

    async def process_ai_enhanced_workflow(
        self,
        client_data: ClientData,
        tax_documents: list[TaxDocument],
        analysis_type: str = "comprehensive",
        enable_predictions: bool = True,
        claude_client: Any = None,
        gemini_client: Any = None,
    ) -> WorkflowResult:
        """
        AI 증강 Julie CPA 완전 워크플로우 실행

        Phase 1 통합 프로세스:
        1. 기존 Julie CPA Associate 분석
        2. Claude AI 증강 세무 해석
        3. 기존 Julie CPA Manager 검토
        4. Gemini AI 재무 예측 (선택적)
        5. 기존 Julie CPA Auditor 최종 검증
        6. AI 통합 결과 종합
        """

        workflow_start = datetime.now().isoformat()
        workflow_results = {
            "workflow_type": "ai_enhanced_julie_cpa_phase_1",
            "client_id": client_data.get("client_id"),
            "analysis_type": analysis_type,
            "processing_phases": [],
            "ai_enhancements": [],
            "final_results": {},
            "trinity_score": 0.0,
            "processing_timestamp": workflow_start,
        }

        try:
            # Phase 1: 기존 Julie CPA Associate 분석
            print("📊 Phase 1.1: 기존 Julie CPA Associate 분석 시작")
            associate_result = await self._run_associate_analysis(
                client_data, tax_documents, analysis_type
            )
            workflow_results["processing_phases"].append(
                {
                    "phase": "associate_analysis",
                    "agent": "JulieAssociateAgent",
                    "status": "completed",
                    "trinity_score": associate_result.get("trinity_score", 0),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Phase 1: Claude AI 증강 세무 해석
            print("🧠 Phase 1.2: Claude AI 세무 해석 증강")
            claude_result = await self._run_claude_tax_analysis(
                client_data, tax_documents, analysis_type, claude_client
            )
            workflow_results["processing_phases"].append(
                {
                    "phase": "claude_ai_enhancement",
                    "agent": "ClaudeTaxAssistant",
                    "status": "completed",
                    "trinity_score": claude_result.get("trinity_score", 0),
                    "confidence": claude_result.get("confidence_level", 0),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            workflow_results["ai_enhancements"].append(
                {
                    "type": "claude_tax_interpretation",
                    "insights": len(
                        claude_result.get("client_analysis", {}).get("key_insights", [])
                    ),
                    "recommendations": len(claude_result.get("ai_recommendations", [])),
                }
            )

            # Phase 1: 기존 Julie CPA Manager 검토 (AI 분석 포함)
            print("⚖️ Phase 1.3: Julie CPA Manager 검토 (AI 증강)")
            manager_result = await self._run_manager_review_with_ai(
                associate_result, claude_result, client_data
            )
            workflow_results["processing_phases"].append(
                {
                    "phase": "manager_review_ai_enhanced",
                    "agent": "JulieManagerAgent",
                    "status": "completed",
                    "gate_decision": manager_result.get("gate_decision"),
                    "trinity_score": manager_result.get("trinity_score", 0),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Phase 1: Gemini AI 재무 예측 (선택적)
            gemini_result = None
            if enable_predictions and manager_result.get("gate_decision") == "AUTO_RUN":
                print("🔮 Phase 1.4: Gemini AI 재무 예측")
                gemini_result = await self._run_gemini_prediction(
                    client_data, associate_result, gemini_client
                )
                workflow_results["processing_phases"].append(
                    {
                        "phase": "gemini_financial_prediction",
                        "agent": "GeminiFinancialPredictor",
                        "status": "completed",
                        "trinity_score": gemini_result.get("trinity_score", 0),
                        "prediction_horizon": gemini_result.get("prediction_horizon", 0),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                workflow_results["ai_enhancements"].append(
                    {
                        "type": "gemini_financial_prediction",
                        "scenarios": len(gemini_result.get("risk_scenarios", [])),
                        "recommendations": len(gemini_result.get("strategic_recommendations", [])),
                    }
                )

            # Phase 1: 기존 Julie CPA Auditor 최종 검증 (AI 결과 포함)
            print("🎯 Phase 1.5: Julie CPA Auditor 최종 검증")
            auditor_result = await self._run_auditor_final_review(
                associate_result, manager_result, claude_result, gemini_result
            )
            workflow_results["processing_phases"].append(
                {
                    "phase": "auditor_final_review",
                    "agent": "JulieAuditorAgent",
                    "status": "completed",
                    "certification_status": auditor_result.get("certification_status"),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Phase 1: AI 통합 결과 종합
            print("🎯 Phase 1.6: AI 통합 결과 종합")
            final_results = self._synthesize_ai_enhanced_results(
                associate_result, claude_result, manager_result, gemini_result, auditor_result
            )

            workflow_results["final_results"] = final_results
            workflow_results["trinity_score"] = final_results.get("overall_trinity_score", 0)
            workflow_results["status"] = "completed"
            workflow_results["completion_timestamp"] = datetime.now().isoformat()

            print("✅ AI 증강 Julie CPA 워크플로우 완료")
            print(f"🎖️ 최종 Trinity Score: {workflow_results['trinity_score']:.3f}")

        except Exception as e:
            workflow_results["status"] = "failed"
            workflow_results["error"] = str(e)
            workflow_results["failure_timestamp"] = datetime.now().isoformat()
            print(f"❌ 워크플로우 실패: {e}")

        return workflow_results

    async def _run_associate_analysis(
        self, client_data: ClientData, tax_documents: list[TaxDocument], analysis_type: str
    ) -> AssociateResult:
        """기존 Julie CPA Associate 분석 실행"""
        # 분석 유형에 따른 적절한 변환
        julie_analysis_type = self._convert_analysis_type_for_julie(analysis_type)

        return await self.associate.analyze_tax_scenario(
            client_data, tax_documents, julie_analysis_type
        )

    async def _run_claude_tax_analysis(
        self,
        client_data: ClientData,
        tax_documents: list[TaxDocument],
        analysis_type: str,
        claude_client: Any = None,
    ) -> ClaudeResult:
        """Claude AI 세무 해석 실행"""
        return await self.claude_assistant.analyze_tax_scenario_with_ai(
            client_data, tax_documents, analysis_type, claude_client
        )

    async def _run_manager_review_with_ai(
        self,
        associate_result: AssociateResult,
        claude_result: ClaudeResult,
        client_data: ClientData,
    ) -> ManagerResult:
        """AI 증강 Julie CPA Manager 검토"""

        # AI 분석 결과를 Manager 검토에 통합
        enhanced_draft = self._merge_ai_into_draft_analysis(
            associate_result["draft_analysis"], claude_result
        )

        # 기존 Manager 로직 사용하되 AI 강화된 데이터로
        return await self.manager.review_associate_draft(
            enhanced_draft,
            associate_result["evidence_links"] + claude_result.get("evidence_links", []),
            {
                "objective": "ai_enhanced_tax_optimization",
                "ai_confidence": claude_result.get("trinity_score", 0.8),
                "mathematical_validation": claude_result.get("mathematical_validation", {}),
            },
        )

    async def _run_gemini_prediction(
        self,
        client_data: ClientData,
        associate_result: AssociateResult,
        gemini_client: Any = None,
    ) -> GeminiResult | None:
        """Gemini AI 재무 예측 실행"""

        # 과거 데이터 구성 (Associate 결과 활용)
        historical_data = self._extract_historical_data_from_associate(associate_result)

        # 예측 유형 결정
        prediction_type = (
            "retirement_planning" if client_data.get("current_age", 35) > 30 else "tax_optimization"
        )

        return await self.gemini_predictor.predict_financial_scenarios(
            client_data, historical_data, prediction_type, gemini_client
        )

    async def _run_auditor_final_review(
        self,
        associate_result: AssociateResult,
        manager_result: ManagerResult,
        claude_result: ClaudeResult,
        gemini_result: GeminiResult | None = None,
    ) -> dict[str, Any]:
        """AI 증강 Julie CPA Auditor 최종 검증"""

        # AI 결과를 Auditor 검토에 통합
        enhanced_associate_draft = self._merge_ai_into_draft_analysis(
            associate_result["draft_analysis"], claude_result
        )

        enhanced_manager_result = self._enhance_manager_result_with_ai(
            manager_result, claude_result, gemini_result
        )

        return await self.auditor.perform_final_audit(
            enhanced_associate_draft,
            enhanced_manager_result,
            {
                "evidence_bundle": associate_result["evidence_links"]
                + claude_result.get("evidence_links", []),
                "ai_analysis_results": {
                    "claude_insights": claude_result.get("client_analysis", {}).get(
                        "key_insights", []
                    ),
                    "mathematical_validation": claude_result.get("mathematical_validation", {}),
                    "gemini_predictions": gemini_result.get("hybrid_prediction", {})
                    if gemini_result
                    else None,
                },
            },
        )

    def _synthesize_ai_enhanced_results(
        self,
        associate_result: AssociateResult,
        claude_result: ClaudeResult,
        manager_result: ManagerResult,
        gemini_result: GeminiResult | None,
        auditor_result: dict[str, Any],
    ) -> FinalResults:
        """AI 증강 결과를 종합하여 최종 출력 생성"""

        # Trinity Score 가중 평균 계산
        trinity_scores = {
            "associate": associate_result.get("trinity_score", 0),
            "claude": claude_result.get("trinity_score", 0),
            "manager": manager_result.get("trinity_score", 0),
            "gemini": gemini_result.get("trinity_score", 0) if gemini_result else 0,
            "auditor": 0.95 if auditor_result.get("certification_status") == "CERTIFIED" else 0.8,
        }

        # AI 증강 가중치 적용
        weights = {
            "associate": 0.15,  # 기존 분석
            "claude": 0.35,  # AI 세무 해석 (최고 가중치)
            "manager": 0.20,  # 검토 및 전략
            "gemini": 0.20,  # 예측 분석
            "auditor": 0.10,  # 최종 검증
        }

        overall_trinity_score = sum(
            score * weights[agent] for agent, score in trinity_scores.items()
        )

        # AI 증강 인사이트 통합
        all_insights = []
        all_insights.extend(associate_result.get("draft_analysis", {}).get("assumptions", []))
        all_insights.extend(claude_result.get("client_analysis", {}).get("key_insights", []))
        if gemini_result:
            all_insights.extend(
                [
                    f"예측 분석: {scenario['description']}"
                    for scenario in gemini_result.get("risk_scenarios", [])[:2]  # 상위 2개만
                ]
            )

        # 전략적 추천사항 통합
        all_recommendations = []
        all_recommendations.extend(claude_result.get("ai_recommendations", []))
        if gemini_result:
            all_recommendations.extend(gemini_result.get("strategic_recommendations", []))
        all_recommendations.extend(manager_result.get("strategic_recommendations", []))

        return {
            "overall_trinity_score": round(overall_trinity_score, 3),
            "individual_scores": trinity_scores,
            "key_insights": list(set(all_insights)),  # 중복 제거
            "strategic_recommendations": list(set(all_recommendations)),  # 중복 제거
            "certification_status": auditor_result.get("certification_status"),
            "compliance_status": claude_result.get("client_analysis", {})
            .get("compliance", {})
            .get("status"),
            "mathematical_validation": claude_result.get("mathematical_validation", {}),
            "prediction_summary": self._summarize_predictions(gemini_result)
            if gemini_result
            else None,
            "processing_metadata": {
                "phase": "phase_1_ai_enhanced",
                "agents_used": [
                    "JulieAssociateAgent",
                    "ClaudeTaxAssistant",
                    "JulieManagerAgent",
                    "GeminiFinancialPredictor",
                    "JulieAuditorAgent",
                ],
                "ai_enhancements": [
                    "claude_tax_interpretation",
                    "mathematical_validation",
                    "financial_prediction",
                ],
                "confidence_level": "high" if overall_trinity_score >= 0.85 else "medium",
            },
        }

    def _convert_analysis_type_for_julie(self, analysis_type: str) -> str:
        """AI 분석 유형을 기존 Julie CPA 호환 형식으로 변환"""
        type_mapping = {
            "comprehensive": "standard_deduction",
            "tax_optimization": "standard_deduction",
            "roth_conversion": "roth_conversion",
            "retirement_planning": "standard_deduction",
        }
        return type_mapping.get(analysis_type, "standard_deduction")

    def _merge_ai_into_draft_analysis(
        self, original_draft: DraftAnalysis, claude_result: ClaudeResult
    ) -> DraftAnalysis:
        """AI 분석 결과를 기존 draft에 통합"""
        enhanced_draft = original_draft.copy()

        # Claude 인사이트 추가
        claude_insights = claude_result.get("client_analysis", {}).get("key_insights", [])
        enhanced_draft["ai_insights"] = claude_insights

        # 수학적 검증 결과 추가
        math_validation = claude_result.get("mathematical_validation", {})
        enhanced_draft["mathematical_validation"] = math_validation

        # Trinity Score 향상 반영
        ai_trinity = claude_result.get("trinity_score", 0)
        original_trinity = original_draft.get("confidence_level", 0.7)
        enhanced_draft["enhanced_confidence"] = (original_trinity + ai_trinity) / 2

        return enhanced_draft

    def _enhance_manager_result_with_ai(
        self,
        manager_result: ManagerResult,
        claude_result: ClaudeResult,
        gemini_result: GeminiResult | None = None,
    ) -> ManagerResult:
        """Manager 결과를 AI 분석으로 강화"""
        enhanced_result = manager_result.copy()

        # AI 기반 전략 추천 추가
        ai_recommendations = claude_result.get("ai_recommendations", [])
        existing_recommendations = enhanced_result.get("strategic_recommendations", [])
        enhanced_result["strategic_recommendations"] = list(
            set(existing_recommendations + ai_recommendations)
        )

        # 예측 분석이 있는 경우 통합
        if gemini_result:
            prediction_summary = self._summarize_predictions(gemini_result)
            enhanced_result["prediction_context"] = prediction_summary

        return enhanced_result

    def _extract_historical_data_from_associate(
        self, associate_result: AssociateResult
    ) -> list[HistoricalDataPoint]:
        """Associate 결과에서 과거 데이터 추출"""
        # 실제 구현에서는 Associate의 계산 결과를 기반으로 과거 데이터 구성
        # Phase 1에서는 모의 데이터 생성
        return [
            {"year": 2021, "income": 65000, "expenses": 45000, "investments": 150000},
            {"year": 2022, "income": 68000, "expenses": 47000, "investments": 165000},
            {"year": 2023, "income": 72000, "expenses": 49000, "investments": 180000},
            {"year": 2024, "income": 75000, "expenses": 51000, "investments": 195000},
        ]

    def _summarize_predictions(self, gemini_result: GeminiResult) -> PredictionSummary:
        """Gemini 예측 결과를 요약"""
        hybrid = gemini_result.get("hybrid_prediction", {})

        return {
            "prediction_horizon": gemini_result.get("prediction_horizon", 5),
            "expected_growth": hybrid.get("integrated_forecast_revenues", [])[-1]
            if hybrid.get("integrated_forecast_revenues")
            else 0,
            "risk_scenarios_count": len(gemini_result.get("risk_scenarios", [])),
            "confidence_level": gemini_result.get("confidence_assessment", {}).get(
                "overall_confidence", 0
            ),
        }


# Phase 1: AI 증강 Julie CPA 워크플로우 편의 함수
async def process_ai_enhanced_julie_cpa_workflow(
    client_data: ClientData,
    tax_documents: list[TaxDocument],
    analysis_type: str = "comprehensive",
    enable_predictions: bool = True,
) -> WorkflowResult:
    """
    AI 증강 Julie CPA 워크플로우 실행 편의 함수

    Phase 1: Claude + Gemini AI 완전 통합 인터페이스
    """
    workflow = AIEnhancedJulieCPAWorkflow()
    return await workflow.process_ai_enhanced_workflow(
        client_data, tax_documents, analysis_type, enable_predictions
    )
