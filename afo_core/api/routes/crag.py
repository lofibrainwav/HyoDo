from __future__ import annotations

import logging
import os
import re
import time
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException
from langchain_community.tools import TavilySearchResults
from langsmith import traceable
from pydantic import BaseModel

from AFO.config.settings import get_settings
from AFO.llm_router import LLMRouter

if TYPE_CHECKING:
    from collections.abc import Callable

# Trinity Score: 90.0 (Established by Chancellor)
# 🛡️ CRAG Self-Correction API Router
# 眞善美孝: Truth 95%, Goodness 90%, Beauty 85%, Serenity 100%
# CRAG = Corrective RAG: 문서 채점 + 필요시 웹 검색 fallback
# Phase 5: LangSmith Tracing 통합


logger = logging.getLogger("crag")

# LangSmith tracing (optional)
try:
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False

    # Fallback: no-op decorator
    def traceable(name: str | None = None) -> Callable[[Callable], Callable]:  # type: ignore[no-redef]
        def decorator(func: Callable) -> Callable:
            return func

        return decorator


# AFO LLM Router 사용 (Ollama → Gemini → Claude → OpenAI fallback)
try:
    LLM_ROUTER_AVAILABLE = True
    llm_router: LLMRouter | None = LLMRouter()
    print("✅ CRAG: AFO LLM Router 초기화 완료 (Ollama → Gemini → Claude → OpenAI)")
except ImportError as e:
    LLM_ROUTER_AVAILABLE = False
    llm_router = None
    print(f"⚠️  CRAG: LLM Router 사용 불가 ({e})")

# Tavily 웹 검색 (선택사항)
try:
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("⚠️  tavily-python not available, web fallback disabled")

router = APIRouter(prefix="/api/crag", tags=["CRAG"])

# Web search 설정 (Phase 2-4: settings 사용)
web_search = None

if TAVILY_AVAILABLE:
    # Phase 2-4: settings 사용
    try:
        settings = get_settings()
        tavily_key = settings.TAVILY_API_KEY
    except ImportError:
        tavily_key = os.getenv("TAVILY_API_KEY")

    if tavily_key:
        try:
            web_search = TavilySearchResults(max_results=3, api_key=tavily_key)
            print("✅ CRAG: Tavily 웹 검색 초기화 완료")
        except Exception as e:
            print(f"⚠️  CRAG: Tavily 초기화 실패: {e}")
    else:
        print("⚠️  CRAG: TAVILY_API_KEY 환경변수 없음 (웹 fallback 비활성화)")


class CragRequest(BaseModel):
    """CRAG 요청 모델"""

    question: str
    documents: list[str] = []  # n8n에서 RAG로 가져온 문서들 (MVP에서는 빈 리스트 가능)


class CragResponse(BaseModel):
    """CRAG 응답 모델"""

    answer: str
    graded_docs: dict[str, float]  # {doc: score (0-1)}
    used_web_fallback: bool


@traceable(name="crag_grade_documents")
async def grade_documents(question: str, documents: list[str]) -> dict[str, float]:
    """
    간단한 CRAG 문서 점수 매기기 (0~1).

    LangSmith tracing: crag_grade_documents
    AFO LLM Router 사용 (Ollama → Gemini → Claude → OpenAI)

    Args:
        question: 사용자 질문
        documents: 검색된 문서 리스트

    Returns:
        {doc: score} 딕셔너리
    """
    scores: dict[str, float] = {}

    if not documents or not llm_router:
        return scores

    for doc in documents:
        prompt = (
            "You are a strict relevance grader.\n"
            "Return ONLY one decimal number between 0 and 1.\n\n"
            f"Question: {question}\n"
            f"Document:\n{doc}\n"
        )
        try:
            # AFO LLM Router를 사용하여 답변 생성
            result = await llm_router.execute_with_routing(
                query=prompt,
                context={
                    "task": "relevance_grading",
                    "question": question,
                    "document": doc[:500],
                },
            )

            # 응답에서 숫자 추출
            response_text = result.get("response", "").strip()
            if not response_text:
                scores[doc] = 0.0
                continue

            # 응답에서 첫 번째 숫자만 float으로 파싱
            try:
                # 숫자 패턴 찾기 (0.0 ~ 1.0)

                numbers = re.findall(r"\b0?\.\d+|\b1\.0|\b0\.0|\b1\b", response_text)
                value = float(numbers[0]) if numbers else float(response_text.split()[0])
            except (ValueError, IndexError):
                value = 0.0
            value = max(0.0, min(1.0, value))  # 0-1 범위로 클램핑
            scores[doc] = value
        except Exception as e:
            logger.warning(f"문서 채점 실패: {e}")
            scores[doc] = 0.0

    return scores


