from __future__ import annotations

import os

from langchain.document_loaders import TextLoader
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Trinity Score: 90.0 (Established by Chancellor)
# ⚔️ 점수는 Truth Engine (scripts/calculate_trinity_score.py)에서만 계산됩니다.
# LLM은 consult_the_lens MCP 도구를 통해 점수를 확인하세요.
# 이 파일은 AFO 왕국의 眞善美孝 철학을 구현합니다

#!/usr/bin/env python3
"""주유 책사 제안: Advanced RetrievalQA
프롬프트 템플릿 + Chain Type + Source Documents
"""


def main() -> None:
    print("=" * 70)
    print("주유 책사 제안: Advanced RetrievalQA")
    print("=" * 70)
    print()

    # OpenAI API Key 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   export OPENAI_API_KEY='your-key-here'")
        print()
        print("📚 DRY RUN 모드: 구조만 표시합니다.\n")
        show_structure()
        return

    # LLM 초기화
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    embeddings = OpenAIEmbeddings()

    # 샘플 문서 준비
    print("=" * 70)
    print("문서 준비 및 벡터 스토어 생성")
    print("=" * 70)
    print()

    sample_docs = """
    AFO Ultimate는 다중 컴포넌트 자동화 및 워크플로우 관리 플랫폼입니다.
    AFO Soul Engine은 Python 기반 음악 분석 및 AI 에이전트 오케스트레이션 시스템입니다.
    MCP Frontend는 React TypeScript 대시보드로 n8n 워크플로우 모니터링을 제공합니다.
    N8N Custom Nodes는 n8n-MCP 통합 패키지로 AI 어시스턴트에게 n8n 노드 문서를 제공합니다.
    LangChain은 47개 노드로 Memory, Retriever, Chain 기능을 제공합니다.
    """

    with open("/tmp/afo_docs.txt", "w") as f:
        f.write(sample_docs)

    print("1️⃣ 문서 로드 및 분할...")
    loader = TextLoader("/tmp/afo_docs.txt")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200, chunk_overlap=50, separators=["\n\n", "\n", ". ", " ", ""]
    )
    texts = splitter.split_documents(docs)
    print(f"   ✓ {len(texts)}개 청크로 분할 완료\n")

    print("2️⃣ FAISS 벡터 스토어 생성...")
    vectorstore = FAISS.from_documents(texts, embeddings)
    print("   ✓ 벡터 스토어 생성 완료\n")

    # 예제 1: 기본 RetrievalQA
    print("=" * 70)
    print("예제 1: 기본 RetrievalQA (Stuff Chain)")
    print("=" * 70)
    print()

    qa_basic = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),
        return_source_documents=True,
    )

    query1 = "AFO Ultimate는 무엇인가요?"
    print(f"👤 질문: {query1}")
    result1 = qa_basic({"query": query1})
    print(f"🤖 답변: {result1['result']}")
    print(f"📄 소스: {len(result1['source_documents'])}개 문서 참조\n")

    # 예제 2: 커스텀 프롬프트 RetrievalQA
    print("=" * 70)
    print("예제 2: 커스텀 프롬프트 RetrievalQA")
    print("=" * 70)
    print()

    custom_prompt_template = """다음 컨텍스트를 사용하여 질문에 한국어로 답변하세요.
    답변은 간결하고 명확하게 작성하세요.
    답을 모르면 "문서에 해당 정보가 없습니다"라고 답하세요.

    컨텍스트:
    {context}

    질문: {question}
    답변:"""

    CUSTOM_PROMPT = PromptTemplate(
        template=custom_prompt_template, input_variables=["context", "question"]
    )

    qa_custom = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": CUSTOM_PROMPT},
    )

    query2 = "LangChain은 몇 개의 노드를 제공하나요?"
    print(f"👤 질문: {query2}")
    result2 = qa_custom({"query": query2})
    print(f"🤖 답변: {result2['result']}")
    print(f"📄 소스: {len(result2['source_documents'])}개 문서 참조")
    print("   참조 문서:")
    for i, doc in enumerate(result2["source_documents"][:2], 1):
        preview = doc.page_content[:100].replace("\n", " ")
        print(f"   [{i}] {preview}...")
    print()

    # 예제 3: Map-Reduce Chain (긴 문서용)
    print("=" * 70)
    print("예제 3: Map-Reduce Chain (긴 문서 요약)")
    print("=" * 70)
    print()

    qa_mapreduce = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="map_reduce",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        return_source_documents=True,
    )

    query3 = "AFO Ultimate의 주요 컴포넌트들을 설명해주세요."
    print(f"👤 질문: {query3}")
    result3 = qa_mapreduce({"query": query3})
    print(f"🤖 답변: {result3['result']}")
    print(f"📄 소스: {len(result3['source_documents'])}개 문서 참조\n")

    print("💡 Map-Reduce 특징:")
    print("   • 각 문서를 개별적으로 처리 (Map)")
    print("   • 결과를 종합하여 최종 답변 생성 (Reduce)")
    print("   • 긴 문서나 많은 컨텍스트 처리에 적합\n")

    # 예제 4: Refine Chain (정교한 답변)
    print("=" * 70)
    print("예제 4: Refine Chain (순차적 정제)")
    print("=" * 70)
    print()

    qa_refine = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="refine",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
    )

    query4 = "n8n과 LangChain의 관계는 무엇인가요?"
    print(f"👤 질문: {query4}")
    result4 = qa_refine({"query": query4})
    print(f"🤖 답변: {result4['result']}")
    print(f"📄 소스: {len(result4['source_documents'])}개 문서 참조\n")

    print("💡 Refine 특징:")
    print("   • 첫 문서로 초기 답변 생성")
    print("   • 이후 문서들로 답변을 순차적으로 정제")
    print("   • 정교하고 상세한 답변 생성\n")

    # Chain Type 비교
    print("=" * 70)
    print("Chain Type 비교 요약")
    print("=" * 70)
    print()
    print("┌─────────────┬──────────────────────┬──────────────────────┐")
    print("│ Chain Type  │ 장점                 │ 적합한 경우          │")
    print("├─────────────┼──────────────────────┼──────────────────────┤")
    print("│ stuff       │ 빠름, 간단           │ 짧은 컨텍스트        │")
    print("│ map_reduce  │ 병렬 처리, 확장성    │ 긴 문서, 많은 청크   │")
    print("│ refine      │ 정교한 답변          │ 상세한 분석 필요     │")
    print("│ map_rerank  │ 최적 답변 선택       │ 명확한 답변 필요     │")
    print("└─────────────┴──────────────────────┴──────────────────────┘")
    print()

    print("=" * 70)
    print("✓ Advanced RetrievalQA 예제 완료")
    print("=" * 70)


