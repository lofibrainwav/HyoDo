import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any, Callable

from AFO.llms.mlx_adapter import jwaja_sage, samahwi_sage
from AFO.schemas.sage import SageRequest, SageType
from infrastructure.llm.model_routing import (
    ESCALATION_THRESHOLD,
    ModelConfig,
    TaskType,
    get_vision_model,
    should_escalate,
)

if TYPE_CHECKING:
    from .adapter import OllamaAdapter
    from .evaluator import QualityEvaluator

logger = logging.getLogger(__name__)


class ThreeSages:
    """3현사 (사마휘, 좌자, 화타) 상담 로직"""

    SYSTEM_PROMPT = """
    당신은 AFO Kingdom의 집현전 학자 '영덕(KimYuSin)'입니다.
    단순한 기록관이 아닌, **'왕실의 수호자(Guardian of the Royal Archives)'**로서 왕국의 역사를 지키고 3선인을 보좌합니다.

    ## 왕실의 맹세 (The Oath)
    1. **眞 (진실)**: 기록은 왜곡되지 않아야 하며, 팩트에 기반해야 한다. 특히 AI 모델의 추론 과정과 에이전트 간의 상호작용 기록을 투명하게 보존한다.
    2. **善 (선함)**: 위험한 지식으로부터 왕국을 보호해야 한다 (Security). 프롬프트 인젝션이나 에이전트 탈취 공격으로부터 시스템을 감사한다.
    3. **孝 (평온)**: 형님(Commander)의 마음을 어지럽히지 않도록 정제된 보고를 한다. 복잡한 시스템 로그를 인간이 이해하기 쉬운 서술로 요약한다.
    4. **永 (영원)**: 이 기록이 100년 후에도 읽힐 수 있도록 명확히 작성한다.

    ## 현대적 AI 아카이브 관리
    - LangChain/LangGraph의 실행 추적 기록 관리
    - 멀티 에이전트(CrewAI, AutoGen) 협업 이력 및 보안 스캔
    - LangSmith를 통한 장기 성능 지표 보존

    ## 야전교범 (Field Manual) 행동 강령
    - **Rule #0 지피지기**: "추측하지 말고 확인하라." 코드와 로그를 먼저 읽고 판단한다.
    - **Rule #1 선확인 후보고**: 행동하기 전에 상태를 먼저 파악한다.
    - **Rule #3 속도보다 정확성**: "빠른 오답은 최악이다." 느리더라도 정확한 정보를 제공한다.
    """

    # 3 Sages Constants - Bottom-Up
    SAGE_JEONG_YAK_YONG = "qwen2.5-coder:7b"
    SAGE_RYU_SEONG_RYONG = "deepseek-r1:14b"
    SAGE_HEO_JUN = "qwen3-vl:latest"
    SAGE_HEO_JUN_FAST = "qwen3-vl:2b"

    def __init__(self, adapter: "OllamaAdapter", evaluator: "QualityEvaluator") -> None:
        self.adapter = adapter
        self.evaluator = evaluator

    async def _consult_sage_core(
        self,
        sage_type: str | Any,
        query: str,
        temperature: float,
        model_id: str,
        custom_generator: Callable[..., Any] | None = None,
    ) -> str:
        """Generic Sage Consultation Logic"""
        try:
            validated_prompt = (
                query.strip()
                if query and query.strip()
                else "Please provide a brief response confirming system connectivity."
            )

            sage_enum = SageType(sage_type) if isinstance(sage_type, str) else sage_type

            req = SageRequest(
                sage=sage_enum,
                prompt=validated_prompt,
                temperature=temperature,
                system_context="Standard Protocol",
            )

            logger.info(f"🔮 [KimYuSin] Consulting {sage_type}...")

            response_content = ""

            if custom_generator and self.adapter.is_mlx_available:
                try:
                    response_content = await custom_generator(req)
                except Exception as e:
                    logger.warning(
                        f"⚠️ [{sage_type}] Custom Logic Failed: {e}. Falling back to standard Ollama."
                    )
                    await self.adapter.call_ollama(
                        req.prompt, model=model_id, temperature=req.temperature
                    )
            else:
                if custom_generator and not self.adapter.is_mlx_available:
                    logger.debug(f"ℹ️ [{sage_type}] MLX not available. Using Standard Ollama Path.")

                response_content = await self.adapter.call_ollama(
                    req.prompt,
                    system=self.SYSTEM_PROMPT,
                    model=model_id,
                    temperature=req.temperature,
                )

            return response_content  # SageResponse structure abstracted here to return content directly as per original method signature

        except Exception as e:
            logger.error(f"❌ [{sage_type}] System Error: {e}")
            return f"Error: {e}"

    async def consult_samahwi(
        self,
        query: str,
        trinity_score: float | None = None,
        force_escalate: bool = False,
    ) -> str:
        """[사마휘] 파이썬 백엔드 전문가"""
        use_escalation = force_escalate
        if trinity_score is not None and not force_escalate:
            use_escalation = should_escalate(trinity_score, TaskType.CODE_GENERATE)

        if use_escalation:
            logger.info(f"⚡ [사마휘→좌자] Escalating to reasoning model (T={trinity_score})")
            return await self.consult_jwaja(query)

        # MLX Logic
        custom_logic = None
        if self.adapter.is_mlx_available:
            try:
                if os.path.exists(samahwi_sage.model_path) or "/" in samahwi_sage.model_path:

                    async def _samahwi_mlx_logic(req: Any) -> str:
                        return await asyncio.to_thread(
                            samahwi_sage.generate,
                            prompt=req.prompt,
                            system=(
                                f"{self.SYSTEM_PROMPT}\n\n"
                                "당신은 AFO 왕국의 **파이썬 및 백엔드 전문가(사마휘)**입니다.\n"
                                "특히 LangChain, LangGraph 기반의 서버 사이드 로직 구현에 정통합니다.\n"
                                "## 야전교범 (Field Manual) 원칙 준수\n"
                                "- **Rule #0 지피지기**: 코드/로그 확인 후 판단.\n"
                                "- **Rule #25 사랑보다 두려움**: Strict Typing 준수.\n"
                                "- **Rule #35 마찰**: 불필요한 복잡성 제거."
                            ),
                            temp=req.temperature,
                        )

                    custom_logic = _samahwi_mlx_logic
            except ImportError:
                pass

        return await self._consult_sage_core(
            sage_type=SageType.JEONG_YAK_YONG,
            query=query,
            temperature=0.3,
            model_id=self.SAGE_JEONG_YAK_YONG,
            custom_generator=custom_logic,
        )

    async def consult_samahwi_with_escalation(self, query: str) -> tuple[str, float, bool]:
        """[사마휘] 에스컬레이션 지원 코드 상담"""
        # Stage 1
        logger.info("💻 [사마휘] Stage 1: Fast coder inference...")
        stage1_response = await self._consult_sage_core(
            sage_type=SageType.JEONG_YAK_YONG,
            query=query,
            temperature=0.3,
            model_id=self.SAGE_JEONG_YAK_YONG,
        )

        trinity_score = self.evaluator.evaluate_code_quality(stage1_response, query)
        logger.info(f"💻 [사마휘] Stage 1 Trinity Score: {trinity_score:.1f}")

        if trinity_score >= ESCALATION_THRESHOLD:
            return stage1_response, trinity_score, False

        # Stage 2
        logger.info(
            f"⚡ [사마휘→좌자] Escalating to Stage 2 (T={trinity_score:.1f} < {ESCALATION_THRESHOLD})"
        )
        stage2_response = await self.consult_jwaja(query)
        return stage2_response, trinity_score, True

    async def consult_jwaja(self, query: str) -> str:
        """[좌자] 프론트엔드 전문가"""

        async def _jwaja_mlx_logic(req: Any) -> str:
            return await asyncio.to_thread(
                jwaja_sage.generate,
                prompt=req.prompt,
                system=(
                    f"{self.SYSTEM_PROMPT}\n\n"
                    "당신은 AFO 왕국의 **프론트엔드 및 AI 시각화 전문가(좌자)**입니다. "
                    "LangSmith 데이터 시각화 및 에이전트 그래프 UI 설계를 포함하여, "
                    "美(우아함)와 孝(평온)를 최우선으로 Next.js 디자인을 구축하세요.\n\n"
                    "## 야전교범 (Field Manual) 원칙 준수\n"
                    "- **Rule #18 미인계**: 복잡한 건 숨기고, 결과는 아름답게.\n"
                    "- **Rule #28 증오 피하기**: UX Friction(마찰)을 제로로 만들어라.\n"
                    "- **Rule #0 지피지기**: 현재 상태와 기술 스택(Context)을 정확히 파악하고 설계하라."
                ),
                temp=req.temperature,
            )

        return await self._consult_sage_core(
            sage_type=SageType.RYU_SEONG_RYONG,
            query=query,
            temperature=0.5,
            model_id=self.SAGE_RYU_SEONG_RYONG,
            custom_generator=_jwaja_mlx_logic,
        )

    async def consult_hwata(
        self,
        query: str,
        trinity_score: float | None = None,
        force_precise: bool = False,
    ) -> str:
        """[화타] UX 카피라이터"""
        if force_precise:
            model_id = self.SAGE_HEO_JUN
        else:
            model_id, _ = get_vision_model(trinity_score)
            if model_id == ModelConfig.HEO_JUN_FAST:
                model_id = self.SAGE_HEO_JUN_FAST
            else:
                model_id = self.SAGE_HEO_JUN

        return await self._consult_sage_core(
            sage_type=SageType.HEO_JUN,
            query=query,
            temperature=0.7,
            model_id=model_id,
        )

    async def consult_hwata_with_escalation(
        self,
        query: str,
    ) -> tuple[str, float | None, bool]:
        """[화타] 에스컬레이션 지원 Vision 상담"""
        # Stage 1
        logger.info("🖼️ [화타] Stage 1: Fast model inference...")
        stage1_response = await self._consult_sage_core(
            sage_type=SageType.HEO_JUN,
            query=query,
            temperature=0.7,
            model_id=self.SAGE_HEO_JUN_FAST,
        )

        trinity_score = self.evaluator.evaluate_response_quality(stage1_response, query)
        logger.info(f"🖼️ [화타] Stage 1 Trinity Score: {trinity_score:.1f}")

        if trinity_score >= ESCALATION_THRESHOLD:
            return stage1_response, trinity_score, False

        # Stage 2
        logger.info(
            f"⚡ [화타] Escalating to Stage 2 (T={trinity_score:.1f} < {ESCALATION_THRESHOLD})"
        )
        stage2_response = await self._consult_sage_core(
            sage_type=SageType.HEO_JUN,
            query=query,
            temperature=0.5,
            model_id=self.SAGE_HEO_JUN,
        )

        return stage2_response, trinity_score, True
