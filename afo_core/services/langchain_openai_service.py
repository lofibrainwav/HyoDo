# Trinity Score: 90.0 (Established by Chancellor)
"""
LangChain + OpenAI Service for AFO Kingdom (Phase 10)
Advanced AI integration with LangChain and OpenAI for intelligent processing.
Sequential Thinking: 단계별 AI 서비스 구축 및 최적화
"""

import asyncio
import logging
from typing import Any

# LangChain 1.2.0+ API 변경사항 반영
# 타입 별칭 문제를 피하기 위해 런타임에서만 import
try:
    from langchain_core.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI

    LANGCHAIN_NEW_API = True
except ImportError:
    # Fallback for older versions
    try:
        from langchain.llms import OpenAI as ChatOpenAI  # type: ignore[no-redef]
        from langchain.prompts import PromptTemplate  # type: ignore[no-redef]

        # LANGCHAIN_NEW_API = False (Redundant)
    except ImportError:
        # Fallback - Use Any for everything to silence MyPy on legacy paths
        ChatOpenAI = Any  # type: ignore[assignment, misc]
        PromptTemplate = Any  # type: ignore[assignment, misc]
        BaseMessage = Any  # type: ignore[assignment, misc]
        HumanMessage = Any  # type: ignore[assignment, misc]
        SystemMessage = Any  # type: ignore[assignment, misc]
        LANGCHAIN_NEW_API = False

from ..utils.circuit_breaker import CircuitBreaker
from ..utils.exponential_backoff import exponential_backoff
from .redis_cache_service import cache_get, cache_set

# 로깅 설정
logger = logging.getLogger(__name__)

# OpenAI 설정
OPENAI_CONFIG = {
    "model": "gpt-4-turbo-preview",  # 최신 모델 사용
    "temperature": 0.7,
    "max_tokens": 2048,
    "timeout": 30,
    "max_retries": 3,
    "cache_enabled": True,
    "cache_ttl": 3600,  # 1시간 캐시
}

# LangChain 설정
LANGCHAIN_CONFIG = {
    "verbose": False,
    "memory_key": "chat_history",
    "input_key": "input",
    "output_key": "output",
}

# AI 모델 contracts에서 import (PH12-001: symlink 호환 기본값)
from services.contracts.ai_request import AIRequest, AIResponse  # noqa: E402


class PromptTemplateManager:
    """
    프롬프트 템플릿 관리자 (Sequential Thinking Phase 1)
    """

    def __init__(self) -> None:
        self.templates: dict[str, PromptTemplate] = {}
        self._initialize_templates()

    def _initialize_templates(self) -> None:
        """기본 템플릿 초기화"""

        # 코드 분석 템플릿
        self.templates["code_analysis"] = PromptTemplate(
            input_variables=["code", "language", "task"],
            template="""다음 {language} 코드를 분석해주세요:

코드:
{code}

요청사항: {task}

분석 결과를 구조화된 형태로 제공해주세요:
1. 코드 개요
2. 주요 기능
3. 개선 제안
4. 잠재적 문제점
""",
        )

        # 문서 요약 템플릿
        self.templates["document_summary"] = PromptTemplate(
            input_variables=["document", "max_length"],
            template="""다음 문서를 {max_length}자 이내로 요약해주세요:

문서:
{document}

요약 시 다음 사항을 고려해주세요:
- 핵심 내용을 모두 포함
- 중요한 세부사항 유지
- 읽기 쉬운 형태로 작성
""",
        )

        # 코드 리뷰 템플릿
        self.templates["code_review"] = PromptTemplate(
            input_variables=["code", "context"],
            template="""다음 코드를 리뷰해주세요:

코드:
{code}

컨텍스트: {context}

다음 관점에서 리뷰해주세요:
1. 코드 품질 및 가독성
2. 잠재적 버그 및 보안 문제
3. 성능 및 최적화 기회
4. 모범 사례 준수 여부
5. 개선 제안
""",
        )

        # Trinity 분석 템플릿
        self.templates["trinity_analysis"] = PromptTemplate(
            input_variables=["subject", "context"],
            template="""眞善美孝永 5기둥 관점에서 다음 대상을 분석해주세요:

대상: {subject}
컨텍스트: {context}

각 기둥별 분석:
1. 眞 (Truth) - 기술적 정확성과 사실성
2. 善 (Goodness) - 윤리성, 안전성, 신뢰성
3. 美 (Beauty) - 구조적 우아함과 사용성
4. 孝 (Serenity) - 평온함과 유지보수성
5. 永 (Eternity) - 장기적 지속가능성

종합 평가를 Trinity Score (0-100)로 제시해주세요.
""",
        )

    def get_template(self, name: str) -> PromptTemplate | None:
        """템플릿 조회"""
        return self.templates.get(name)

    def add_template(self, name: str, template: PromptTemplate) -> None:
        """템플릿 추가"""
        self.templates[name] = template