def show_structure() -> None:
    """DRY RUN 모드에서 구조 표시"""
    print("📐 Advanced RetrievalQA 구조:\n")
    print("  예제 1: 기본 RetrievalQA (stuff)")
    print("    • 모든 문서를 하나의 프롬프트로")
    print("    • 빠르고 간단")
    print()
    print("  예제 2: 커스텀 프롬프트")
    print("    • PromptTemplate로 답변 형식 제어")
    print("    • 언어, 스타일 커스터마이징")
    print()
    print("  예제 3: Map-Reduce Chain")
    print("    • 각 문서 개별 처리 → 결과 병합")
    print("    • 긴 문서, 많은 컨텍스트")
    print()
    print("  예제 4: Refine Chain")
    print("    • 초기 답변 생성 → 순차적 정제")
    print("    • 정교하고 상세한 답변")
    print()
    print("📊 데이터 흐름:")
    print("  질문 → [벡터 검색] → 관련 문서 → [Chain 처리] → LLM → 답변")
    print()
    print("✨ Chain Type 선택 가이드:")
    print("  • 짧은 컨텍스트 → stuff")
    print("  • 긴 문서 → map_reduce")
    print("  • 정교한 답변 → refine")
    print("  • 최적 답변 → map_rerank")


if __name__ == "__main__":
    main()
