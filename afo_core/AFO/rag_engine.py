import logging
from typing import Any

from AFO.llm_router import route_and_execute
from utils.embedding import get_embedding
from utils.vector_store import get_vector_store, query_vector_store

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    AFO Kingdom RAG Engine (眞 - Tech Purity)
    Orchestrates: Query -> Embedding -> Vector Search -> LLM Generation
    """

    @staticmethod
    async def execute(
        query: str, top_k: int = 3, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        RAG 파이프라인 전체 실행
        """
        try:
            # 0. Vector Store 차원 확인
            store = get_vector_store()
            target_dim = 1536  # 기본값
            if hasattr(store, "embed_dim") and store.embed_dim:
                target_dim = store.embed_dim

            # 1. Embedding 생성 (차원 맞춤)
            embedding = await get_embedding(query, target_dim=target_dim)

            if not embedding:
                return {
                    "response": "임베딩 생성에 실패했습니다.",
                    "confidence": 0.0,
                    "sources": [],
                    "enhancement": "Embedding Generation Failed",
                }

            # 2. Vector Store 검색 (LanceDB)
            search_results = query_vector_store(embedding, top_k=top_k)

            if not search_results:
                logger.warning(f"RAG: No relevant documents found for query: {query[:50]}...")
                return {
                    "response": "관련된 서고 기록을 찾지 못했습니다.",
                    "confidence": 0.0,
                    "sources": [],
                    "enhancement": "Local Knowledge No-hit",
                }

            # 3. Context 구성
            context_text = "\n\n".join([r["content"] for r in search_results])
            sources = [r["source"] for r in search_results]

            # 4. LLM 최종 응답 생성 (LLM Router 활용)
            prompt = (
                "당신은 AFO 왕국의 지혜로운 책사입니다. 다음 서고 기록(Context)을 바탕으로 사령관의 질문에 답하세요.\n"
                "기록에 없는 내용은 억지로 꾸며내지 마십시오.\n\n"
                f"[서고 기록]\n{context_text}\n\n"
                f"[질문]\n{query}\n\n"
                "[책사의 답변]"
            )

            llm_result = await route_and_execute(prompt, context=context)

            return {
                "response": llm_result.get("response", "답변 생성 실패"),
                "confidence": (
                    sum(r["score"] for r in search_results) / len(search_results)
                    if search_results
                    else 0
                ),
                "sources": list(set(sources)),
                "enhancement": "Retrieved from LanceDB Royal Library",
            }

        except Exception as e:
            logger.error(f"RAG Engine 실행 오류: {e}")
            raise


rag_engine = RAGEngine()
