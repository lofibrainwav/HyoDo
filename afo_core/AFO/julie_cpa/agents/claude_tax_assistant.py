"""
Claude AI Tax Assistant - Phase 1 AI Enhancement

세금 해석 및 전략 추천을 위한 Claude LLM 통합 어시스턴트
Julie CPA Associate Agent의 AI 증강 버전
"""

import json
from datetime import datetime
from typing import Any

from AFO.mathematical_tools import CPAMathematicalTools

from .types import ClaudeResult, ClientData, TaxDocument


class ClaudeTaxAssistant:
    """
    Claude LLM 기반 세금 해석 AI 어시스턴트

    Phase 1: AI 증강 CPA 시스템의 핵심 컴포넌트
    기존 Julie CPA Associate Agent를 Claude로 증강
    """

    def __init__(self) -> None:
        self.math_tools = CPAMathematicalTools()
        self.confidence_threshold = 0.85
        self.max_claude_calls = 3

    async def analyze_tax_scenario_with_ai(
        self,
        client_data: ClientData,
        tax_documents: list[TaxDocument],
        analysis_type: str,
        claude_client: Any = None,  # Claude client injection for testing
    ) -> ClaudeResult:
        """
        Claude LLM을 활용한 지능적 세금 분석

        기존 Associate Agent의 기능을 AI로 증강:
        1. 세법 해석 및 적용
        2. 전략적 추천 생성
        3. 복잡한 시나리오 분석
        4. Trinity Score 기반 검증
        """

        # Phase 1: 기본 검증 (기존 Associate 로직 유지)
        if not self._validate_client_data(client_data):
            raise ValueError("Invalid client data provided")

        # 증거 수집 (수학적 도구 활용)
        evidence_links = self._collect_evidence_with_math(tax_documents)

        # Claude 기반 AI 분석
        ai_analysis = await self._perform_claude_tax_analysis(
            client_data, tax_documents, analysis_type, claude_client
        )

        # 수학적 검증 (CPA 도구 활용)
        mathematical_validation = self._validate_with_math_tools(
            ai_analysis, client_data, analysis_type
        )

        # Trinity Score 계산 (AI 정확성 포함)
        trinity_score = self._calculate_ai_trinity_score(
            ai_analysis, evidence_links, mathematical_validation
        )

        # AI 기반 전략 추천
        ai_recommendations = await self._generate_ai_recommendations(
            ai_analysis, client_data, analysis_type, claude_client
        )

        return {
            "analysis_type": "claude_enhanced",
            "client_analysis": ai_analysis,
            "mathematical_validation": mathematical_validation,
            "evidence_links": evidence_links,
            "ai_recommendations": ai_recommendations,
            "trinity_score": trinity_score,
            "confidence_level": trinity_score,  # AI 기반 신뢰도
            "processing_timestamp": datetime.now().isoformat(),
            "phase": "phase_1_claude_integration",
        }

    def _validate_client_data(self, client_data: dict[str, Any]) -> bool:
        """클라이언트 데이터 검증"""
        required_fields = ["client_id", "tax_year", "filing_status", "income"]
        return all(field in client_data for field in required_fields)

    def _collect_evidence_with_math(
        self, tax_documents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """수학적 도구를 활용한 증거 수집 및 검증"""
        evidence_links = []

        for doc in tax_documents:
            doc_type = doc.get("type", "unknown")
            evidence = {
                "type": doc_type,
                "reference": doc.get("reference", ""),
                "validation_status": "mathematically_validated",
                "mathematical_checks": [],
                "timestamp": datetime.now().isoformat(),
            }

            # 수학적 검증 적용
            if doc_type == "income_statement":
                # 재무 비율 검증
                try:
                    ratios = self.math_tools.calculate_financial_ratios(
                        doc.get("balance_sheet", {}), doc.get("income_statement", {})
                    )
                    evidence["mathematical_checks"].append(
                        {"type": "financial_ratios", "ratios": ratios, "status": "calculated"}
                    )
                except Exception as e:
                    evidence["mathematical_checks"].append(
                        {"type": "financial_ratios", "error": str(e), "status": "failed"}
                    )

            elif doc_type == "depreciation_schedule":
                # 감가상각 계산 검증
                try:
                    depr_calc = self.math_tools.calculate_depreciation_schedule(
                        doc.get("cost_basis", 0),
                        doc.get("salvage_value", 0),
                        doc.get("useful_life", 5),
                    )
                    evidence["mathematical_checks"].append(
                        {
                            "type": "depreciation_validation",
                            "calculation": depr_calc,
                            "status": "verified",
                        }
                    )
                except Exception as e:
                    evidence["mathematical_checks"].append(
                        {"type": "depreciation_validation", "error": str(e), "status": "failed"}
                    )

            evidence_links.append(evidence)

        return evidence_links

    async def _perform_claude_tax_analysis(
        self,
        client_data: dict[str, Any],
        tax_documents: list[dict[str, Any]],
        analysis_type: str,
        claude_client=None,
    ) -> dict[str, Any]:
        """
        Claude LLM을 활용한 세금 분석

        실제 Claude API 호출 대신 모의 응답 생성
        (프로덕션에서는 실제 Claude API 호출로 대체)
        """

        # Claude 프롬프트 구성
        prompt = self._build_claude_prompt(client_data, tax_documents, analysis_type)

        # Phase 1: 모의 Claude 응답 (실제 API 연동 전)
        mock_claude_response = self._generate_mock_claude_response(client_data, analysis_type)

        # AI 분석 결과 구조화
        ai_analysis = {
            "prompt_used": prompt,
            "claude_response": mock_claude_response,
            "analysis_summary": mock_claude_response.get("summary", ""),
            "key_insights": mock_claude_response.get("insights", []),
            "risk_assessment": mock_claude_response.get("risks", {}),
            "strategic_recommendations": mock_claude_response.get("recommendations", []),
            "compliance_check": mock_claude_response.get("compliance", {}),
            "confidence_score": mock_claude_response.get("confidence", 0.85),
        }

        return ai_analysis

    def _build_claude_prompt(
        self,
        client_data: dict[str, Any],
        tax_documents: list[dict[str, Any]],
        analysis_type: str,
    ) -> str:
        """Claude를 위한 분석 프롬프트 구성"""

        prompt = f"""
당신은 AFO 왕국의 최고 세무 전문가인 Julie CPA의 AI 어시스턴트입니다.

클라이언트 데이터:
{json.dumps(client_data, indent=2, ensure_ascii=False)}

세금 문서 요약:
{json.dumps([{"type": doc.get("type"), "key_data": doc.get("key_data")} for doc in tax_documents], indent=2, ensure_ascii=False)}

분석 유형: {analysis_type}

다음과 같은 포괄적인 세무 분석을 수행해주세요:

1. 세법 해석 및 적용
2. 잠재적 세금 절감 전략
3. 컴플라이언스 리스크 평가
4. 미래 세무 계획 추천
5. 수치적 근거 및 계산

응답은 다음 JSON 형식으로 제공해주세요:
{{
    "summary": "분석 요약",
    "insights": ["주요 인사이트 목록"],
    "risks": {{"high": [], "medium": [], "low": []}},
    "recommendations": ["전략적 추천사항"],
    "compliance": {{"status": "compliant/partially_compliant/non_compliant", "issues": []}},
    "confidence": 0.95
}}
"""

        return prompt

    def _generate_mock_claude_response(
        self, client_data: dict[str, Any], analysis_type: str
    ) -> dict[str, Any]:
        """
        Claude API 모의 응답 생성
        실제 Claude API 연동 전 테스트용
        """

        income = client_data.get("income", 0)
        filing_status = client_data.get("filing_status", "single")

        # 분석 유형별 모의 응답 생성
        if analysis_type == "tax_optimization":
            return {
                "summary": f"{filing_status} 신고자인 클라이언트의 종합 세금 최적화 분석 결과입니다.",
                "insights": [
                    f"현재 소득 ${income:,.0f}에 대한 효과적인 공제 전략 필요",
                    "Roth IRA 전환을 통한 장기 세금 절감 가능성 검토",
                    "의료비 및 교육비 공제 최적화 추천",
                ],
                "risks": {
                    "high": ["과도한 Roth 전환으로 인한 세금 부담 증가"],
                    "medium": ["공제 누락으로 인한 세금 납부 증가"],
                    "low": ["세법 변경에 따른 전략 수정 필요"],
                },
                "recommendations": [
                    "표준공제 대신 항목별 공제 검토",
                    "퇴직연금 기여금 최대화",
                    "자선 기부 전략 수립",
                ],
                "compliance": {
                    "status": "compliant",
                    "issues": [],
                },
                "confidence": 0.92,
            }

        elif analysis_type == "roth_conversion":
            return {
                "summary": f"Roth IRA 전환 전략 분석 - 현재 소득 ${income:,.0f} 기반",
                "insights": [
                    "전환 금액에 따른 세금 영향 분석 필요",
                    "5년 규칙 준수를 위한 전략 수립",
                    "전환 시기 최적화 검토",
                ],
                "risks": {
                    "high": ["전환 후 소득 증가로 인한 세율 상승"],
                    "medium": ["5년 규칙 위반으로 인한 벌금"],
                    "low": ["시장 변동성에 따른 투자 수익 변화"],
                },
                "recommendations": [
                    "연간 전환 한도 내에서 점진적 전환",
                    "세율이 낮은 연도 우선 전환",
                    "필요시 재전환(Reconversion) 전략 고려",
                ],
                "compliance": {
                    "status": "compliant",
                    "issues": [],
                },
                "confidence": 0.89,
            }

        else:
            return {
                "summary": f"일반 세무 분석 - {analysis_type} 유형",
                "insights": ["기본 세무 컴플라이언스 확인 필요"],
                "risks": {"high": [], "medium": [], "low": ["세법 준수 검토 필요"]},
                "recommendations": ["CPA 전문가 상담 권장"],
                "compliance": {"status": "unknown", "issues": ["추가 분석 필요"]},
                "confidence": 0.75,
            }

    def _validate_with_math_tools(
        self,
        ai_analysis: dict[str, Any],
        client_data: dict[str, Any],
        analysis_type: str,
    ) -> dict[str, Any]:
        """CPA 수학 도구를 활용한 AI 분석 검증"""

        validation_results = {
            "mathematical_checks": [],
            "accuracy_score": 0.0,
            "validation_timestamp": datetime.now().isoformat(),
        }

        try:
            # 세금 계산 검증
            if analysis_type in ["tax_optimization", "roth_conversion"]:
                tax_analysis = self.math_tools.optimize_tax_strategy(
                    client_data.get("income", 0),
                    client_data.get("deductions", []),
                    [(0, 0.10), (10000, 0.12), (40000, 0.22), (90000, 0.24)],  # 기본 세율
                )

                validation_results["mathematical_checks"].append(
                    {
                        "type": "tax_calculation_validation",
                        "ai_predicted_tax": ai_analysis.get("claude_response", {}).get(
                            "estimated_tax", 0
                        ),
                        "mathematical_calculation": tax_analysis,
                        "accuracy": 0.95,  # 모의 정확도
                        "status": "validated",
                    }
                )

            # 재무 비율 검증
            if "balance_sheet" in client_data:
                ratios = self.math_tools.calculate_financial_ratios(
                    client_data.get("balance_sheet", {}), client_data.get("income_statement", {})
                )

                validation_results["mathematical_checks"].append(
                    {
                        "type": "financial_ratios_validation",
                        "calculated_ratios": ratios,
                        "status": "validated",
                    }
                )

            # 종합 정확도 계산
            validation_results["accuracy_score"] = 0.93  # 모의 정확도

        except Exception as e:
            validation_results["mathematical_checks"].append(
                {"type": "error", "error": str(e), "status": "failed"}
            )
            validation_results["accuracy_score"] = 0.0

        return validation_results

    def _calculate_ai_trinity_score(
        self,
        ai_analysis: dict[str, Any],
        evidence_links: list[dict[str, Any]],
        mathematical_validation: dict[str, Any],
    ) -> float:
        """AI 증강 분석을 위한 Trinity Score 계산"""

        # AI 분석 품질 평가
        ai_confidence = ai_analysis.get("claude_response", {}).get("confidence", 0.8)
        ai_completeness = len(ai_analysis.get("key_insights", [])) / 5.0  # 5개 이상 인사이트 기대

        # 증거 품질 평가
        evidence_quality = min(len(evidence_links) * 0.2, 1.0)

        # 수학적 검증 품질 평가
        math_accuracy = mathematical_validation.get("accuracy_score", 0.0)

        # Trinity Score 계산
        truth_score = (ai_confidence + math_accuracy) / 2.0  # 眞: AI + 수학 정확성
        goodness_score = min(ai_confidence * 0.9, 0.95)  # 善: 윤리적 정확성
        beauty_score = min(ai_completeness * 0.8, 0.9)  # 美: 분석 완결성
        serenity_score = evidence_quality  # 孝: 증거 기반 안정성
        eternity_score = 0.85  # 永: AI 시스템 지속성

        # AFO Kingdom Trinity Score 공식
        trinity_score = (
            truth_score * 0.35
            + goodness_score * 0.35
            + beauty_score * 0.20
            + serenity_score * 0.08
            + eternity_score * 0.02
        )

        return round(trinity_score, 3)

    async def _generate_ai_recommendations(
        self,
        ai_analysis: dict[str, Any],
        client_data: dict[str, Any],
        analysis_type: str,
        claude_client=None,
    ) -> list[str]:
        """AI 기반 전략적 추천사항 생성"""

        base_recommendations = ai_analysis.get("claude_response", {}).get("recommendations", [])

        # CPA 수학 도구 기반 추가 추천
        enhanced_recommendations = base_recommendations.copy()

        try:
            # 세금 최적화 추천 강화
            if analysis_type == "tax_optimization":
                tax_analysis = self.math_tools.optimize_tax_strategy(
                    client_data.get("income", 0),
                    client_data.get("deductions", [12500]),  # 기본 공제 가정
                    [(0, 0.10), (10000, 0.12), (40000, 0.22), (90000, 0.24)],
                )

                best_scenario = max(
                    tax_analysis.get("optimization_scenarios", []),
                    key=lambda x: x.get("savings", 0),
                    default={},
                )

                if best_scenario:
                    enhanced_recommendations.append(
                        f"수학적 최적화: 추가 공제 ${best_scenario['additional_deduction']}로 "
                        f"${best_scenario['savings']} 절세 가능"
                    )

        except Exception:
            # 수학적 도구 실패 시 AI 추천만 사용
            pass

        return enhanced_recommendations

    async def get_tax_strategy_explanation(
        self,
        strategy_name: str,
        client_context: dict[str, Any],
        claude_client=None,
    ) -> str:
        """
        특정 세금 전략에 대한 Claude 기반 상세 설명
        교육 및 의사결정 지원용
        """

        f"""
세금 전략 "{strategy_name}"에 대해 자세히 설명해주세요:

클라이언트 상황:
{json.dumps(client_context, indent=2, ensure_ascii=False)}

다음 항목을 포함해서 설명해주세요:
1. 전략의 기본 개념
2. 적용 가능한 상황
3. 잠재적 이점과 리스크
4. 실행 방법
5. 모니터링 포인트

일반인이 이해하기 쉽게 설명해주세요.
"""

        # Phase 1: 모의 응답
        explanations = {
            "roth_conversion": """
Roth IRA 전환 전략은 전통 IRA의 세금 부담을 미래로 이연시키는 방법입니다.

**기본 개념**: 기존의 세전 달러로 납입한 전통 IRA를 세후 달러로 전환하여,
미래 인출 시 세금을 면제받는 전략입니다.

**적용 상황**:
- 현재 소득이 낮아 세율이 유리한 경우
- 은퇴 후 세율이 상승할 것으로 예상되는 경우
- 상속세 최소화를 원하는 경우

**이점**:
- 미래 세금 부담 완전 면제
- 자녀/상속인에게 세금 부담 전가 방지
- 투자 수익에 대한 세금 절감

**리스크**:
- 전환 시점의 세율 적용
- 5년 규칙 준수 필요
- 전환 금액에 대한 즉시 과세

**실행 방법**:
1. 현재 소득과 세율 분석
2. 전환 가능 금액 계산
3. 단계적 전환 계획 수립
4. 세무 전문가와 실행

**모니터링**: 매년 세율 변화와 시장 상황 모니터링
            """,
        }

        return explanations.get(strategy_name, f"{strategy_name} 전략에 대한 설명을 준비 중입니다.")
