from __future__ import annotations

import os
import traceback
from typing import Any, Literal, Optional, TypedDict, Union

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

# Trinity Score: 90.0 (Established by Chancellor)
# ⚔️ 점수는 Truth Engine (scripts/calculate_trinity_score.py)에서만 계산됩니다.
# LLM은 consult_the_lens MCP 도구를 통해 점수를 확인하세요.
# 이 파일은 AFO 왕국의 眞善美孝 철학을 구현합니다

"""AFO Kingdom - CRAG LangGraph Implementation
제갈량의 전략, 영덕의 실행

CRAG = LangGraph 상태 그래프로 구현한 버전
- 시각화 가능
- 워크플로우 명확
- 단계별 추적 가능

구조:
START → retrieve → grade → [route] → (web_search) → generate → END
                              ↓
                            generate

철학: 眞善美孝
- 眞 (Truth): 상태 그래프로 흐름 증명
- 善 (Goodness): 시각화로 이해 쉬움
- 美 (Beauty): 그래프 구조의 아름다움
- 孝 (Serenity): 형님이 워크플로우 한눈에 파악
"""


# 환경 변수
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


class GraphState(TypedDict):
    """CRAG 그래프 상태

    초등학생: 로봇 놀이에서 기억할 것들
    - question: 질문
    - documents: 찾은 책들
    - web_search: 웹 검색 필요? ("Yes" or "No")
    - generation: 최종 답변
    """

    question: str
    documents: list[Document]
    web_search: str
    generation: str


