from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from typing import Any

# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
# mypy: ignore-errors
"""Claude CLI Wrapper
형님 정기구독제 Claude Code CLI 연동

CLI 기반으로 월 구독제 LLM 통합
"""


logger = logging.getLogger(__name__)

MAX_PROMPT_CHARS = int(os.getenv("AFO_CLAUDE_PROMPT_MAX_CHARS", "100000"))
TRUNCATION_NOTICE = "\n\n[... truncated to fit prompt budget ...]\n\n"


def _trim_prompt(prompt: str, max_chars: int = MAX_PROMPT_CHARS) -> str:
    if len(prompt) <= max_chars:
        return prompt
    head = prompt[: max_chars // 2]
    tail = prompt[-(max_chars // 2) :]
    return f"{head}{TRUNCATION_NOTICE}{tail}"


def _stdin_unsupported(error: str) -> bool:
    lowered = error.lower()
    return "prompt" in lowered or "usage:" in lowered or "expected" in lowered


class ClaudeCLIWrapper:
    """Claude Code CLI 연동
    형님 정기구독제 CLI 사용 (API 키 불필요)
    """

    def __init__(self) -> None:
        self.cli_path = "${HOME}/.local/bin/claude"
        self.available = self._check_availability()

        if self.available:
            logger.info("✅ Claude CLI Wrapper 초기화 완료 (정기구독 CLI 사용)")
        else:
            logger.warning("⚠️ Claude CLI 사용 불가 - claude 명령어 없음")

    def _check_availability(self) -> bool:
        """CLI 사용 가능 여부 확인"""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"📍 Claude CLI 버전: {version}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Claude CLI 확인 실패: {e}")
            return False

    async def generate(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Claude CLI로 텍스트 생성"""
        if not self.available:
            return {"error": "Claude CLI not available", "success": False}

        try:
            prompt = _trim_prompt(prompt)
            # --print 모드로 비대화식 출력
            cmd = [
                self.cli_path,
                "--print",  # 비대화식 출력
                "--output-format",
                "json",  # JSON 형식
                "--input-format",
                "text",
            ]

            # 비동기로 subprocess 실행
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(prompt.encode()),
                timeout=kwargs.get("timeout", 120),
            )

            if process.returncode == 0:
                try:
                    result = json.loads(stdout.decode())
                    return {
                        "success": True,
                        "content": result.get("result", result.get("text", stdout.decode())),
                        "model": "claude-code-cli",
                        "finish_reason": "complete",
                    }
                except json.JSONDecodeError:
                    # Plain text 응답
                    return {
                        "success": True,
                        "content": stdout.decode().strip(),
                        "model": "claude-code-cli",
                        "finish_reason": "complete",
                    }
            else:
                error_msg = stderr.decode().strip() or "Unknown error"
                if _stdin_unsupported(error_msg):
                    return await self._generate_with_arg(prompt, **kwargs)
                logger.error(f"Claude CLI 오류: {error_msg}")
                return {"error": error_msg, "success": False}

        except TimeoutError:
            logger.error("Claude CLI 타임아웃")
            return {"error": "Timeout", "success": False}
        except Exception as e:
            logger.error(f"Claude CLI 예외: {e}")
            return {"error": str(e), "success": False}

    async def _generate_with_arg(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Fallback for CLIs that require prompt as an argument."""
        cmd = [
            self.cli_path,
            "--print",
            "--output-format",
            "json",
            prompt,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=kwargs.get("timeout", 120)
        )

        if process.returncode == 0:
            try:
                result = json.loads(stdout.decode())
                return {
                    "success": True,
                    "content": result.get("result", result.get("text", stdout.decode())),
                    "model": "claude-code-cli",
                    "finish_reason": "complete",
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "content": stdout.decode().strip(),
                    "model": "claude-code-cli",
                    "finish_reason": "complete",
                }

        error_msg = stderr.decode().strip() or "Unknown error"
        logger.error(f"Claude CLI 오류: {error_msg}")
        return {"error": error_msg, "success": False}

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
claude_cli = ClaudeCLIWrapper()


if __name__ == "__main__":

    async def test_claude_cli():
        print("🤖 Claude CLI Wrapper 테스트")
        print("=" * 50)

        if not claude_cli.is_available():
            print("❌ Claude CLI 사용 불가")
            return

        test_prompt = "안녕하세요! 당신은 누구인가요? 간단히 답해주세요."
        print(f"🔍 테스트 프롬프트: {test_prompt}")

        result = await claude_cli.generate(test_prompt)

        if result.get("success"):
            print("✅ 성공!")
            print(f"📝 응답: {result['content'][:200]}...")
        else:
            print(f"❌ 실패: {result.get('error')}")

    asyncio.run(test_claude_cli())
