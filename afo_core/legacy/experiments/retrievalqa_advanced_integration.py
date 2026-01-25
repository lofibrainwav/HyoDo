from __future__ import annotations

import os

from langchain.document_loaders import TextLoader
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Trinity Score: 90.0 (Established by Chancellor)
# ⚔️ 점수는 Truth Engine (scripts/calculate_trinity_score.py)에서만 계산됩니다.
# LLM은 consult_the_lens MCP 도구를 통해 점수를 확인하세요.
# 이 파일은 AFO 왕국의 眞善美孝 철학을 구현합니다

#!/usr/bin/env python3
"""제갈량 책사 제안: ConversationalRetrievalChain 통합
프롬프트 템플릿 + 메모리 + 벡터 검색 통합 (대화형 RAG)
"""


def main() -> None:
    print("=" * 70)
    print("제갈량 책사 제안: ConversationalRetrievalChain 통합")
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

    # 샘플 문서 생성
    print("1️⃣ 문서 로드 및 분할...")
    sample_docs = """
    LangChain은 대규모 언어 모델(LLM) 기반 애플리케이션을 구축하기 위한 프레임워크입니다.
    LangChain의 핵심 기능은 체인(Chain), 메모리(Memory), 에이전트(Agent)입니다.
    n8n은 워크플로우 자동화 플랫폼으로, LangChain 노드를 통해 AI 기능을 통합할 수 있습니다.
    """

    with open("/tmp/sample_docs.txt", "w") as f:
        f.write(sample_docs)

    loader = TextLoader("/tmp/sample_docs.txt")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
    texts = splitter.split_documents(docs)
    print(f"   ✓ {len(texts)}개 청크로 분할 완료\n")

    # 벡터 스토어 생성
    print("2️⃣ FAISS 벡터 스토어 생성...")
    vectorstore = FAISS.from_documents(texts, embeddings)
    print("   ✓ 벡터 스토어 생성 완료\n")

    # 고급 프롬프트 템플릿
    print("3️⃣ 프롬프트 템플릿 설정...")
    prompt_template = """다음 컨텍스트를 사용하여 질문에 답변하세요.
    답을 모르면 모른다고 말하고, 억지로 답변하지 마세요.

    컨텍스트: {context}

    질문: {question}
    답변:"""

    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    print("   ✓ 프롬프트 템플릿 설정 완료\n")

    # 메모리 초기화
    print("4️⃣ 대화 메모리 초기화...")
    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, output_key="answer"
    )
    print("   ✓ 메모리 초기화 완료\n")

    # ConversationalRetrievalChain 생성
    print("5️⃣ ConversationalRetrievalChain 생성...")
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": PROMPT},
    )
    print("   ✓ Chain 생성 완료\n")

    # 대화 테스트
    print("=" * 70)
    print("대화 테스트 (멀티 턴)")
    print("=" * 70)
    print()

    # 턴 1
    query1 = "LangChain이란 무엇인가요?"
    print(f"👤 질문 1: {query1}")
    result1 = qa_chain({"question": query1})
    print(f"🤖 답변 1: {result1['answer']}")
    print()

    # 턴 2
    query2 = "그걸 n8n에서 어떻게 사용하나요?"
    print(f"👤 질문 2: {query2}")
    result2 = qa_chain({"question": query2})
    print(f"🤖 답변 2: {result2['answer']}")
    print()

    # 턴 3
    query3 = "핵심 기능은 뭐가 있어요?"
    print(f"👤 질문 3: {query3}")
    result3 = qa_chain({"question": query3})
    print(f"🤖 답변 3: {result3['answer']}")
    print()

    print("=" * 70)
    print("✓ ConversationalRetrievalChain 테스트 완료")
    print("=" * 70)


def show_structure() -> None:
    """DRY RUN 모드에서 구조 표시"""
    print("📐 ConversationalRetrievalChain 구조:\n")
    print("  1. LLM: ChatOpenAI (gpt-3.5-turbo)")
    print("  2. Embeddings: OpenAIEmbeddings")
    print("  3. Vector Store: FAISS")
    print("  4. Memory: ConversationBufferMemory")
    print("  5. Prompt: Custom PromptTemplate")
    print("  6. Chain: ConversationalRetrievalChain")
    print()
    print("📊 데이터 흐름:")
    print("  질문 → [메모리 확인] → [벡터 검색] → [프롬프트 생성] → LLM → 답변")
    print("           ↓")
    print("        [메모리 저장]")
    print()
    print("✨ 특징:")
    print("  • 이전 대화 기억 (ConversationBufferMemory)")
    print("  • 문서 검색 기반 답변 (FAISS Retriever)")
    print("  • 커스텀 프롬프트 템플릿")
    print("  • 소스 문서 추적")


if __name__ == "__main__":
    main()