class LangChainOpenAIService:
    """
    LangChain + OpenAI 통합 서비스
    Sequential Thinking: 단계별 AI 서비스 구현
    """

    def __init__(self) -> None:
        self.llm: Any = None  # Optional[ChatOpenAI], but using Any for compatibility
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exceptions=(Exception,),
            service_name="langchain_openai",
        )
        self.template_manager = PromptTemplateManager()
        self._initialized = False
        self._stats = {
            "requests": 0,
            "cache_hits": 0,
            "errors": 0,
            "total_tokens": 0,
        }

    async def initialize(self, api_key: str) -> bool:
        """
        서비스 초기화 (Sequential Thinking Phase 2)
        """
        try:
            # Phase 2.1: OpenAI 클라이언트 설정 (LangChain 1.2.0+ API)
            # model_name 파라미터 사용 (LangChain 버전에 따라 다름)
            llm_kwargs: dict[str, Any] = {
                "api_key": api_key,
                "temperature": OPENAI_CONFIG["temperature"],
                "max_tokens": OPENAI_CONFIG["max_tokens"],
                "timeout": OPENAI_CONFIG["timeout"],
            }
            # model_name 또는 model 파라미터 시도
            if hasattr(ChatOpenAI, "__init__"):
                try:
                    # model_name 시도
                    llm_kwargs["model_name"] = OPENAI_CONFIG["model"]
                except (TypeError, ValueError):
                    # model 시도
                    llm_kwargs["model"] = OPENAI_CONFIG["model"]
            self.llm = ChatOpenAI(**llm_kwargs)

            # Phase 2.2: 연결 테스트
            test_response = await self._call_openai("Hello", max_tokens=10)
            if not test_response:
                raise Exception("OpenAI 연결 테스트 실패")

            self._initialized = True
            logger.info("✅ LangChain + OpenAI 서비스 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"❌ LangChain + OpenAI 서비스 초기화 실패: {e}")
            return False

    async def process_request(self, request: AIRequest) -> AIResponse:
        """
        AI 요청 처리 (Sequential Thinking Phase 3)
        """
        if not self._initialized or not self.llm:
            raise Exception("서비스가 초기화되지 않았습니다")

        start_time = asyncio.get_event_loop().time()
        self._stats["requests"] += 1

        try:
            # Phase 3.1: 캐시 확인 (선택적)
            cache_key = None
            cached_response = None

            if request.use_cache and OPENAI_CONFIG["cache_enabled"]:
                cache_key = f"ai:{hash(request.prompt)}"
                cached_response = await cache_get(cache_key)

                if cached_response:
                    self._stats["cache_hits"] += 1
                    return AIResponse(
                        response=cached_response["response"],
                        usage=cached_response.get("usage", {}),
                        cached=True,
                        processing_time=asyncio.get_event_loop().time() - start_time,
                        model=str(OPENAI_CONFIG["model"]),
                    )

            # Phase 3.2: AI 요청 실행
            response_text = await self._call_openai(
                request.prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            if not response_text:
                raise Exception("AI 응답이 비어있습니다")

            # Phase 3.3: 응답 생성
            ai_response = AIResponse(
                response=response_text,
                usage={"estimated": len(response_text.split()) * 1.3},  # 대략적 추정
                cached=False,
                processing_time=asyncio.get_event_loop().time() - start_time,
                model=str(OPENAI_CONFIG["model"]),
            )

            # Phase 3.4: 캐시 저장 (선택적)
            if request.use_cache and OPENAI_CONFIG["cache_enabled"] and cache_key:
                cache_data = {
                    "response": response_text,
                    "usage": ai_response.usage,
                    "timestamp": asyncio.get_event_loop().time(),
                }
                cache_ttl: int | None = (
                    int(OPENAI_CONFIG["cache_ttl"])
                    if OPENAI_CONFIG.get("cache_ttl") is not None
                    and isinstance(OPENAI_CONFIG["cache_ttl"], (int, str, float))
                    else None
                )
                await cache_set(cache_key, cache_data, cache_ttl)

            return ai_response

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"AI 요청 처리 실패: {e}")
            raise

    async def analyze_code(self, code: str, language: str, task: str = "일반 분석") -> AIResponse:
        """
        코드 분석 (Sequential Thinking Phase 4)
        """
        template = self.template_manager.get_template("code_analysis")
        if not template:
            raise Exception("코드 분석 템플릿을 찾을 수 없습니다")

        prompt = template.format(code=code, language=language, task=task)
        request = AIRequest(prompt=prompt)

        return await self.process_request(request)

    async def summarize_document(self, document: str, max_length: int = 500) -> AIResponse:
        """
        문서 요약 (Sequential Thinking Phase 5)
        """
        template = self.template_manager.get_template("document_summary")
        if not template:
            raise Exception("문서 요약 템플릿을 찾을 수 없습니다")

        prompt = template.format(document=document, max_length=max_length)
        request = AIRequest(prompt=prompt)

        return await self.process_request(request)

    async def review_code(self, code: str, context: str = "") -> AIResponse:
        """
        코드 리뷰 (Sequential Thinking Phase 6)
        """
        template = self.template_manager.get_template("code_review")
        if not template:
            raise Exception("코드 리뷰 템플릿을 찾을 수 없습니다")

        prompt = template.format(code=code, context=context)
        request = AIRequest(prompt=prompt)

        return await self.process_request(request)

    async def analyze_trinity(self, subject: str, context: str = "") -> AIResponse:
        """
        Trinity 분석 (Sequential Thinking Phase 7)
        """
        template = self.template_manager.get_template("trinity_analysis")
        if not template:
            raise Exception("Trinity 분석 템플릿을 찾을 수 없습니다")

        prompt = template.format(subject=subject, context=context)
        request = AIRequest(prompt=prompt)

        return await self.process_request(request)

    async def get_stats(self) -> dict[str, Any]:
        """
        서비스 통계 조회 (Sequential Thinking Phase 8)
        """
        return {
            "service": "langchain_openai",
            "initialized": self._initialized,
            "model": OPENAI_CONFIG["model"],
            "stats": self._stats.copy(),
            "templates": list(self.template_manager.templates.keys()),
            "cache_enabled": OPENAI_CONFIG["cache_enabled"],
            "circuit_breaker_status": "active" if self.circuit_breaker else "inactive",
        }

    async def health_check(self) -> dict[str, Any]:
        """
        건강 상태 점검 (Sequential Thinking Phase 9)
        """
        health_status: dict[str, Any] = {
            "service": "langchain_openai",
            "status": "unknown",
            "details": {},
            "timestamp": asyncio.get_event_loop().time(),
        }
        details: dict[str, Any] = health_status["details"]

        try:
            # Phase 9.1: 초기화 상태 확인
            details["initialized"] = self._initialized

            if self._initialized and self.llm:
                # Phase 9.2: AI 연결 테스트
                test_response = await self._call_openai("Health check", max_tokens=5)
                details["ai_connection"] = "healthy" if test_response else "unhealthy"

                # Phase 9.3: 캐시 연결 테스트
                if OPENAI_CONFIG["cache_enabled"]:
                    cache_test = await cache_set("health_test", {"test": True}, ttl=10)
                    details["cache_connection"] = "healthy" if cache_test else "unhealthy"
                else:
                    details["cache_connection"] = "disabled"

                # Phase 9.4: 종합 상태 판정
                if details["ai_connection"] == "healthy":
                    health_status["status"] = "healthy"
                else:
                    health_status["status"] = "degraded"

                # Phase 9.5: 성능 메트릭 추가
                health_status["details"]["stats"] = await self.get_stats()

            else:
                health_status["status"] = "unhealthy"
                health_status["details"]["error"] = "서비스가 초기화되지 않았습니다"

        except Exception as e:
            logger.error(f"건강 상태 점검 실패: {e}")
            health_status["status"] = "error"
            health_status["details"]["error"] = str(e)

        return health_status

    async def _call_openai(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str | None:
        """
        OpenAI API 직접 호출 (내부 메서드)
        LangChain 1.2.0+ API 사용
        """
        if not self.llm:
            return None

        try:
            # Circuit Breaker 적용 (call 메서드 사용)
            async def _invoke_llm():
                # LangChain 1.2.0+ API: ChatOpenAI.ainvoke 사용
                if LANGCHAIN_NEW_API:
                    # ChatOpenAI는 HumanMessage를 받음
                    from langchain_core.messages import HumanMessage

                    messages = [HumanMessage(content=prompt)]

                    # 온도 및 max_tokens 설정
                    if temperature is not None:
                        self.llm.temperature = temperature
                    if max_tokens is not None:
                        self.llm.max_tokens = max_tokens

                    # 재시도 로직 적용
                    max_retries_val: int = int(OPENAI_CONFIG["max_retries"])
                    response = await exponential_backoff(
                        lambda: self.llm.ainvoke(messages),
                        max_retries=max_retries_val,
                        base_delay=1.0,
                    )

                    if response and hasattr(response, "content"):
                        return response.content.strip()
                    elif response:
                        return str(response).strip()
                else:
                    # 구버전 API (fallback)
                    call_params = {
                        "prompt": prompt,
                        "temperature": temperature or OPENAI_CONFIG["temperature"],
                        "max_tokens": max_tokens or OPENAI_CONFIG["max_tokens"],
                    }

                    max_retries_val_legacy: int = int(OPENAI_CONFIG["max_retries"])
                    response = await exponential_backoff(
                        lambda: self.llm.agenerate([call_params]),
                        max_retries=max_retries_val_legacy,
                        base_delay=1.0,
                    )

                    if response and response.generations:
                        return response.generations[0][0].text.strip()

                return None

            return await self.circuit_breaker.call(_invoke_llm)

        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {e}")
            raise


# 전역 인스턴스
langchain_openai_service = LangChainOpenAIService()


async def get_ai_service() -> LangChainOpenAIService:
    """AI 서비스 인스턴스 반환"""
    return langchain_openai_service


async def initialize_ai_service(api_key: str) -> bool:
    """AI 서비스 초기화"""
    return await langchain_openai_service.initialize(api_key)


# 편의 함수들
async def analyze_code_ai(code: str, language: str, task: str = "일반 분석") -> AIResponse:
    """코드 분석 편의 함수"""
    return await langchain_openai_service.analyze_code(code, language, task)


async def summarize_document_ai(document: str, max_length: int = 500) -> AIResponse:
    """문서 요약 편의 함수"""
    return await langchain_openai_service.summarize_document(document, max_length)


async def review_code_ai(code: str, context: str = "") -> AIResponse:
    """코드 리뷰 편의 함수"""
    return await langchain_openai_service.review_code(code, context)


async def analyze_trinity_ai(subject: str, context: str = "") -> AIResponse:
    """Trinity 분석 편의 함수"""
    return await langchain_openai_service.analyze_trinity(subject, context)


async def get_ai_stats() -> dict[str, Any]:
    """AI 서비스 통계 조회 편의 함수"""
    return await langchain_openai_service.get_stats()
