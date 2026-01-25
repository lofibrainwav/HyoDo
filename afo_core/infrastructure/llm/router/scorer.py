from __future__ import annotations

from typing import Any

from AFO.domain.metrics.trinity import TrinityInputs, TrinityMetrics


class TrinityScorer:
    """Trinity Score Evaluator logic (moved from Router)"""

    @staticmethod
    def calculate_ssot_trinity_score(
        response: str, _scholar_key: str, scholar_config: dict[str, Any]
    ) -> TrinityMetrics:
        """SSOT 기반 Trinity Score 계산"""
        base_scores = scholar_config.get(
            "philosophy_scores",
            {"truth": 0.9, "goodness": 0.9, "beauty": 0.9, "serenity": 0.9},
        )

        # 응답 품질 기반 동적 조정
        quality_bonus = TrinityScorer.analyze_response_quality(response)

        # SSOT 준수 보너스 (API Wallet 사용)
        ssot_compliance_bonus = 0.1

        inputs = TrinityInputs(
            truth=min(
                1.0,
                base_scores["truth"] + quality_bonus["truth"] + ssot_compliance_bonus,
            ),
            goodness=min(
                1.0,
                base_scores["goodness"] + quality_bonus["goodness"] + ssot_compliance_bonus,
            ),
            beauty=min(
                1.0,
                base_scores["beauty"] + quality_bonus["beauty"] + ssot_compliance_bonus,
            ),
            filial_serenity=min(
                1.0,
                base_scores.get("serenity", 0.9)
                + quality_bonus["serenity"]
                + ssot_compliance_bonus,
            ),
        )

        # 영속성(eternity)은 SSOT 준수로 최대값
        return TrinityMetrics.from_inputs(inputs, eternity=1.0)

    @staticmethod
    def analyze_response_quality(response: str) -> dict[str, float]:
        """응답 품질 분석"""
        if not response:
            return {"truth": -0.2, "goodness": -0.2, "beauty": -0.2, "serenity": -0.2}

        quality_scores = {"truth": 0.0, "goodness": 0.0, "beauty": 0.0, "serenity": 0.0}

        # Truth: 기술적 정확성 (코드, 사실, 논리)
        if any(
            keyword in response.lower()
            for keyword in ["```", "function", "class", "import", "def "]
        ):
            quality_scores["truth"] += 0.1
        if len(response) > 100:  # 충분한 길이
            quality_scores["truth"] += 0.05

        # Goodness: 윤리적 고려 (안전, 보안, 최적화)
        if any(
            keyword in response.lower()
            for keyword in ["security", "safe", "optimize", "best practice"]
        ):
            quality_scores["goodness"] += 0.1

        # Beauty: 구조화, 가독성 (목록, 헤더, 정리)
        if any(keyword in response for keyword in ["•", "###", "- ", "1. ", "```"]):
            quality_scores["beauty"] += 0.1
        if "\n\n" in response:  # 단락 구분
            quality_scores["beauty"] += 0.05

        # Serenity: 평온함 (명확한 결론, 마찰 최소화)
        if any(
            keyword in response.lower()
            for keyword in ["summary", "conclusion", "recommend", "다음과 같이"]
        ):
            quality_scores["serenity"] += 0.1

        return quality_scores
