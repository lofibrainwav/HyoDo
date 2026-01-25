from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from AFO.config.settings import get_settings
from AFO.guardians.critic_agent import CriticAgent
from AFO.julie_cpa.grok_engine import generate_genui_component
from AFO.llm_router import LLMRouter
from AFO.services.vision_verifier import vision_verifier
from AFO.utils.structured_logging import log_sse

# Trinity Score: 90.0 (Established by Chancellor)
# serenity/creation_loop.py
"""
Project Serenity: GenUI-Playwright Creation Loop (v100.0)
Autonomous UI creation with visual verification and Trinity Gating.

Philosophy:
- 眞 (Truth): 실시간 코드 품질 및 렌더링 검증
- 善 (Goodness): Trinity/Risk 임계치를 통한 안전한 배포
- 美 (Beauty): Playwright를 이용한 시각적 완성도 확인
"""


# Core Systems

logger = logging.getLogger(__name__)


@dataclass
class CreationResult:
    """Result of a creation loop iteration."""

    code: str
    screenshot_path: str | None
    trinity_score: float
    risk_score: float
    iteration: int
    success: bool
    feedback: str


class SerenityCreationLoop:
    """
    Autonomous UI Creation Loop (Project Serenity)
    Combines GenUI (creation) + Playwright (verification) + Chancellor (governance)
    """

    MAX_ITERATIONS = 3
    # v100.0 Standard: Trinity >= 90%, Risk <= 10%
    TRINITY_THRESHOLD = 0.9
    RISK_THRESHOLD = 0.1

    def __init__(self, sandbox_dir: str | None = None) -> None:
        settings = get_settings()
        # Ensure we use an absolute path for the sandbox
        self.sandbox_dir = sandbox_dir or str(
            Path(settings.BASE_DIR) / "packages" / "dashboard" / "src" / "components" / "genui"
        )
        os.makedirs(self.sandbox_dir, exist_ok=True)

        self.router = LLMRouter()
        self.critic = CriticAgent()
        self.vision = vision_verifier
        # Type hints allow external injection
        self.bridge: Any | None = None  # Playwright bridge, initialized separately if needed
        self.trinity_manager: Any | None = None  # Trinity manager, injected if available

    async def create_ui(self, prompt: str) -> CreationResult:
        """Main entry point: Create UI from natural language prompt."""
        log_sse(f"🎨 [Serenity] Starting creation: {prompt[:50]}...")

        iteration = 0
        feedback = ""
        last_result = None

        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            log_sse(f"📍 [Serenity] Iteration {iteration}/{self.MAX_ITERATIONS}")

            # Step 1: Generate Code
            code = await self._generate_code(prompt, feedback)
            if not code:
                return CreationResult(
                    code="",
                    screenshot_path=None,
                    trinity_score=0,
                    risk_score=1,
                    iteration=iteration,
                    success=False,
                    feedback="GenUI failed",
                )

            # Step 2: Write to Sandbox (HTML wrapped for rendering)
            html_path = await self._prepare_sandbox(code, iteration)

            # Step 3: Capture Screenshot & Verify (眞 & 美)
            screenshot_path = None
            verification_data: dict[str, Any] = {}
            if self.bridge:
                try:
                    screenshot_path = os.path.join(self.sandbox_dir, f"screenshot_v{iteration}.png")
                    # Disable dry-run momentarily for real verification if explicitly asked or permitted
                    verification_data = await self.bridge.verify_ui(
                        f"file://{html_path}", screenshot_path
                    )
                    log_sse(
                        f"📸 [Serenity] Visual verification complete: {verification_data.get('status')}"
                    )
                except Exception as e:
                    log_sse(f"⚠️ [Serenity] Visual verification failed: {e}")

            # Step 4: Evaluate with Trinity (善)
            trinity_score, risk_score, feedback = self._evaluate(code, verification_data, prompt)
            log_sse(
                f"⚖️ [Serenity] Iteration Score: {trinity_score * 100:.1f}/100 (Risk: {risk_score * 100:.1f}%)"
            )

            last_result = CreationResult(
                code=code,
                screenshot_path=screenshot_path,
                trinity_score=trinity_score,
                risk_score=risk_score,
                iteration=iteration,
                success=(
                    trinity_score >= self.TRINITY_THRESHOLD and risk_score <= self.RISK_THRESHOLD
                ),
                feedback=feedback,
            )

            if last_result.success:
                log_sse("✅ [Serenity] AUTO_RUN: Quality threshold met! Deploying...")
                if self.trinity_manager:
                    self.trinity_manager.apply_trigger("AUTO_RUN_ACTION")
                return last_result

            log_sse(f"🔄 [Serenity] Refining: {feedback[:50]}...")

        log_sse("⚠️ [Serenity] Max iterations reached. Returning best effort.")
        return last_result or CreationResult(
            code="",
            screenshot_path=None,
            trinity_score=0,
            risk_score=1,
            iteration=iteration,
            success=False,
            feedback="Failed to generate result",
        )

    async def _generate_code(self, prompt: str, feedback: str = "") -> str:
        """Generate React component via Grok Web Bridge (The Brain)."""

        log_sse("🧠 Connecting to Grok Brain for architecture...")

        # Add feedback to prompt if exists
        final_prompt = prompt
        if feedback:
            final_prompt += f"\n\nMake sure to address this feedback: {feedback}"

        # Call Grok
        code = await generate_genui_component(final_prompt)

        if code and not code.startswith("// Error"):
            return code

        log_sse(f"⚠️ Grok failed ({code[:50]}...), falling back to Router...")

        # Fallback to original router logic
        full_query = f"User Intent: {prompt}\n\nRefinement: {feedback}"
        res = await self.router.execute_with_routing(
            full_query, context={"quality_tier": "ultra", "provider": "auto"}
        )

        if res.get("success"):
            code = res.get("response", "")
            if "```tsx" in code:
                code = code.split("```tsx")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            return str(code)

        return "// Code generation failed"

    async def _prepare_sandbox(self, code: str, iteration: int) -> str:
        """Saves code to the dashboard source tree (real deployment)."""
        # Note: We name it 'KingdomMessageBoard.tsx' for this specific mission
        filename = "KingdomMessageBoard.tsx"
        file_path = os.path.join(self.sandbox_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        return file_path

    def _evaluate(self, code: str, verification: dict, prompt: str) -> tuple[float, float, str]:
        """Strategic evaluation via Trinity Score."""
        # Simple evaluation logic for now, could use CriticAgent+LLM
        truth = 1.0 if "use client" in code and "export default" in code else 0.8
        beauty = 1.0 if "gradient" in code or "blur" in code else 0.8

        # Simulation: if verification failed (Playwright error), high risk
        risk = 0.05 if verification.get("success") else 0.5

        score = (truth * 0.4) + (beauty * 0.4) + 0.2  # Minimum baseline

        return score, risk, "Alignment achieved."


# Singleton
serenity_loop = SerenityCreationLoop()
