from __future__ import annotations

import os

from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.prompts import PromptTemplate
from langchain_classic.chains import ConversationChain
from langchain_openai import ChatOpenAI

# Trinity Score: 90.0 (Established by Chancellor)
# ⚔️ 점수는 Truth Engine (scripts/calculate_trinity_score.py)에서만 계산됩니다.
# LLM은 consult_the_lens MCP 도구를 통해 점수를 확인하세요.
# 이 파일은 AFO 왕국의 眞善美孝 철학을 구현합니다

#!/usr/bin/env python3
"""사마의 책사 제안: Multi-turn Conversation (멀티 턴 대화)
ConversationChain + Memory로 이전 대화 맥락 유지
"""


def main() -> None:
    print("=" * 70)
    print("사마의 책사 제안: Multi-turn Conversation")
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

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    # 예제 1: 기본 ConversationBufferMemory
    print("=" * 70)
    print("예제 1: 기본 대화 메모리 (ConversationBufferMemory)")
    print("=" * 70)
    print()

    memory_buffer = ConversationBufferMemory(return_messages=True)
    conversation_buffer = ConversationChain(llm=llm, memory=memory_buffer, verbose=False)

    print("1️⃣ 첫 번째 대화 턴")
    response1 = conversation_buffer.predict(input="안녕하세요! 저는 영덕입니다.")
    print("   👤 입력: 안녕하세요! 저는 영덕입니다.")
    print(f"   🤖 응답: {response1}\n")

    print("2️⃣ 두 번째 대화 턴 (이름 기억 확인)")
    response2 = conversation_buffer.predict(input="제 이름이 뭐죠?")
    print("   👤 입력: 제 이름이 뭐죠?")
    print(f"   🤖 응답: {response2}\n")

    print("3️⃣ 세 번째 대화 턴 (맥락 유지 확인)")
    response3 = conversation_buffer.predict(input="저는 LangChain을 공부하고 있어요.")
    print("   👤 입력: 저는 LangChain을 공부하고 있어요.")
    print(f"   🤖 응답: {response3}\n")

    print("4️⃣ 네 번째 대화 턴 (이전 맥락 기억)")
    response4 = conversation_buffer.predict(input="제가 뭘 공부한다고 했죠?")
    print("   👤 입력: 제가 뭘 공부한다고 했죠?")
    print(f"   🤖 응답: {response4}\n")

    # 메모리 내용 확인
    print("📝 저장된 대화 기록:")
    print("-" * 70)
    history = memory_buffer.load_memory_variables({})
    for i, msg in enumerate(history["history"]):
        role = "👤 사용자" if msg.type == "human" else "🤖 AI"
        print(f"   {role}: {msg.content}")
    print()

    # 예제 2: ConversationSummaryMemory (긴 대화용)
    print("=" * 70)
    print("예제 2: 요약 메모리 (ConversationSummaryMemory)")
    print("=" * 70)
    print()
    print("💡 긴 대화를 요약하여 저장 → 토큰 절약\n")

    memory_summary = ConversationSummaryMemory(llm=llm, return_messages=True)
    conversation_summary = ConversationChain(llm=llm, memory=memory_summary, verbose=False)

    print("1️⃣ 긴 대화 시뮬레이션")
    inputs = [
        "저는 n8n 워크플로우 자동화를 공부하고 있습니다.",
        "LangChain을 n8n에 통합하려고 합니다.",
        "Memory, Retriever, Chain 노드를 사용할 계획입니다.",
        "그동안 우리가 무슨 얘기를 했죠?",
    ]

    for i, user_input in enumerate(inputs, 1):
        print(f"   턴 {i}:")
        print(f"     👤 입력: {user_input}")
        response = conversation_summary.predict(input=user_input)
        print(f"     🤖 응답: {response}\n")

    # 요약된 메모리 확인
    print("📝 요약된 대화 기록:")
    print("-" * 70)
    summary = memory_summary.load_memory_variables({})
    if "history" in summary:
        for msg in summary["history"]:
            role = "👤 사용자" if msg.type == "human" else "🤖 AI"
            print(f"   {role}: {msg.content}")
    print()

    # 예제 3: 커스텀 프롬프트
    print("=" * 70)
    print("예제 3: 커스텀 프롬프트 템플릿")
    print("=" * 70)
    print()

    custom_template = """당신은 친절한 AI 어시스턴트입니다.
    항상 이전 대화 맥락을 기억하며 답변합니다.

    이전 대화:
    {history}

    현재 질문: {input}
    답변:"""

    custom_prompt = PromptTemplate(input_variables=["history", "input"], template=custom_template)

    memory_custom = ConversationBufferMemory(return_messages=False)
    conversation_custom = ConversationChain(
        llm=llm, memory=memory_custom, prompt=custom_prompt, verbose=False
    )

    print("1️⃣ 커스텀 프롬프트 대화")
    custom_inputs = [
        "저는 AFO Ultimate 프로젝트를 개발하고 있습니다.",
        "이 프로젝트는 무엇을 하는 건가요?",
    ]

    for i, user_input in enumerate(custom_inputs, 1):
        print(f"   턴 {i}:")
        print(f"     👤 입력: {user_input}")
        response = conversation_custom.predict(input=user_input)
        print(f"     🤖 응답: {response}\n")

    print("=" * 70)
    print("✓ Multi-turn Conversation 예제 완료")
    print("=" * 70)


def show_structure() -> None:
    """DRY RUN 모드에서 구조 표시"""
    print("📐 Multi-turn Conversation 구조:\n")
    print("  예제 1: ConversationBufferMemory")
    print("    • 모든 대화를 버퍼에 저장")
    print("    • 짧은 대화에 적합")
    print()
    print("  예제 2: ConversationSummaryMemory")
    print("    • 대화를 요약하여 저장")
    print("    • 긴 대화, 토큰 절약")
    print()
    print("  예제 3: 커스텀 프롬프트")
    print("    • PromptTemplate로 응답 스타일 제어")
    print("    • 특정 페르소나 구현")
    print()
    print("📊 공통 데이터 흐름:")
    print("  사용자 입력 → [메모리 로드] → [프롬프트 구성] → LLM → 응답")
    print("                     ↓")
    print("                 [메모리 저장]")
    print()
    print("✨ 핵심 개념:")
    print("  • Memory: 대화 맥락 유지")
    print("  • ConversationChain: 대화 체인 관리")
    print("  • PromptTemplate: 응답 형식 제어")


if __name__ == "__main__":
    main()