@traceable(name="crag_web_fallback")
def perform_web_fallback(question: str) -> list[str]:
    """
    Tavily 웹 검색 fallback 수행.

    LangSmith tracing: crag_web_fallback

    Args:
        question: 사용자 질문

    Returns:
        검색된 문서 리스트
    """
    if web_search is None:
        return []

    try:
        search_results = web_search.run(question)
        docs: list[str] = []

        if isinstance(search_results, list):
            for item in search_results:
                content = item.get("content") or item.get("text")
                if content:
                    docs.append(content)
        elif isinstance(search_results, str):
            docs.append(search_results)

        return docs
    except Exception as e:
        logger.warning(f"웹 검색 fallback 실패: {e}")
        return []


@traceable(name="crag_generate_answer")
async def generate_answer(question: str, context: str) -> str:
    """
    컨텍스트 기반 최종 답변 생성.

    LangSmith tracing: crag_generate_answer
    AFO LLM Router 사용 (Ollama → Gemini → Claude → OpenAI)

    Args:
        question: 사용자 질문
        context: 컨텍스트 문서

    Returns:
        생성된 답변
    """
    if not llm_router:
        return "CRAG LLM Router not available. Please check AFO LLM Router configuration."

    answer_prompt = (
        "You are an assistant that answers using the context when possible.\n"
        "If the context does not contain the answer, say you do not know instead of guessing.\n\n"
        f"Question: {question}\n\n"
    )

    if context:
        answer_prompt += f"Context:\n{context}\n\n"
    else:
        answer_prompt += "Context: No context available.\n\n"

    answer_prompt += "Answer:"

    try:
        # AFO LLM Router를 사용하여 답변 생성
        result = await llm_router.execute_with_routing(
            query=answer_prompt,
            context={
                "task": "answer_generation",
                "question": question,
                "has_context": bool(context),
                "context_length": len(context) if context else 0,
            },
        )

        answer_text = str(result.get("response", "")).strip()

        if not answer_text:
            answer_text = "I could not generate an answer. Please try rephrasing your question."

        return answer_text
    except Exception as e:
        logger.error(f"답변 생성 실패: {e}", exc_info=True)
        return f"Error generating answer: {e!s}"


@traceable(name="crag_pipeline_entry")
@router.post("", response_model=CragResponse)
async def crag_endpoint(payload: CragRequest) -> CragResponse:
    """
    CRAG 메인 엔드포인트: 문서 채점 + 필요하면 웹 검색 fallback + 최종 답변.

    LangSmith tracing: crag_pipeline_entry (전체 파이프라인)

    Flow:
    1. 문서 채점 (grade_documents) → crag_grade_documents
    2. 최고 점수 < 0.7이면 Tavily 웹 검색으로 보강 → crag_web_fallback
    3. 컨텍스트 합쳐서 LLM으로 최종 답변 생성 → crag_generate_answer

    KPI 로깅:
    - best_score: 최고 문서 점수
    - used_web_fallback: 웹 검색 사용 여부
    - latency_ms: 전체 처리 시간
    """
    start_time = time.time()
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    if not llm_router:
        raise HTTPException(
            status_code=503,
            detail="CRAG LLM Router not available. Please check AFO LLM Router configuration.",
        )

    # 1) 문서 채점 (traced: crag_grade_documents) - async로 변경
    graded_docs = await grade_documents(question, payload.documents)
    best_score = max(graded_docs.values()) if graded_docs else 0.0

    # 2) 필요하면 Tavily 웹 검색으로 보강 (traced: crag_web_fallback)
    used_web_fallback = False
    combined_docs: list[str] = list(payload.documents)

    if (not graded_docs or best_score < 0.7) and web_search is not None:
        used_web_fallback = True
        fallback_docs = perform_web_fallback(question)
        combined_docs.extend(fallback_docs)

    context = "\n\n---\n\n".join(combined_docs) if combined_docs else ""

    # 3) 최종 답변 생성 (traced: crag_generate_answer) - async로 변경
    answer_text = await generate_answer(question, context)

    # KPI 로깅 (眞善美孝: Truth 측정)
    elapsed_ms = int((time.time() - start_time) * 1000)
    avg_score = sum(graded_docs.values()) / len(graded_docs) if graded_docs else 0.0

    logger.info(
        "CRAG question=%r best_score=%.2f avg_score=%.2f used_web_fallback=%s latency_ms=%d doc_count=%d",
        question[:80],  # 질문 앞 80자만 로그
        best_score,
        avg_score,
        used_web_fallback,
        elapsed_ms,
        len(payload.documents),
    )

    return CragResponse(
        answer=answer_text,
        graded_docs=graded_docs,
        used_web_fallback=used_web_fallback,
    )
