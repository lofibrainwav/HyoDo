from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class TaskClassifier:
    """Task Classification & Routing Decisions"""

    def __init__(self, scholars_config: dict) -> None:
        self.scholars_config = scholars_config

    def classify_task(self, query: str) -> str:
        """쿼리를 기반으로 태스크 타입 분류"""
        query_lower = query.lower()

        # 구현 관련 (Implementation)
        if any(
            word in query_lower
            for word in [
                "implement",
                "create",
                "build",
                "develop",
                "write code",
                "코딩",
                "구현",
            ]
        ):
            return "implementation"

        # 논리 검증 관련 (Logic Verification)
        if any(
            word in query_lower
            for word in [
                "verify",
                "check",
                "validate",
                "test",
                "논리",
                "검증",
                "리팩토링",
            ]
        ):
            return "logic_verification"

        # 전략 계획 관련 (Strategy Checking)
        if any(
            word in query_lower
            for word in [
                "strategy",
                "plan",
                "design",
                "architecture",
                "철학",
                "전략",
                "큰 그림",
            ]
        ):
            return "strategy_planning"

        # 코드 리뷰 관련
        if any(word in query_lower for word in ["review", "analyze", "audit", "코드리뷰", "분석"]):
            return "code_review"

        # 디버깅 관련
        if any(word in query_lower for word in ["debug", "fix", "error", "bug", "디버깅", "수정"]):
            return "debugging"

        # 문서화 관련
        if any(word in query_lower for word in ["document", "docs", "readme", "문서", "설명"]):
            return "documentation"

        # 보안 관련
        if any(word in query_lower for word in ["security", "auth", "encrypt", "보안", "인증"]):
            return "security_analysis"

        return "general"

    def get_scholar_for_task(self, task_type: str) -> str:
        """태스크 타입에 따른 학자 선택 (SSOT 기반)"""
        task_scholar_map = {
            "implementation": "codex",  # 방통 - 구현·실행·프로토타이핑
            "logic_verification": "claude",  # 자룡 - 논리 검증·리팩터링
            "strategy_planning": "gemini",  # 육손 - 전략·철학·큰 그림
            "code_review": "claude",  # 자룡 - 논리 검증
            "debugging": "codex",  # 방통 - 구현
            "documentation": "ollama",  # 영덕 - 로컬 설명
            "security_analysis": "ollama",  # 영덕 - 보안
            "general": "ollama",  # 영덕 - 기본
        }

        scholar_key = task_scholar_map.get(task_type, "ollama")
        scholar_name = (
            self.scholars_config.get(scholar_key, {}).get("codename", "Unknown")
            if self.scholars_config
            else "Unknown"
        )

        logger.info(f"🧭 Task '{task_type}' → Scholar '{scholar_key}' ({scholar_name})")
        return scholar_key
