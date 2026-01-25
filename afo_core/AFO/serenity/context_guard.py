# Trinity Score: 95.0 (Established by Chancellor)
"""
Context Guard - Token Efficiency & Evidence Extraction Layer
사령관의 의도를 학자들에게 전달할 때, 불필요한 노이즈를 제거하고 핵심 증거(Evidence)만 추출하여
컨텍스트 윈도우를 최적화하는 미들웨어입니다.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class ContextGuard:
    def __init__(self, max_context_tokens: int = 4000) -> None:
        self.max_context_tokens = max_context_tokens
        self.evidence_registry: dict[str, str] = {}

    def extract_evidence(self, raw_content: str, focus_topic: str) -> str:
        """
        [Phase 50] 대용량 텍스트에서 주제와 관련된 핵심 증거만 추출.
        현재는 휴리스틱 기반이며, 추후 학자(류성룡)의 요약 엔진과 연동 예정.
        """
        lines = raw_content.split("\n")
        evidence = []

        # 주제와 관련된 라인 필터링 (간소화된 정찰 로직)
        keywords = focus_topic.lower().split()
        for line in lines:
            if any(kw in line.lower() for kw in keywords) or line.strip().startswith(
                ("#", "-", "*")
            ):
                evidence.append(line)

        # 너무 길 경우 상위 50줄로 제한
        summary = "\n".join(evidence[:50])
        return f"[EVIDENCE: {focus_topic}]\n{summary}\n[END OF EVIDENCE]"

    def load_hierarchical_context(self, current_path: str) -> str:
        """
        [Phase 50] 현재 디렉토리부터 루트까지 거슬러 올라가며 AGENTS.md를 수집.
        하위 디렉토리의 규칙이 상위 규칙보다 우선순위를 가짐.
        """
        contexts = []
        path = os.path.abspath(current_path)
        while path != "/":
            agent_file = os.path.join(path, "AGENTS.md")
            if os.path.exists(agent_file):
                with open(agent_file) as f:
                    contexts.append(f.read())

            # 한 단계 위로
            parent = os.path.dirname(path)
            if parent == path:
                break
            path = parent

        # 최신(하위) 정보가 먼저 오도록 취합
        return "\n\n---\n\n".join(contexts)

    def lean_context(
        self, system_prompt: str, user_prompt: str, history: list[dict[str, str]]
    ) -> dict[str, Any]:
        """
        [Phase 50] 전체 컨텍스트를 분석하여 토큰 효율성을 극대화한 메시지 묶음 생성.
        """
        # TODO: 실제 토큰 계산 로직 (tiktoken 등) 연동
        # 지금은 문자열 길이 기반 근사치 사용
        total_len = len(system_prompt) + len(user_prompt) + sum(len(m["content"]) for m in history)

        if total_len > self.max_context_tokens * 4:  # 대략 1토큰=4자 기준
            logger.warning(f"Context too heavy ({total_len} chars). Triggering leaning...")
            # 히스토리 요약 또는 오래된 메시지 절삭 로직 발동
            history = history[-5:]  # 최근 5개만 유지

        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                *history,
                {"role": "user", "content": user_prompt},
            ],
            "leaned": total_len > self.max_context_tokens * 4,
        }


# 글로벌 인스턴스
context_guard = ContextGuard()
