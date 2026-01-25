from __future__ import annotations

import json
import re
from typing import Any

from AFO.domain.metrics.trinity import calculate_trinity

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""
MCP Tool Trinity Score Evaluator
MCP Tool 실행 결과를 분석하여 동적 眞善美孝永 점수를 계산하는 평가기

眞善美孝永 5기둥 철학 기반 실행 결과 평가:
- 眞 (Truth): 실행 성공, 검증 가능한 결과
- 善 (Goodness): 안전성, 리스크 없음
- 美 (Beauty): 결과의 구조화, 명확성
- 孝 (Serenity): 마찰 없음, 자동화 가능
- 永 (Eternity): 영속성, 재사용 가능성
"""


class MCPToolTrinityEvaluator:
    """
    MCP Tool 실행 결과를 분석하여 동적 Trinity Score를 계산하는 평가기

    실행 결과의 특성을 분석하여 眞善美孝永 5기둥 점수를 동적으로 계산합니다.
    """

    @staticmethod
    def evaluate_execution_result(
        tool_name: str,
        execution_result: str,
        execution_time_ms: float | None = None,
        is_error: bool = False,
        base_philosophy_scores: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        """
        MCP Tool 실행 결과를 분석하여 Trinity Score 계산

        Args:
            tool_name: 실행된 MCP Tool 이름
            execution_result: 실행 결과 텍스트
            execution_time_ms: 실행 시간 (밀리초)
            is_error: 에러 발생 여부
            base_philosophy_scores: 기본 철학 점수 (정적 점수, 선택적)

        Returns:
            Trinity Score 계산 결과 (眞善美孝永 5기둥 + 총점)
        """
        # 기본 점수 초기화 (정적 점수가 있으면 사용, 없으면 중간값)
        if base_philosophy_scores:
            truth_base = base_philosophy_scores.get("truth", 85) / 100.0
            goodness_base = base_philosophy_scores.get("goodness", 80) / 100.0
            beauty_base = base_philosophy_scores.get("beauty", 75) / 100.0
            serenity_base = base_philosophy_scores.get("serenity", 90) / 100.0
        else:
            truth_base = 0.85
            goodness_base = 0.80
            beauty_base = 0.75
            serenity_base = 0.90

        # 眞 (Truth): 실행 성공 여부, 검증 가능한 결과
        truth_score = MCPToolTrinityEvaluator._evaluate_truth(execution_result, is_error, tool_name)
        truth_final = min(1.0, truth_base * 0.7 + truth_score * 0.3)

        # 善 (Goodness): 안전성, 리스크 없음
        goodness_score = MCPToolTrinityEvaluator._evaluate_goodness(
            execution_result, is_error, tool_name
        )
        goodness_final = min(1.0, goodness_base * 0.7 + goodness_score * 0.3)

        # 美 (Beauty): 결과의 구조화, 명확성
        beauty_score = MCPToolTrinityEvaluator._evaluate_beauty(execution_result, tool_name)
        beauty_final = min(1.0, beauty_base * 0.7 + beauty_score * 0.3)

        # 孝 (Serenity): 마찰 없음, 자동화 가능
        serenity_score = MCPToolTrinityEvaluator._evaluate_serenity(
            execution_result, execution_time_ms, is_error, tool_name
        )
        serenity_final = min(1.0, serenity_base * 0.7 + serenity_score * 0.3)

        # 永 (Eternity): 영속성, 재사용 가능성
        eternity_score = MCPToolTrinityEvaluator._evaluate_eternity(execution_result, tool_name)
        eternity_final = min(1.0, eternity_score)

        # Trinity Metrics 계산 (SSOT 가중치 적용)
        trinity_metrics = calculate_trinity(
            truth=truth_final,
            goodness=goodness_final,
            beauty=beauty_final,
            filial_serenity=serenity_final,
            eternity=eternity_final,
            from_100_scale=False,
        )

        return {
            "tool_name": tool_name,
            "trinity_scores": {
                "truth": round(truth_final, 4),
                "goodness": round(goodness_final, 4),
                "beauty": round(beauty_final, 4),
                "filial_serenity": round(serenity_final, 4),
                "eternity": round(eternity_final, 4),
            },
            "trinity_metrics": trinity_metrics.to_dict(),
            "execution_metadata": {
                "execution_time_ms": execution_time_ms,
                "is_error": is_error,
                "result_length": len(execution_result) if execution_result else 0,
            },
        }

    @staticmethod
    def _evaluate_truth(result: str, is_error: bool, _tool_name: str) -> float:
        """
        眞 (Truth) 평가: 실행 성공, 검증 가능한 결과

        - 성공: 1.0
        - 에러: 0.3
        - 검증 가능한 구조 (JSON, 숫자 등): +0.2
        """
        if is_error or "Error" in result or "error" in result.lower():
            return 0.3

        score = 1.0

        # 검증 가능한 구조화된 결과
        if MCPToolTrinityEvaluator._is_structured_result(result):
            score = min(1.0, score + 0.2)

        # 성공 메시지 확인
        if "Success" in result or "success" in result.lower():
            score = min(1.0, score + 0.1)

        return score

    @staticmethod
    def _evaluate_goodness(result: str, is_error: bool, _tool_name: str) -> float:
        """
        善 (Goodness) 평가: 안전성, 리스크 없음

        - 에러 없음: 1.0
        - 위험한 명령어 (rm, delete 등): -0.5
        - 예외 처리 메시지: +0.1
        """
        if is_error:
            return 0.4

        score = 1.0

        # 위험한 명령어 감지
        dangerous_patterns = [
            r"\brm\s+-rf",
            r"\bdelete\b",
            r"\bdrop\b",
            r"\btruncate\b",
            r"\bformat\b",
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, result, re.IGNORECASE):
                score = max(0.5, score - 0.5)
                break

        # 예외 처리 메시지 (안전한 실패)
        if "Exception" in result or "exception" in result.lower():
            score = min(1.0, score + 0.1)

        return score

    @staticmethod
    def _evaluate_beauty(result: str, _tool_name: str) -> float:
        """
        美 (Beauty) 평가: 결과의 구조화, 명확성

        - JSON 구조: 1.0
        - 구조화된 텍스트: 0.8
        - 단순 텍스트: 0.6
        - 너무 길거나 복잡: -0.2
        """
        if not result:
            return 0.5

        # JSON 구조 확인
        if MCPToolTrinityEvaluator._is_json(result):
            return 1.0

        # 구조화된 텍스트 (리스트, 테이블 등)
        if MCPToolTrinityEvaluator._is_structured_text(result):
            return 0.8

        # 단순 텍스트
        score = 0.6

        # 너무 길거나 복잡한 결과는 감점
        if len(result) > 10000:
            score = max(0.4, score - 0.2)

        return score

    @staticmethod
    def _evaluate_serenity(
        result: str, execution_time_ms: float | None, is_error: bool, _tool_name: str
    ) -> float:
        """
        孝 (Serenity) 평가: 마찰 없음, 자동화 가능

        - 빠른 실행 (< 1초): 1.0
        - 중간 실행 (1-5초): 0.8
        - 느린 실행 (> 5초): 0.6
        - 에러: 0.3
        """
        if is_error:
            return 0.3

        if execution_time_ms is None:
            # 실행 시간 정보가 없으면 결과 길이로 추정
            if len(result) < 100:
                return 0.9
            elif len(result) < 1000:
                return 0.7
            else:
                return 0.5

        if execution_time_ms < 1000:
            return 1.0
        elif execution_time_ms < 5000:
            return 0.8
        else:
            return 0.6

    @staticmethod
    def _evaluate_eternity(_result: str, tool_name: str) -> float:
        """
        永 (Eternity) 평가: 영속성, 재사용 가능성

        - 파일 쓰기 작업: 1.0
        - 읽기 작업: 0.8
        - 쿼리/조회: 0.7
        - 일회성 실행: 0.5
        """
        # 파일 관련 작업
        if "write" in tool_name.lower() or "save" in tool_name.lower():
            return 1.0
        elif "read" in tool_name.lower() or "get" in tool_name.lower():
            return 0.8
        elif "query" in tool_name.lower() or "search" in tool_name.lower():
            return 0.7
        else:
            return 0.5

    @staticmethod
    def _is_structured_result(result: str) -> bool:
        """결과가 구조화되어 있는지 확인"""
        return MCPToolTrinityEvaluator._is_json(
            result
        ) or MCPToolTrinityEvaluator._is_structured_text(result)

    @staticmethod
    def _is_json(result: str) -> bool:
        """결과가 JSON 형식인지 확인"""
        try:
            json.loads(result)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    @staticmethod
    def _is_structured_text(result: str) -> bool:
        """결과가 구조화된 텍스트인지 확인 (리스트, 테이블 등)"""
        # 리스트 패턴 (줄바꿈으로 구분된 항목들)
        lines = result.strip().split("\n")
        if len(lines) > 3:
            # 대부분의 줄이 비슷한 패턴을 가지는지 확인
            pattern_count = 0
            for line in lines[:10]:  # 처음 10줄만 확인
                if re.match(r"^\s*[-*•]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
                    pattern_count += 1
            if pattern_count >= 3:
                return True

        # 테이블 패턴 (|로 구분된 열)
        return bool("|" in result and result.count("|") >= 3)


# 싱글톤 인스턴스
mcp_tool_trinity_evaluator = MCPToolTrinityEvaluator()
