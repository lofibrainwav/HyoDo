# Trinity Score: 90.0 (Established by Chancellor)
import logging
import os

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class VisionResult:
    def __init__(self, passed: bool, screenshot_path: str, errors: list) -> None:
        self.passed = passed
        self.screenshot_path = screenshot_path
        self.errors = errors


class VisionVerifier:
    """The Eyes of the Kingdom.
    Uses Playwright to visually verify GenUI outputs.
    """

    def __init__(self) -> None:
        # Use absolute path to shared artifact directory
        self.screenshot_dir = (
            "${HOME}/.gemini/antigravity/brain/a805a42d-de23-4690-bbb3-e36fd1dfc691"
        )
        # Ensure dir exists in a safe location
        os.makedirs(self.screenshot_dir, exist_ok=True)

    async def verify_url(self, url: str, name: str) -> VisionResult:
        """Visits a URL, takes a screenshot, and checks for console errors."""
        async with async_playwright() as p:
            logger.info(f"👁️ VisionVerifier observing: {url}")
            browser = await p.chromium.launch()
            page = await browser.new_page()

            errors = []
            page.on(
                "console",
                lambda msg: (
                    errors.append(f"Console {msg.type}: {msg.text}")
                    if msg.type == "error" and "hydration" not in msg.text.lower()
                    else None
                ),
            )
            page.on(
                "pageerror",
                lambda exc: (
                    errors.append(f"Page Error: {exc}")
                    if "hydration" not in str(exc).lower()
                    else None
                ),
            )
            page.on(
                "response",
                lambda response: (
                    errors.append(f"Network Error {response.status}: {response.url}")
                    if response.status >= 400
                    else None
                ),
            )

            try:
                await page.goto(url, wait_until="domcontentloaded")

                # Screenshot
                screenshot_path = os.path.join(self.screenshot_dir, f"vision_{name}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"📸 Screenshot captured: {screenshot_path}")

            except Exception as e:
                errors.append(f"Navigation Failed: {e!s}")
                screenshot_path = ""

            await browser.close()

            passed = len(errors) == 0
            if passed:
                logger.info("✅ Vision Check Passed")
            else:
                logger.warning(f"⚠️ Vision Defects Found: {errors}")

            return VisionResult(passed, screenshot_path, errors)
