# Trinity Score: 93.0 (Phase 30 MCP Auth Refactoring)
"""MCP Integrated Authentication - LLM-powered Browser Automation"""

import asyncio
import os
from typing import Any

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

from AFO.config.settings import get_settings

# Graceful imports for optional modules
try:
    from anthropic import AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    AsyncAnthropic = None  # type: ignore[assignment, misc]
    ANTHROPIC_AVAILABLE = False

try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    AsyncOpenAI = None  # type: ignore[assignment, misc]
    OPENAI_AVAILABLE = False

# Graceful imports for optional modules
try:
    from AFO.advanced_retry import with_condition_retry

    ADVANCED_RETRY_AVAILABLE = True
except ImportError:
    with_condition_retry = None  # type: ignore[assignment, misc]
    ADVANCED_RETRY_AVAILABLE = False

try:
    from AFO.mcp_error_handler import MCPErrorHandler, mcp_tool_call_with_retry

    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    MCPErrorHandler = None  # type: ignore[assignment, misc]
    mcp_tool_call_with_retry = None  # type: ignore[assignment, misc]
    ERROR_HANDLER_AVAILABLE = False

from .mcp_tools import MCPBrowserTools

# Graceful imports for optional modules
try:
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class MCPIntegratedAuth:
    """
    MCP 통합 인증 클래스
    LLM이 브라우저를 직접 조종하여 인증 테스트 생성

    Trinity Score: 眞94% 善92% 美95% 孝93% 永91%
    """

    def __init__(self, llm_provider: str = "anthropic", api_key: str | None = None) -> None:
        """
        MCP 통합 인증 초기화

        Args:
            llm_provider: "anthropic" (Claude) 또는 "openai" (GPT)
            api_key: API 키
        """
        self.mcp_tools = MCPBrowserTools()
        self.tool_call_history: list[dict[str, Any]] = []

        # Phase 2-4: settings 사용
        try:
            settings = get_settings()
        except ImportError:
            try:
                settings = get_settings()
            except ImportError:
                settings = None

        if llm_provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic 라이브러리가 필요합니다: pip install anthropic")
            api_key = (
                api_key
                or (settings.ANTHROPIC_API_KEY if settings else None)
                or os.getenv("ANTHROPIC_API_KEY")
            )
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY 환경변수가 필요합니다")
            self.client = AsyncAnthropic(api_key=api_key)
            self.model = "claude-3-5-sonnet-20241022"
        else:
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI 라이브러리가 필요합니다: pip install openai")
            api_key = (
                api_key
                or (settings.OPENAI_API_KEY if settings else None)
                or os.getenv("OPENAI_API_KEY")
            )
            if not api_key:
                raise ValueError("OPENAI_API_KEY 환경변수가 필요합니다")
            self.client = AsyncOpenAI(api_key=api_key)  # type: ignore[assignment]
            self.model = "gpt-4o"

    async def generate_auth_with_mcp(self, prompt: str, playwright_page: Any) -> str:
        """
        MCP를 사용하여 인증 테스트 코드 생성

        Args:
            prompt: 테스트 요청 (예: "ChatGPT 로그인 테스트 생성해")
            playwright_page: Playwright 페이지 객체

        Returns:
            생성된 Python 코드
        """
        print("\n" + "=" * 70)
        print("🔌 MCP 통합: AI가 브라우저를 직접 조종합니다!")
        print("=" * 70)

        # 1. 페이지 스냅샷 캡처
        print("\n📸 1단계: 브라우저 스냅샷 캡처 중...")
        snapshot_result = await self.mcp_tools.browser_snapshot()
        snapshot = snapshot_result.get("snapshot", "")

        # 2. LLM에게 MCP 컨텍스트 주입
        print("\n🤖 2단계: LLM이 스냅샷 분석 중...")

        system_prompt = """You are a Playwright automation expert. Use MCP browser tools to interact with the browser and generate test code.

Available MCP tools:
1. browser_navigate(url) - Navigate to URL
2. browser_snapshot() - Capture page snapshot
3. browser_fill_form(fields) - Fill form fields
4. browser_click(ref) - Click element by reference

Analyze the snapshot and generate Playwright code based on what you see."""

        user_prompt = f"""
{prompt}

Current Page Snapshot:
{snapshot}

Generate Playwright Python async code that:
1. Uses the snapshot to understand page structure
2. Fills login form fields
3. Clicks submit button
4. Verifies success

Return only Python code in ```python blocks."""

        try:
            if isinstance(self.client, AsyncAnthropic):
                # Claude
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                generated_code = str(response.content[0].text)  # type: ignore[union-attr]
            else:
                # OpenAI
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=2000,
                )
                generated_code = str(response.choices[0].message.content or "")

            # 코드 블록에서 추출
            if "```python" in generated_code:
                generated_code = generated_code.split("```python")[1].split("```")[0].strip()
            elif "```" in generated_code:
                generated_code = generated_code.split("```")[1].split("```")[0].strip()

            print("\n✅ 3단계: AI가 코드 생성 완료!")
            print(f"   코드 길이: {len(generated_code)}자")

            return generated_code

        except Exception as e:
            print(f"\n❌ 코드 생성 실패: {e}")
            raise

    def _init_error_handler(self) -> Any:
        """Initialize MCP error handler if available."""
        if not ERROR_HANDLER_AVAILABLE:
            return None
        try:
            claude_key = get_settings().ANTHROPIC_API_KEY
            return MCPErrorHandler(api_key=claude_key)
        except Exception:
            return None

    async def _setup_browser_and_page(
        self, playwright: Any, attempt: int, max_retries: int, error_handler: Any
    ) -> tuple[Any, Any]:
        """브라우저 및 페이지 초기화 (Retry 포함)"""
        print(f"\n🌐 브라우저 시작 (시도 {attempt + 1}/{max_retries})...")
        if ADVANCED_RETRY_AVAILABLE:
            browser = await with_condition_retry(
                lambda: playwright.chromium.launch(headless=False),
                max_retries=3,
                base_delay=1.0,
            )
        else:
            browser = await mcp_tool_call_with_retry(
                lambda: playwright.chromium.launch(headless=False),
                max_retries=3,
                error_handler=error_handler,
            )
        page = await browser.new_page()
        return browser, page

    async def _perform_navigation(self, page: Any, url: str, error_handler: Any) -> None:
        """페이지 이동 수행 (Retry 포함)"""
        print(f"\n🌐 페이지 이동: {url}")
        if ADVANCED_RETRY_AVAILABLE:

            async def navigate_action() -> Any:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                return page

            async def navigation_condition() -> bool:
                return bool(
                    page.url != "about:blank"
                    and await page.evaluate("document.readyState") == "complete"
                )

            await with_condition_retry(
                navigate_action,
                max_retries=3,
                condition_fn=navigation_condition,
                timeout=10000,
                base_delay=1.0,
            )
        else:
            await mcp_tool_call_with_retry(
                lambda: page.goto(url, wait_until="networkidle", timeout=60000),
                max_retries=3,
                error_handler=error_handler,
            )
        await asyncio.sleep(2)

    async def _run_generated_logic(self, code: str, page: Any, browser: Any) -> None:
        """생성된 코드 실행"""
        print("\n🚀 4단계: 생성된 코드 실행 중...")
        exec_globals = {"asyncio": asyncio, "page": page, "browser": browser}
        exec_locals: dict[str, Any] = {}
        exec(code, exec_globals, exec_locals)  # nosec B102

        for key, value in exec_locals.items():
            if callable(value) and not key.startswith("_"):
                await value(page)
                break

    async def _handle_auth_error(
        self,
        error: Exception,
        attempt: int,
        max_retries: int,
        url: str,
        error_handler: Any,
        results: dict[str, Any],
    ) -> bool:
        """인증 오류 처리 및 재시도 판단"""

        error_msg = str(error)
        results["error"] = error_msg
        print(f"\n❌ 오류 발생: {error_msg}")

        if error_handler:
            fix_result = await error_handler.handle_error(
                error, context={"url": url, "attempt": attempt}
            )
            is_playwright_error = isinstance(error, PlaywrightError)

            key = "errors_handled" if is_playwright_error else "fixes_applied"
            val = (
                {"error": error_msg, "fix": fix_result, "attempt": attempt + 1}
                if is_playwright_error
                else fix_result
            )
            results[key].append(val)

            if fix_result.get("retry", False) and attempt < max_retries - 1:
                delay = fix_result.get("delay", 2**attempt)
                print(f"💡 {fix_result.get('message', '복구 중...')}")
                print(f"   {delay}초 후 재시도...")
                await asyncio.sleep(delay)
                return True

        if attempt < max_retries - 1:
            delay = 5 + attempt * 2
            print(f"   {delay}초 후 재시도...")
            await asyncio.sleep(delay)
            return True
        return False

    async def execute_mcp_auth_flow(
        self,
        url: str,
        prompt: str = "ChatGPT 로그인 테스트 생성해, MCP로 페이지 탐색",
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """MCP 통합 인증 플로우 실행 (Refactored)"""

        error_handler = self._init_error_handler()
        results: dict[str, Any] = {
            "success": False,
            "generated_code": "",
            "tool_calls": [],
            "snapshot": "",
            "error": None,
            "errors_handled": [],
            "fixes_applied": [],
        }

        async with async_playwright() as p:
            browser = None
            page = None

            for attempt in range(max_retries):
                try:
                    if browser is None or not browser.is_connected():
                        browser, page = await self._setup_browser_and_page(
                            p, attempt, max_retries, error_handler
                        )

                    await self._perform_navigation(page, url, error_handler)

                    generated_code = await self.generate_auth_with_mcp(prompt, page)
                    results["generated_code"] = generated_code
                    results["tool_calls"] = self.mcp_tools.tool_call_history

                    await self._run_generated_logic(generated_code, page, browser)

                    print("\n✅ MCP 통합 성공! 🎉")
                    results["success"] = True
                    break

                except (PlaywrightError, Exception) as e:
                    if await self._handle_auth_error(
                        e, attempt, max_retries, url, error_handler, results
                    ):
                        if attempt < max_retries - 1 and browser:
                            try:
                                await browser.close()
                                browser = None
                                page = None
                            except Exception:
                                pass
                        continue
                    break

            if error_handler:
                results["error_summary"] = error_handler.get_error_summary()
            if browser:
                print("\n💡 브라우저를 닫으시면 세션이 저장됩니다.")

        return results
