from __future__ import annotations

import logging
from typing import Any

import openai

from AFO.config.settings import get_settings
from AFO.domain.metrics.trinity import TrinityInputs, TrinityMetrics

# Trinity Score: 95.0 (Established by Chancellor)
"""
Codex API Wrapper for AFO Kingdom

방통 (Pangtong) - 구현·실행·프로토타이핑 담당
OpenAI Codex 기반 코드 생성 및 프로토타이핑 래퍼
"""


logger = logging.getLogger(__name__)


class CodexAPIWrapper:
    """
    Codex API Wrapper (방통 - Pangtong)

    OpenAI Codex를 통한 코드 생성 및 프로토타이핑
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Codex API Wrapper 초기화"""
        self.api_key = api_key
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """OpenAI API 키 가용성 확인"""
        return bool(self.api_key)

    def is_available(self) -> bool:
        """Codex 서비스 가용성 반환"""
        return self.available

    async def generate(
        self,
        prompt: str,
        model: str = "code-davinci-002",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """
        Codex 모델 호출 (방통)

        Args:
            prompt: 입력 프롬프트 (코드 생성 요청)
            model: 사용할 모델 (기본: code-davinci-002)
            max_tokens: 최대 토큰 수
            temperature: 온도 설정 (코드 생성에는 낮게)
            **kwargs: 추가 파라미터

        Returns:
            생성된 코드 텍스트
        """
        try:
            # OpenAI 클라이언트 설정
            client = openai.AsyncOpenAI(api_key=self.api_key)

            # Codex 모델 호출
            response = await client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            return response.choices[0].text.strip()

        except Exception as e:
            logger.error(f"❌ Codex API 호출 실패: {e}")
            return f"방통 호출 실패: {e}"

    async def generate_with_context(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        컨텍스트를 포함한 Codex 호출 (SSOT 준수)

        Args:
            prompt: 입력 프롬프트
            context: 추가 컨텍스트 (언어, 프레임워크 등)
            **kwargs: 추가 파라미터

        Returns:
            코드 생성 결과 및 메타데이터
        """
        context = context or {}

        # 컨텍스트 기반 프롬프트 강화
        language = context.get("language", "python")
        framework = context.get("framework", "")
        task_type = context.get("task_type", "implementation")

        enhanced_prompt = f"""
Generate {language} code for: {prompt}

Requirements:
- Language: {language}
{f"- Framework: {framework}" if framework else ""}
- Task Type: {task_type}
- Focus on clean, maintainable code
- Include proper error handling
- Add helpful comments

Code:
"""

        response = await self.generate(enhanced_prompt, **{**context, **kwargs})

        # Trinity Score 계산 (방통의 철학 점수 기반)
        trinity_inputs = TrinityInputs(
            truth=0.95,  # 방통의 기본 Truth 점수
            goodness=0.90,  # 방통의 기본 Goodness 점수
            beauty=0.92,  # 방통의 기본 Beauty 점수
            filial_serenity=0.88,  # 방통의 기본 Serenity 점수
        )
        trinity_score = TrinityMetrics.from_inputs(trinity_inputs, eternity=1.0)

        return {
            "response": response,
            "model": "code-davinci-002",
            "provider": "openai",
            "language": language,
            "framework": framework,
            "task_type": task_type,
            "trinity_score": trinity_score.to_dict(),
            "scholar_codename": "방통",
            "success": True,
        }

    async def generate_code(
        self,
        description: str,
        language: str = "python",
        framework: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        코드 생성 헬퍼 함수

        Args:
            description: 코드 설명
            language: 프로그래밍 언어
            framework: 프레임워크
            **kwargs: 추가 파라미터

        Returns:
            생성된 코드와 메타데이터
        """
        context = {
            "language": language,
            "framework": framework,
            "task_type": "code_generation",
        }

        return await self.generate_with_context(description, context, **kwargs)

    async def close(self) -> None:
        """리소스 정리"""
        pass  # OpenAI 클라이언트는 자동 정리됨


# 글로벌 인스턴스 (API 키가 설정된 경우에만)
try:
    settings = get_settings()
    codex_api = CodexAPIWrapper(api_key=settings.OPENAI_API_KEY)
except Exception:
    codex_api = CodexAPIWrapper(api_key=None)
    logger.warning("⚠️ Codex API 키가 설정되지 않음")
