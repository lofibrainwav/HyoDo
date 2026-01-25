from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langgraph.graph import END, StateGraph
from qdrant_client import QdrantClient
from typing_extensions import TypedDict

from config import EMBEDDING_MODEL, LLM_MODEL, QDRANT_COLLECTION_NAME, QDRANT_URL

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
# mypy: ignore-errors
"""LangGraph를 사용한 RAG 파이프라인
옵시디언 vault 기반 질의응답 시스템
"""


# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))


class GraphState(TypedDict):
    """Graph 상태"""

    question: str
    context: list[str]
    answer: str
    generation: str


def retrieve_documents(state: GraphState) -> GraphState:
    """문서 검색"""
    question = state["question"]

    # Qdrant에서 유사 문서 검색
    client = QdrantClient(url=QDRANT_URL)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    vectorstore = Qdrant(
        client=client,
        collection_name=QDRANT_COLLECTION_NAME,
        embeddings=embeddings,
    )

    # 유사 문서 검색 (상위 5개)
    docs = vectorstore.similarity_search(question, k=5)

    # 컨텍스트 추출
    context = [doc.page_content for doc in docs]
    metadata = [doc.metadata for doc in docs]

    return {
        **state,
        "context": context,
        "metadata": metadata,
    }


def generate_answer(state: GraphState) -> GraphState:
    """답변 생성"""
    question = state["question"]
    context = "\n\n".join(state["context"])

    # 프롬프트 구성
    prompt = f"""다음 컨텍스트를 기반으로 질문에 답변하세요.

컨텍스트:
{context}

질문: {question}

답변:"""

    # LLM 호출
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        **state,
        "answer": response.content,
        "generation": response.content,
    }


def should_continue(state: GraphState) -> Literal["generate", "end"]:
    """다음 단계 결정"""
    if state.get("context"):
        return "generate"
    return "end"


def create_rag_graph() -> StateGraph:
    """RAG Graph 생성"""
    workflow = StateGraph(GraphState)

    # 노드 추가
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("generate", generate_answer)

    # 엣지 추가
    workflow.set_entry_point("retrieve")
    workflow.add_conditional_edges(
        "retrieve",
        should_continue,
        {
            "generate": "generate",
            "end": END,
        },
    )
    workflow.add_edge("generate", END)

    return workflow.compile()


def query_obsidian_vault(question: str) -> dict:
    """옵시디언 vault에 질의

    Args:
        question: 질문

    Returns:
        답변 및 메타데이터

    """
    graph = create_rag_graph()

    # 초기 상태
    initial_state = {
        "question": question,
        "context": [],
        "answer": "",
        "generation": "",
    }

    # Graph 실행
    result = graph.invoke(initial_state)

    return {
        "question": result["question"],
        "answer": result["answer"],
        "context_sources": result.get("metadata", []),
    }


def main() -> None:
    """테스트"""
    print("🔍 옵시디언 vault RAG 시스템 테스트\n")

    # 테스트 질문
    questions = [
        "옵시디언 플러그인 최적화 결과는?",
        "Trinity 점수는 무엇인가?",
        "서비스 최적화에서 제거된 플러그인은?",
    ]

    for question in questions:
        print(f"❓ 질문: {question}")
        result = query_obsidian_vault(question)
        print(f"💡 답변: {result['answer']}")
        print(f"📚 참고 문서: {len(result['context_sources'])}개")
        print()


if __name__ == "__main__":
    main()
