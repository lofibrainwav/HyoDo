# Trinity Score: 90.0 (Established by Chancellor)
import asyncio
import base64
import logging
from typing import Any, cast

import httpx
from playwright.async_api import async_playwright
from pydantic import ValidationError

from AFO.domain.janus.contract import VisualAction, VisualPlan
from config.settings import settings

logger = logging.getLogger(__name__)


class VisualAgent:
    """Step 2: Loop Engine (The Engine of Janus)
    Integrates Brain (Qwen3-VL), Eye (BBox), and Hand (Playwright).
    """

    def __init__(self, ollama_url: str | None = None, model: str | None = None) -> None:
        self.ollama_url = ollama_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.system_prompt = """You are a GUI Agent.
        You receive a screenshot and a goal.
        You MUST output a JSON object adhering strictly to the VisualPlan schema.
        Use "bbox" [x, y, w, h] normalized (0-1) for clicks.
        Output ONLY JSON."""

    async def capture_screenshot(self, url: str = "http://localhost:3000") -> dict[str, Any]:
        """Eye (Screenshot Capture): Capture current screen state
        Returns: {image_b64, width, height, url, timestamp}
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            try:
                page = await browser.new_page()
                await page.goto(url)
                await page.wait_for_load_state("networkidle")

                # Capture screenshot
                screenshot_bytes = await page.screenshot(full_page=False)
                image_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

                # Get viewport size
                viewport = page.viewport_size
                width = viewport["width"] if viewport else 1920
                height = viewport["height"] if viewport else 1080

                return {
                    "image_b64": f"data:image/png;base64,{image_b64}",
                    "width": width,
                    "height": height,
                    "url": url,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            finally:
                await browser.close()

    async def analyze_and_plan(self, screenshot_data: dict[str, Any], goal: str) -> VisualPlan:
        """Brain (Qwen3-VL): Analyze screenshot and create action plan"""
        try:
            image_b64 = screenshot_data["image_b64"]
            # Remove data URL prefix if present
            if image_b64.startswith("data:image"):
                image_b64 = image_b64.split(",")[1]

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": f"Goal: {goal}\n\nAnalyze this screenshot and create a plan.",
                        "images": [image_b64],
                    },
                ],
                "format": "json",
                "stream": False,
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.ollama_url}/api/chat", json=payload, timeout=60.0)
                resp.raise_for_status()
                result = resp.json()
                content = result.get("message", {}).get("content", "")

            # Parse and Validate (Janus Contract)
            plan = VisualPlan.model_validate_json(content)

            # Safety Checks (Yi Sun-sin's Gates)
            for action in plan.actions:
                if action.confidence < 0.7:
                    action.safety = "confirm"
                if action.type in ["delete", "pay", "submit", "logout"]:
                    action.safety = "confirm"

            logger.info(f" Visual plan created: {len(plan.actions)} actions")
            return plan

        except ValidationError as e:
            logger.error(f"Janus Contract Violation: {e}")
            return VisualPlan(
                goal=goal, actions=[], stop=True, summary=f"Contract violation: {e!s}"
            )
        except Exception as e:
            logger.error(f"Brain analysis failed: {e}")
            return VisualPlan(goal=goal, actions=[], stop=True, summary=f"Analysis error: {e!s}")

    async def execute_action(
        self, action: VisualAction, screenshot_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Hand (Playwright): Execute single validated action"""
        try:
            # Denormalize bbox for screen coordinates
            screen_x = int(action.bbox.x * screenshot_data["width"]) if action.bbox else 0
            screen_y = int(action.bbox.y * screenshot_data["height"]) if action.bbox else 0

            async with async_playwright() as p:
                browser = await p.chromium.launch()
                try:
                    page = await browser.new_page()
                    await page.goto(screenshot_data["url"])
                    await page.wait_for_load_state("networkidle")

                    result = {"success": False, "error": "Unknown action type"}

                    if action.type == "click" and action.bbox:
                        await page.mouse.click(screen_x, screen_y)
                        result = {
                            "success": True,
                            "action": "click",
                            "position": (screen_x, screen_y),
                        }

                    elif action.type == "type" and action.text:
                        if action.bbox:
                            await page.mouse.click(screen_x, screen_y)
                        await page.keyboard.type(action.text)
                        result = {
                            "success": True,
                            "action": "type",
                            "text": action.text,
                        }

                    elif action.type == "scroll":
                        await page.evaluate("window.scrollBy(0, 500)")
                        result = {"success": True, "action": "scroll"}

                    elif action.type == "wait":
                        await asyncio.sleep(2)
                        result = {"success": True, "action": "wait"}

                    elif action.type == "goto" and action.text:
                        await page.goto(action.text)
                        result = {"success": True, "action": "goto", "url": action.text}

                    # Wait a bit for any dynamic changes
                    await asyncio.sleep(0.5)

                    return result

                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def run_janus_loop(
        self, goal: str, url: str = "http://localhost:3000", max_iterations: int = 5
    ) -> dict[str, Any]:
        """Complete Janus Loop: Screenshot -> Plan -> Execute -> Screenshot"""
        results = []
        iteration = 0

        while iteration < max_iterations:
            logger.info(f"= Janus Iteration {iteration + 1}")

            # Eye: Capture screenshot
            screenshot_data = await self.capture_screenshot(url)

            # Brain: Analyze and plan
            plan = await self.analyze_and_plan(screenshot_data, goal)

            if plan.stop or len(plan.actions) == 0:
                break

            # Execute first action (Step mode for safety)
            if plan.actions:
                action = plan.actions[0]
                execution_result = await self.execute_action(action, screenshot_data)
                results.append(
                    {
                        "iteration": iteration,
                        "action": action.model_dump(),
                        "result": execution_result,
                    }
                )

                # If execution failed, stop the loop
                if not execution_result.get("success"):
                    break

            iteration += 1

        return {
            "iterations_completed": iteration,
            "total_actions": len(results),
            "successful_actions": len(
                [r for r in results if cast("dict[str, Any]", r["result"]).get("success")]
            ),
            "results": results,
            "final_goal": goal,
        }