class CRAGLangGraph:
    """LangGraph 기반 CRAG 엔진

    제갈량의 전략: 상태 그래프로 워크플로우 시각화
    영덕의 실행: 실제 작동하는 코드

    사용법:
        crag = CRAGLangGraph()
        result = crag.query("What is CRAG?")
    """

    def __init__(
        self,
        vectorstore=None,
        llm_model: str = "gpt-3.5-turbo",
        grade_threshold: float = 0.5,
    ):
        """초기화

        Args:
            vectorstore: 벡터 DB (없으면 더미 사용)
            llm_model: LLM 모델 이름
            grade_threshold: 평가 임계값 (0.5 = 50%)

        """
        self.vectorstore = vectorstore
        self.llm = ChatOpenAI(model=llm_model, temperature=0, api_key=OPENAI_API_KEY)
        self.grade_threshold = grade_threshold

        # Tavily 웹 검색 (API 키 있을 때만)
        self.web_search_tool: TavilySearchResults | None
        if TAVILY_API_KEY:
            self.web_search_tool = TavilySearchResults(k=3)
        else:
            self.web_search_tool = None

        # 그래프 빌드
        self.app = self._build_graph()

        # 통계
        self.stats = {
            "total_queries": 0,
            "web_searches": 0,
            "local_only": 0,
        }

    def _build_graph(self) -> Any:
        """CRAG 워크플로우 그래프 빌드

        초등학생: 로봇 놀이 순서 정하기
        """
        workflow = StateGraph(GraphState)

        # 노드 추가 (각 단계)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("grade_documents", self._grade_documents)
        workflow.add_node("web_search", self._web_search)
        workflow.add_node("generate", self._generate)

        # 엣지 추가 (흐름)
        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "grade_documents")

        # 조건부 엣지 (라우팅)
        workflow.add_conditional_edges(
            "grade_documents",
            self._route_decision,
            {"web_search": "web_search", "generate": "generate"},
        )

        workflow.add_edge("web_search", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()

    def _retrieve(self, state: GraphState) -> GraphState:
        """1단계: 검색 (Retrieve)

        초등학생: 책장에서 책 찾아와
        """
        question = state["question"]

        print(f"📚 [Retrieve] 질문: {question}")

        if self.vectorstore:
            # 실제 벡터스토어 검색
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            documents = retriever.invoke(question)
        else:
            # 더미 문서 (테스트용)
            documents = [
                Document(
                    page_content="CRAG (Corrective RAG) is an improved RAG system that evaluates retrieved documents.",
                    metadata={"source": "mock_db"},
                ),
                Document(
                    page_content="RAG retrieves documents to improve LLM answers.",
                    metadata={"source": "mock_db"},
                ),
                Document(
                    page_content="Unrelated content about Python programming.",
                    metadata={"source": "mock_db"},
                ),
            ]

        print(f"  ✅ 찾은 문서: {len(documents)}개")

        return {
            "question": question,
            "documents": documents,
            "web_search": "No",
            "generation": "",
        }

    def _grade_documents(self, state: GraphState) -> GraphState:
        """2단계: 평가 (Grade)

        초등학생: 각 책 읽고 "관련 있어?" 확인
        """
        question = state["question"]
        documents = state["documents"]

        print("📖 [Grade] 문서 평가 시작...")

        # 평가 프롬프트
        grade_prompt = ChatPromptTemplate.from_template(
            """질문: {question}
문서: {document}

이 문서가 질문에 답하는 데 관련이 있습니까?

"yes" 또는 "no"로만 답하세요."""
        )

        filtered_docs = []
        relevant_count = 0

        for i, doc in enumerate(documents):
            # LLM으로 관련성 평가
            chain = grade_prompt | self.llm | StrOutputParser()
            score = chain.invoke({"question": question, "document": doc.page_content[:500]})

            is_relevant = "yes" in score.lower()

            if is_relevant:
                filtered_docs.append(doc)
                relevant_count += 1
                print(f"  📖 문서 {i + 1}: ✅ 관련 있음")
            else:
                print(f"  📖 문서 {i + 1}: ❌ 관련 없음")

        # 웹 검색 필요 여부 판단
        relevance_ratio = relevant_count / len(documents) if documents else 0
        web_search = "Yes" if relevance_ratio < self.grade_threshold else "No"

        print(f"  📊 관련 문서 비율: {relevance_ratio:.2%} (임계값: {self.grade_threshold:.0%})")
        print(f"  🔍 웹 검색 필요: {web_search}")

        return {
            "question": question,
            "documents": filtered_docs,
            "web_search": web_search,
            "generation": "",
        }

    def _route_decision(self, state: GraphState) -> Literal["web_search", "generate"]:
        """3단계: 라우팅 결정 (Route)

        초등학생: 책 충분해? → 바로 답 / 부족해? → 인터넷 검색
        """
        web_search = state["web_search"]

        if web_search == "Yes":
            print("🌐 [Route] 웹 검색으로 이동")
            return "web_search"
        else:
            print("✅ [Route] 바로 답변 생성")
            return "generate"

    def _web_search(self, state: GraphState) -> GraphState:
        """4단계: 웹 검색 (Web Search)

        초등학생: 인터넷에서 최신 정보 찾아와
        """
        question = state["question"]
        documents = state["documents"]

        print("🌐 [Web Search] Tavily 검색 중...")

        if self.web_search_tool:
            try:
                # Tavily 검색
                search_results = self.web_search_tool.invoke(question)

                # 결과를 Document로 변환
                for result in search_results:
                    web_doc = Document(
                        page_content=result["content"],
                        metadata={"source": "web_search", "url": result.get("url", "")},
                    )
                    documents.append(web_doc)

                print(f"  ✅ 웹 검색 완료: {len(search_results)}개 결과 추가")
                self.stats["web_searches"] += 1

            except Exception as e:
                print(f"  ❌ 웹 검색 실패: {e}")
        else:
            # Tavily API 키 없으면 더미 결과
            dummy_doc = Document(
                page_content=f"Mock web search result for: {question}. CRAG uses web search to correct retrieval errors.",
                metadata={"source": "mock_web"},
            )
            documents.append(dummy_doc)
            print("  ⚠️  Tavily API 키 없음 - 더미 웹 검색 결과 사용")

        return {
            "question": question,
            "documents": documents,
            "web_search": "Yes",
            "generation": "",
        }

    def _generate(self, state: GraphState) -> GraphState:
        """5단계: 답변 생성 (Generate)

        초등학생: 좋은 책으로 답 만들어
        """
        question = state["question"]
        documents = state["documents"]

        print("💡 [Generate] 답변 생성 중...")

        if not documents:
            generation = "죄송합니다. 관련 정보를 찾을 수 없습니다."
        else:
            # 문서 내용 합치기
            context = "\n\n".join(
                [f"문서 {i + 1}: {doc.page_content}" for i, doc in enumerate(documents)]
            )

            # 생성 프롬프트
            generation_prompt = ChatPromptTemplate.from_template(
                """다음 문서들을 참고하여 질문에 답하세요.

문서:
{context}

질문: {question}

답변:"""
            )

            chain = generation_prompt | self.llm | StrOutputParser()
            generation = chain.invoke({"context": context, "question": question})

        print(f"  ✅ 답변 생성 완료 ({len(generation)} 글자)")

        return {
            "question": question,
            "documents": documents,
            "web_search": state["web_search"],
            "generation": generation,
        }

    def query(self, question: str) -> dict:
        """CRAG 쿼리 실행

        초등학생: 질문 받으면 로봇 놀이 시작!

        Args:
            question: 질문

        Returns:
            {
                "answer": "답변...",
                "web_search_used": True/False,
                "num_documents": 3,
                "stats": {...}
            }

        """
        print(f"\n{'=' * 60}")
        print(f"🤖 CRAG (LangGraph) 질문: {question}")
        print(f"{'=' * 60}")

        # 그래프 실행
        inputs = {"question": question}
        result = self.app.invoke(inputs)

        # 통계 업데이트
        self.stats["total_queries"] += 1
        if result["web_search"] == "Yes":
            self.stats["web_searches"] += 1
        else:
            self.stats["local_only"] += 1

        print("\n✅ CRAG 완료!")
        print(f"{'=' * 60}\n")

        return {
            "answer": result["generation"],
            "web_search_used": result["web_search"] == "Yes",
            "num_documents": len(result["documents"]),
            "stats": self.stats.copy(),
        }


def test_crag_langgraph() -> None:
    """LangGraph CRAG 테스트

    초등학생: 로봇 놀이 테스트해봐
    """
    print("\n" + "=" * 60)
    print("🧪 CRAG (LangGraph) 테스트 시작")
    print("=" * 60)

    # API 키 체크
    if not OPENAI_API_KEY:
        print("⚠️  경고: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY=your-key-here 추가하세요.\n")
        return False

    try:
        # CRAG 엔진 생성
        crag = CRAGLangGraph(
            vectorstore=None,  # 더미 모드
            grade_threshold=0.5,  # 50% 이하면 웹 검색
        )

        # 테스트 쿼리
        test_queries = [
            "What is CRAG?",  # 좋은 질문 (로컬 문서 충분)
            "Who invented quantum computing?",  # 나쁜 질문 (로컬 문서 부족)
        ]

        for query in test_queries:
            result = crag.query(query)

            print("\n결과:")
            print(f"  답변: {result['answer'][:100]}...")
            print(f"  웹 검색 사용: {'✅ Yes' if result['web_search_used'] else '❌ No'}")
            print(f"  사용 문서 수: {result['num_documents']}")

        print("\n📊 전체 통계:")
        print(f"  총 질문: {crag.stats['total_queries']}")
        print(f"  로컬만 사용: {crag.stats['local_only']}")
        print(f"  웹 검색 사용: {crag.stats['web_searches']}")

        return True

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_crag_langgraph()

    if success:
        print("\n✅ CRAG (LangGraph) 엔진 테스트 완료!")
        print("제갈량의 전략(LangGraph)을 영덕이 코드로 만들었습니다.")
    else:
        print("\n❌ CRAG (LangGraph) 엔진 테스트 실패")
        print("환경 설정(API 키, 라이브러리)을 확인하세요.")
