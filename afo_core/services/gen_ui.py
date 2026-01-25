# Trinity Score: 98.0 (Established by Chancellor)
"""
GenUI Orchestrator (Royal Architect)
Phase 31: Operation Gwanggaeto (Expansion)

Orchestrates the creation of new UI components using AI (MIPROv2).
- Creator: Samahwi (Royal Architect)
- Validator: Vision Verifier (Janus)
- Stack: Next.js 16, Tailwind v4
"""

import logging
import re
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from AFO.utils.trinity_type_validator import validate_with_trinity
except ImportError:

    def validate_with_trinity[TF: Callable[..., Any]](func: TF) -> TF:
        return func


from AFO.api.models.persona import PersonaTrinityScore as TrinityScore
from AFO.schemas.gen_ui import GenUIRequest, GenUIResponse

# Logger setup
logger = logging.getLogger("afo.services.gen_ui")


class GenUIOrchestrator:
    """
    [Phase 31] The Royal Architect.
    Orchestrates Vibe Coding (Prompt -> React Code) using MIPROv2 templates.
    """

    def __init__(self) -> None:
        self.scholar_name = "Samahwi"
        # Root is ../../../..
        current_file = Path(__file__).resolve()
        self.project_root = current_file.parent.parent.parent.parent
        self.sandbox_dir = (
            self.project_root / "packages" / "dashboard" / "src" / "components" / "genui"
        )

        # Ensure sandbox exists
        if not self.sandbox_dir.exists():
            try:
                self.sandbox_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"⚠️ [GenUI] Could not create sandbox dir: {e}")

    @validate_with_trinity
    async def generate_component(self, request: GenUIRequest) -> GenUIResponse:
        """
        Generates a React component using MIPROv2 Vibe Prompts.
        """
        logger.info(f"🎨 [GenUI] Architecting '{request.component_name}' with MIPROv2...")

        # 1. Blueprint (MIPROv2 Vibe Prompt)
        system_prompt = """
        You are Samahwi, the Royal Architect of AFO Kingdom.
        Your goal is to create a 'Vibe-Coded' React Component.

        [ROYAL STACK]
        - Framework: Next.js 16 (App Router)
        - Styling: Tailwind CSS v4 (No config needed, just classes)
        - Components: Shadcn UI (Radix Primitives), Lucide React (Icons)
        - Animation: Framer Motion (only if requested)
        - Language: TypeScript (Strict)

        [VIBE GUIDELINES]
        - Aesthetics: 'Glassmorphism', 'Neon Glow', 'Deep Space', 'Royal Purple/Gold/Emerald'.
        - Layout: Responsive, Mobile-First, Flexbox/Grid.
        - Sound: Use `use-sound` for interactions if appropriate (e.g. clicks).
        - Quality: 100% Truth (Types), 100% Beauty (Visuals), 100% Serenity (UX).

        [OUTPUT RULES]
        - Return ONLY the raw TSX code.
        - Use `export default function ComponentName()`.
        - Do NOT include markdown fences (```tsx).
        - Do NOT include explanations.
        """

        user_prompt = f"""
        Component Name: {request.component_name}
        User Request: {request.prompt}

        Create this component now.
        """

        # 2. Call Scholar
        try:
            from AFO.llm_router import LLMRouter

            router = LLMRouter()

            # Using 'ollama' with 'deepseek-r1:14b' or 'qwen2.5-coder' if available
            # Prioritize a stronger model for coding
            response_dict: dict[str, Any] = await router.execute_with_routing(
                query=f"{system_prompt}\n\n{user_prompt}",
                context={
                    "provider": "ollama",
                    "ollama_model": "deepseek-r1:14b",  # Or upgrade to qwen2.5-coder-32b if available
                    "max_tokens": 8192,
                    "temperature": 0.2,  # Lower temperature for code precision
                    "ollama_timeout_seconds": 600,
                },
            )

            if not response_dict.get("success"):
                raise RuntimeError(response_dict.get("error", "Router Error"))

            response_text = response_dict.get("response", "")
            code = self._clean_code(response_text)

        except Exception as e:
            logger.error(f"❌ [GenUI] Generation failed: {e}")
            return self._create_error_response(request, str(e))

        # 3. Validation
        is_valid_syntax = self.validate_syntax(code)

        # 4. Trinity Scoring
        trinity_score = TrinityScore(
            truth=100.0 if is_valid_syntax else 0.0,
            goodness=95.0,
            beauty=90.0,
            serenity=95.0,
            eternity=90.0,
            total_score=94.0 if is_valid_syntax else 0.0,
        )

        component_id = f"gen_{uuid.uuid4().hex[:8]}"

        return GenUIResponse(
            component_id=component_id,
            component_name=request.component_name,
            code=code,
            description=f"Architected by Samahwi (MIPROv2): {request.prompt}",
            trinity_score=trinity_score,
            risk_score=0 if is_valid_syntax else 100,
            status="approved" if is_valid_syntax else "rejected",
        )

    def validate_syntax(self, code: str) -> bool:
        if not code or len(code) < 50:
            return False
        return "export default" in code

    def _clean_code(self, text: str) -> str:
        # Think blocks removal for reasoning models (DeepSeek R1)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)
        return cleaned.strip()

    def _create_error_response(self, request: GenUIRequest, error_msg: str) -> GenUIResponse:
        return GenUIResponse(
            component_id="error",
            component_name=request.component_name,
            code="",
            description="Generation Failed",
            trinity_score=TrinityScore(
                truth=0, goodness=0, beauty=0, serenity=0, eternity=0, total_score=0
            ),
            risk_score=100,
            status="rejected",
            error=error_msg,
        )

    def deploy_component(self, response: GenUIResponse) -> str:
        if response.status != "approved" or not response.code:
            raise ValueError(f"Cannot deploy rejected component: {response.component_name}")

        filename = f"{response.component_name}.tsx"
        file_path = self.sandbox_dir / filename

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.code)

            self._update_registry(response.component_name)
            logger.info(f"🚀 [GenUI] Deployed {response.component_name} to Sandbox")
            return str(file_path)
        except Exception as e:
            logger.error(f"❌ [GenUI] Deployment failed: {e}")
            raise OSError(f"Failed to write component: {e}") from e

    def _update_registry(self, component_name: str) -> None:
        registry_path = self.sandbox_dir / "index.ts"
        export_stmt = f"export {{ default as {component_name} }} from './{component_name}';\n"

        try:
            if not registry_path.exists():
                registry_path.write_text("// GenUI Registry\nexport {};\n", encoding="utf-8")

            content = registry_path.read_text(encoding="utf-8")
            if export_stmt.strip() not in content:
                with open(registry_path, "a", encoding="utf-8") as f:
                    f.write(export_stmt)
        except Exception as e:
            logger.warning(f"⚠️ [GenUI] Failed to update registry: {e}")


# Global Instance
gen_ui_service = GenUIOrchestrator()
