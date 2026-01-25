from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Union

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_text_splitters import CharacterTextSplitter

from AFO.config.settings import get_settings

# Trinity Score: 90.0 (Established by Chancellor)
# ⚔️ 점수는 Truth Engine (scripts/calculate_trinity_score.py)에서만 계산됩니다.
# LLM은 consult_the_lens MCP 도구를 통해 점수를 확인하세요.
# 이 파일은 AFO 왕국의 眞善美孝 철학을 구현합니다

#!/usr/bin/env python3
"""
n8n 워크플로우 정보를 AFO RAG 시스템에 추가하는 검증된 스크립트

사용법:
    python add_workflow_to_rag_verified.py
"""


# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


# 환경 변수 로드 (dotenv 없이 직접 파싱)
def load_env() -> None:
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value
    return env_vars


env = load_env()
OPENAI_API_KEY = env.get("OPENAI_API_KEY")

# LangChain 및 Qdrant 임포트 (ChromaDB → Qdrant 마이그레이션)
try:
    pass  # Placeholder
except ImportError as e:
    print(f"❌ 필수 라이브러리가 설치되지 않았습니다: {e}")
    print("   설치: pip install langchain-qdrant langchain-openai")
    sys.exit(1)

# OpenAI API 키 확인
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    print("   .env 파일에 OPENAI_API_KEY를 추가하세요.")
    sys.exit(1)

# Qdrant 설정 (ChromaDB → Qdrant 마이그레이션)
# 중앙 설정 사용 (Phase 1 리팩토링)
try:
    QDRANT_URL = get_settings().QDRANT_URL
except ImportError:
    QDRANT_URL = env.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = env.get("QDRANT_API_KEY", None)
COLLECTION_NAME = "afo_workflows"

# 문서 파일 경로
WORKFLOW_DOC_PATH = (
    PROJECT_ROOT / "n8n_workflows" / "modularized" / "N8N_WORKFLOW_RAG_DOCUMENTATION.md"
)


def create_workflow_document() -> None:
    """워크플로우 문서 파일을 읽어서 Document로 변환"""

    if not WORKFLOW_DOC_PATH.exists():
        print(f"❌ 워크플로우 문서 파일을 찾을 수 없습니다: {WORKFLOW_DOC_PATH}")
        sys.exit(1)

    with open(WORKFLOW_DOC_PATH, encoding="utf-8") as f:
        content = f.read()

    return Document(
        page_content=content,
        metadata={
            "source": str(WORKFLOW_DOC_PATH),
            "workflow_id": "ySdajIsal2qX42ws",
            "workflow_name": "Daily Notion Report",
            "type": "workflow_documentation",
            "category": "automation",
            "tags": [
                "n8n",
                "notion",
                "vibecodehub",
                "daily-report",
                "automation",
                "playwright",
            ],
            "created_at": "2025-01-11",
            "updated_at": "2025-01-11",
        },
    )


def add_to_rag() -> None:
    """워크플로우 문서를 Qdrant에 추가 (ChromaDB → Qdrant 마이그레이션)"""

    print("📚 n8n 워크플로우 정보를 RAG 시스템에 추가 중...")
    print(f"   문서 파일: {WORKFLOW_DOC_PATH}")
    print(f"   Qdrant URL: {QDRANT_URL}")
    print(f"   컬렉션: {COLLECTION_NAME}")

    # 임베딩 생성
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    # 워크플로우 문서 생성
    workflow_doc = create_workflow_document()

    # 텍스트 분할 (큰 문서를 작은 청크로)
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents([workflow_doc])

    print(f"   문서 청크 수: {len(splits)}개")

    try:
        # Qdrant에 문서 추가 (기존 컬렉션이 있으면 자동으로 사용)
        print("\n📝 Qdrant에 문서 추가 중...")
        vectorstore = Qdrant.from_documents(
            documents=splits,
            embedding=embeddings,
            url=QDRANT_URL,
            collection_name=COLLECTION_NAME,
            api_key=QDRANT_API_KEY,
            force_recreate=False,  # 기존 컬렉션 유지
        )

        print("✅ 워크플로우 문서 추가 완료!")
        print(f"   컬렉션: {COLLECTION_NAME}")
        print(f"   추가된 청크: {len(splits)}개")
        print(f"   Qdrant URL: {QDRANT_URL}")

        # 검색 테스트
        print("\n🔍 검색 테스트 중...")
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        test_queries = [
            "Daily Notion Report 워크플로우",
            "vibecodehub 연결 방법",
            "Playwright 자동화",
        ]

        for query in test_queries:
            results = retriever.get_relevant_documents(query)
            if results:
                print(f"   ✅ '{query}': {len(results)}개 문서 발견")
            else:
                print(f"   ⚠️ '{query}': 검색 결과 없음")

        return vectorstore

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("   Qdrant 서비스가 실행 중인지 확인하세요: docker Union[ps, grep] qdrant")

        traceback.print_exc()
        raise


def verify_workflow_in_rag(vectorstore) -> None:
    """RAG에 워크플로우가 제대로 추가되었는지 검증"""

    print("\n🔍 최종 검증 중...")

    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

    # 핵심 검색어로 테스트
    verification_queries = [
        "Daily Notion Report",
        "ySdajIsal2qX42ws",
        "Notion Query Vibecodehub",
        "n8n API 업데이트",
    ]

    success_count = 0
    for query in verification_queries:
        try:
            results = retriever.get_relevant_documents(query)
            if results and len(results) > 0:
                doc = results[0]
                if (
                    "ySdajIsal2qX42ws" in doc.page_content
                    or "Daily Notion Report" in doc.page_content
                ):
                    success_count += 1
                    print(f"   ✅ '{query}': 검색 성공")
                else:
                    print(f"   ⚠️ '{query}': 검색 결과 있으나 관련성 낮음")
            else:
                print(f"   ❌ '{query}': 검색 결과 없음")
        except Exception as e:
            print(f"   ❌ '{query}': 오류 - {e}")

    print(f"\n📊 검증 결과: {success_count}/{len(verification_queries)} 성공")

    if success_count >= len(verification_queries) * 0.75:  # 75% 이상 성공
        print("✅ RAG 시스템에 워크플로우 정보가 성공적으로 추가되었습니다!")
        return True
    else:
        print("⚠️ 일부 검색이 실패했습니다. 다시 시도해보세요.")
        return False


def main() -> None:
    """메인 함수"""
    try:
        print("=" * 60)
        print("n8n 워크플로우 RAG 추가 및 검증")
        print("=" * 60)

        # 1. RAG에 추가
        vectorstore = add_to_rag()

        # 2. 검증
        success = verify_workflow_in_rag(vectorstore)

        print("\n" + "=" * 60)
        if success:
            print("✅ 완료! 이제 RAG 시스템에서 워크플로우 정보를 검색할 수 있습니다.")
            print("\n사용 예시:")
            print("  - 'Daily Notion Report 워크플로우는 어떻게 구성되어 있나요?'")
            print("  - 'vibecodehub 연결 방법은?'")
            print("  - 'n8n 노드 설정을 Playwright로 자동화하려면?'")
        else:
            print("⚠️ 완료되었지만 일부 검증이 실패했습니다.")
        print("=" * 60)

        return 0 if success else 1

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
