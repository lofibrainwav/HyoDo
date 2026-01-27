from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import Any

# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
# mypy: ignore-errors
"""OpenAI Codex CLI Wrapper
형님 정기구독제 Codex CLI 연동

CLI 기반으로 월 구독제 LLM 통합
"""


logger = logging.getLogger(__name__)


class CodexCLIWrapper:
    """OpenAI Codex CLI 연동
    형님 정기구독제 CLI 사용 (API 키 불필요)
    """

    def __init__(self) -> None:
        self.cli_path = "${HOME}/.nvm/versions/node/v24.11.1/bin/codex"
        self.available = self._check_availability()

        if self.available:
            logger.info("✅ Codex CLI Wrapper 초기화 완료 (정기구독 CLI 사용)")
        else:
            logger.warning("⚠️ Codex CLI 사용 불가 - codex 명령어 없음")

    def _check_availability(self) -> bool:
        """CLI 사용 가능 여부 확인"""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"📍 Codex CLI 버전: {version}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Codex CLI 확인 실패: {e}")
            return False

    async def generate(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Codex CLI로 텍스트 생성"""
        if not self.available:
            return {"error": "Codex CLI not available", "success": False}

        try:
            # Codex CLI 명령어 구성 - exec 서브명령어로 비대화식 실행
            cmd = [
                self.cli_path,
                "exec",  # 비대화식 실행 모드
                prompt,
            ]

            # 비동기로 subprocess 실행
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=kwargs.get("timeout", 120)
            )

            if process.returncode == 0:
                content = stdout.decode().strip()
                return {
                    "success": True,
                    "content": content,
                    "model": "codex-cli",
                    "finish_reason": "complete",
                }
            else:
                error_msg = stderr.decode().strip() or "Unknown error"
                logger.error(f"Codex CLI 오류: {error_msg}")
                return {"error": error_msg, "success": False}

        except TimeoutError:
            logger.error("Codex CLI 타임아웃")
            return {"error": "Timeout", "success": False}
        except Exception as e:
            logger.error(f"Codex CLI 예외: {e}")
            return {"error": str(e), "success": False}

    async def generate_with_context(
        self, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """대화 맥락을 포함한 생성"""
        # 메시지들을 하나의 프롬프트로 조합
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"[System Instructions]\n{content}\n")
            elif role == "user":
                prompt_parts.append(f"[User]\n{content}\n")
            elif role == "assistant":
                prompt_parts.append(f"[Assistant]\n{content}\n")

        combined_prompt = "\n".join(prompt_parts)
        return await self.generate(combined_prompt, **kwargs)

    async def close(self):
        """리소스 정리"""
        pass

    def is_available(self) -> bool:
        """CLI 사용 가능 여부"""
        return self.available


# 글로벌 인스턴스
codex_cli = CodexCLIWrapper()


if __name__ == "__main__":

    async def test_codex_cli():
        print("🤖 Codex CLI Wrapper 테스트")
        print("=" * 50)

        if not codex_cli.is_available():
            print("❌ Codex CLI 사용 불가")
            return

        test_prompt = "간단한 Python Fibonacci 함수를 작성해줘."
        print(f"🔍 테스트 프롬프트: {test_prompt}")

        result = await codex_cli.generate(test_prompt)

        if result.get("success"):
            print("✅ 성공!")
            print(f"📝 응답: {result['content'][:200]}...")
        else:
            print(f"❌ 실패: {result.get('error')}")

    asyncio.run(test_codex_cli())
