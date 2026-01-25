# Trinity Score: 90.0 (Established by Chancellor)
import asyncio
import logging
import shutil

logger = logging.getLogger("AFO.LLMs.CLI")

MAX_PROMPT_CHARS = 100_000
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


class CLIWrapper:
    """Wraps local CLI tools (codex, claude, ollama) to act as LLM providers.
    Uses subprocess to execute commands and capture stdout.
    This enables usage of 'Monthly Subscription' accounts without API Keys.
    """

    @staticmethod
    def is_available(tool: str) -> bool:
        """Check if a CLI tool is installed and executable."""
        return shutil.which(tool) is not None

    @staticmethod
    async def run_command(
        command: list[str],
        timeout: int = 120,
        stdin_payload: bytes | None = None,
    ) -> dict:
        """Runs a shell command and returns output."""
        try:
            logger.debug(f"Executing CLI: {' '.join(command)}")
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE if stdin_payload is not None else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(stdin_payload), timeout=timeout
                )
                result = stdout.decode().strip()
                error = stderr.decode().strip()

                # Check for specific CLI error patterns even if returncode is 0 (some capture logs in stdout)
                if process.returncode != 0:
                    logger.warning(f"CLI Error ({command[0]}): {error}")
                    return {"success": False, "error": error}

                return {"success": True, "content": result}

            except TimeoutError:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                logger.error(f"CLI Timeout ({command[0]})")
                return {"success": False, "error": "Timeout"}

        except Exception as e:
            logger.error(f"CLI Exception: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def execute_codex(prompt: str) -> dict:
        """Call Codex CLI (OpenAI).
        Uses 'codex exec' to run the agent.
        """
        if not CLIWrapper.is_available("codex"):
            return {"success": False, "error": "Codex CLI not found"}

        # We constrain Codex to just answer, preventing it from running random shell commands if possible.
        # But 'exec' is agentic. We append a system-like instruction.
        enhanced_prompt = f"Answer the following question directly and concisely without executing system commands if possible: {prompt}"

        # Disable MCP to prevent docker errors seen previously
        # Note: --disable mcp might not work if flag is unknown, relying on config.toml patch
        cmd = ["codex", "exec", enhanced_prompt]

        res = await CLIWrapper.run_command(cmd)

        # Codex output often includes logs. We might need to clean it.
        # But for now, returning raw content is safer than over-cleaning.
        return res

    @staticmethod
    async def execute_claude(prompt: str) -> dict:
        """Call Claude CLI (Anthropic).
        Uses 'claude <prompt>' which acts as a REPL but accepts prompt as arg.
        """
        if not CLIWrapper.is_available("claude"):
            return {"success": False, "error": "Claude CLI not found"}

        # Claude outputs '2' for '1+1'. It's clean.
        # Use -p flag for non-interactive mode
        prompt = _trim_prompt(prompt)
        cmd = ["claude", "-p", "--input-format", "text"]
        res = await CLIWrapper.run_command(cmd, stdin_payload=prompt.encode())
        if not res.get("success") and _stdin_unsupported(res.get("error", "")):
            cmd = ["claude", "-p", prompt]
            return await CLIWrapper.run_command(cmd)
        return res

    @staticmethod
    async def execute_ollama(prompt: str, model: str | None = None) -> dict:
        """Call Ollama CLI"""
        if not CLIWrapper.is_available("ollama"):
            return {"success": False, "error": "Ollama CLI not found"}

        # Use Model from Env or Default
        if not model:
            import os

            model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

        cmd = ["ollama", "run", model, prompt]
        return await CLIWrapper.run_command(cmd)
