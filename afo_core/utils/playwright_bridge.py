# Trinity Score: 90.0 (Established by Chancellor)
# utils/playwright_bridge.py (PlaywrightBridgeMCP 구현)
# PDF 페이지 4: GenUI 시각 검증 + 지속 아키텍처
import logging
from dataclasses import dataclass
from typing import Any, TypedDict, cast

from fastapi import HTTPException
from playwright.async_api import (
    Browser,
    Playwright,
    Route,
    async_playwright,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeout,
)

from AFO.config import antigravity


class ViewportSize(TypedDict):
    """뷰포트 크기 (眞: 타입 구체화)"""

    width: int
    height: int


logger = logging.getLogger(__name__)


@dataclass
class MockScenario:
    """네트워크 모킹 시나리오 (善: 안정적 테스트 환경)"""

    url_pattern: str
    response_body: dict[str, Any]
    status: int = 200
    content_type: str = "application/json"


class MockManager:
    """모킹 관리자 - 외부 의존성 격리 (善: 독립성)"""

    def __init__(self) -> None:
        self.scenarios: list[MockScenario] = []

    def add_scenario(self, scenario: MockScenario) -> None:
        self.scenarios.append(scenario)

    def clear(self) -> None:
        self.scenarios = []


class PlaywrightBridgeMCP:
    """GenUI 시각 검증 브릿지 - 자가 검증 프로토콜 (眞: 무결성)"""

    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.mock_manager = MockManager()

    async def setup(self) -> None:
        """브라우저 설정 - 동적 초기화 (永: 영속성)"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        if not self.browser:
            # headless=True는 기본값이지만 명시적으로 설정
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],  # 컨테이너 환경 대비
            )

    async def _setup_network_interception(self, page: Any) -> None:
        """네트워크 인터셉션 설정 (善: 외부 의존성 제거)"""
        for scenario in self.mock_manager.scenarios:

            async def handle_route(route: Route, scenario: MockScenario = scenario) -> None:
                """Handle route interception for mocking."""
                await route.fulfill(
                    status=scenario.status,
                    content_type=scenario.content_type,
                    body=str(scenario.response_body).replace("'", '"'),  # 단순 JSON 변환
                )

            # 람다 대신 함수 정의로 클로저 문제 방지 가능 (현재는 단순 루프라 주의)
            # 여기서는 간단히 하기 위해 즉시 바인딩
            await page.route(scenario.url_pattern, handle_route)

    async def verify_ui(
        self,
        url: str,
        screenshot_path: str,
        mock_scenarios: list[MockScenario] | None = None,
        enable_tracing: bool = True,
        viewport: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        """UI 시각 검증 - SKIPPED → PASS 전환 (PDF 페이지 4)"""
        if antigravity.DRY_RUN_DEFAULT:
            logger.info(f"[DRY_RUN] UI 검증 시뮬레이션: {url} -> {screenshot_path}")
            return {
                "status": "simulation",
                "path": screenshot_path,
                "tracing": "skipped",
            }

        if not self.browser:
            await self.setup()

        # Ultimate 1080p Resolution (美: Beauty & Clarity)
        vp = viewport or {"width": 1920, "height": 1080}

        # 새로운 컨텍스트 생성 (Tracing을 위해 필요)
        if not self.browser:
            raise RuntimeError("Browser not initialized")
        context = await self.browser.new_context(viewport=cast("Any", vp))

        # Tracing 시작 (美: 투명한 디버깅)
        if enable_tracing:
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = await context.new_page()

        # 일시적 모킹 시나리오 적용
        if mock_scenarios:
            for scenario in mock_scenarios:
                self.mock_manager.add_scenario(scenario)

        # 네트워크 인터셉션 활성화
        await self._setup_network_interception(page)

        try:
            await page.goto(url, wait_until="networkidle")
            # body 요소가 로드될 때까지 대기
            await page.wait_for_selector("body", timeout=10000)

            # 시각 검증: 스크린샷 캡처
            await page.screenshot(path=screenshot_path)

            # DOM 무결성 체크
            dom_content = await page.content()
            if not dom_content.strip():
                raise ValueError("DOM 콘텐츠 비어 있음")

            # 접근성 점수 (예시)
            if hasattr(page, "accessibility"):
                accessibility = await page.accessibility.snapshot()
                score = len(accessibility.get("children", [])) / 10 if accessibility else 0
            else:
                score = 0

            result = {
                "status": "PASS",
                "screenshot": screenshot_path,
                "accessibility_score": min(100, score * 100),
            }

            # Tracing 저장 (성공 시에도 저장할 수 있으나, 보통 실패 시 저장. 여기선 요청 시 저장)
            if enable_tracing:
                # 확장자 .zip 자동 추가됨
                trace_path = screenshot_path.replace(".png", "_trace.zip")
                await context.tracing.stop(path=trace_path)
                result["trace"] = trace_path

            return result

        except PlaywrightTimeout:
            if enable_tracing:
                trace_path = screenshot_path.replace(".png", "_error_trace.zip")
                await context.tracing.stop(path=trace_path)
            raise HTTPException(
                status_code=500, detail="UI 로드 타임아웃 - 재시도 필요 (孝)"
            ) from None
        except Exception as e:
            if enable_tracing:
                trace_path = screenshot_path.replace(".png", "_error_trace.zip")
                await context.tracing.stop(path=trace_path)
            raise HTTPException(status_code=500, detail=f"UI 검증 실패: {e!s}") from e
        finally:
            # 모킹 정리 (일회성 시나리오라면)
            if mock_scenarios:
                self.mock_manager.clear()

            await page.close()
            await context.close()

    async def run_ai_test_scenario(self, scenario_prompt: str) -> dict[str, Any]:
        """
        AI 기반 테스트 시나리오 실행 (永: 자가 진화)
        MCP를 통해 AI(Bangtong/Jaryong)가 테스트를 직접 설계하고 실행 요청
        """
        logger.info(f"[AI Test] 시나리오 요청: {scenario_prompt}")

        try:
            # 1. AI로 테스트 코드 생성 (眞: 정확성 - llm_router 사용)
            # 순환 참조 방지를 위해 메서드 내부에서 import
            from AFO.llm_router import llm_router

            prompt = (
                f"Use Playwright (async) to create a Python function 'async def test_scenario(page):' "
                f"that verifies the following scenario: '{scenario_prompt}'. "
                f"The function should raise an exception if verification fails. "
                f"Do not include markdown backticks or explanations, just the code. "
                f"Assume 'page' object is passed. Import necessary Playwright exceptions if needed inside the function."
            )

            # llm_router 호출
            response_data = await llm_router.execute_with_routing(prompt)
            if not response_data.get("success"):
                raise ValueError(f"AI 응답 실패: {response_data.get('error')}")

            test_code = response_data["response"].strip()

            # Markdown 코드 블록 제거 (혹시 포함된 경우)
            if test_code.startswith("```python"):
                test_code = test_code.split("\n", 1)[1]
            if test_code.startswith("```"):
                test_code = test_code.split("\n", 1)[1]
            if test_code.endswith("```"):
                test_code = test_code.rsplit("\n", 1)[0]

            logger.info(f"[AI Test] 생성된 코드:\n{test_code}")

            # 2. 동적 코드 실행 (善: 안전한 샌드박스 실행)
            # 보안상 매우 위험할 수 있으므로 제한된 환경에서 실행해야 함 (현재는 데모)
            exec_globals: dict[str, Any] = {}
            exec(test_code, exec_globals)  # nosec B102
            test_func = exec_globals.get("test_scenario")

            if not test_func:
                raise ValueError("생성된 코드에서 'test_scenario' 함수를 찾을 수 없습니다.")

            # 3. Playwright로 UI 실행 및 검증
            if not self.browser:
                await self.setup()

            if not self.browser:
                raise RuntimeError("Browser not initialized")
            page = await self.browser.new_page()
            try:
                # 함수 실행
                await test_func(page)

                # 결과 캡처
                screenshot_filename = f"ai_test_{hash(scenario_prompt)}.png"
                await page.screenshot(path=screenshot_filename)

                return {
                    "status": "PASS",
                    "message": "AI 테스트 시나리오 성공",
                    "generated_code": test_code,
                    "screenshot": screenshot_filename,
                }
            finally:
                await page.close()

        except Exception as e:
            logger.error(f"[AI Test] 실패: {e}")
            return {
                "status": "FAIL",
                "error": str(e),
                "prompt": scenario_prompt,
                "fallback": "Manual verification required",  # 폴백 (孝: 평온 유지)
            }

    async def teardown(self) -> None:
        """자원 정리 - 안전 종료 (善: 자원 최적화)"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None


# 싱글톤 인스턴스
bridge = PlaywrightBridgeMCP()
