from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from obsidian_loader import ObsidianLoader
from qdrant_client import QdrantClient
from rag_graph import create_rag_graph

from AFO.config.settings import get_settings
from config import OBSIDIAN_VAULT_PATH, print_config

# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
#!/usr/bin/env python3
"""
RAG 연결 검증 스크립트
옵시디언 vault와 Qdrant 연결 상태 확인
"""


# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))


def verify_obsidian_vault() -> None:
    """옵시디언 vault 확인"""
    print("1️⃣ 옵시디언 vault 확인")
    vault_path = OBSIDIAN_VAULT_PATH

    if not vault_path.exists():
        print(f"  ❌ Vault 경로 없음: {vault_path}")
        return False

    print(f"  ✅ Vault 경로: {vault_path}")

    # 문서 수 확인
    md_files = list(vault_path.rglob("*.md"))
    print(f"  ✅ Markdown 파일: {len(md_files)}개")

    # 로더 테스트
    try:
        loader = ObsidianLoader(vault_path)
        documents = loader.load_documents()
        print(f"  ✅ 로드 가능한 문서: {len(documents)}개")
        return True, len(documents)
    except Exception as e:
        print(f"  ❌ 문서 로드 실패: {e}")
        return False, 0


def verify_qdrant() -> None:
    """Qdrant 연결 확인"""
    print("\n2️⃣ Qdrant 연결 확인")
    # 중앙 설정 사용 (Phase 1 리팩토링)
    try:
        qdrant_url = get_settings().QDRANT_URL
    except ImportError:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")

    try:
        client = QdrantClient(url=qdrant_url)
        collections = client.get_collections()

        print(f"  ✅ Qdrant URL: {qdrant_url}")
        print("  ✅ 연결 성공")
        print(f"  📊 컬렉션 수: {len(collections.collections)}")

        # obsidian_vault 컬렉션 확인
        collection_names = [c.name for c in collections.collections]
        if "obsidian_vault" in collection_names:
            info = client.get_collection("obsidian_vault")
            print(f"  ✅ obsidian_vault 컬렉션: {info.points_count}개 벡터")
            return True, info.points_count
        else:
            print("  ⚠️  obsidian_vault 컬렉션 없음 (인덱싱 필요)")
            return True, 0

    except Exception as e:
        print(f"  ❌ Qdrant 연결 실패: {e}")
        return False, 0


def verify_embeddings() -> None:
    """임베딩 모델 확인"""
    print("\n3️⃣ 임베딩 모델 확인")
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("  ❌ OPENAI_API_KEY 환경 변수 없음")
        return False

    print(f"  ✅ OPENAI_API_KEY 설정됨 (길이: {len(api_key)})")

    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        test_embedding = embeddings.embed_query("테스트")

        print("  ✅ 임베딩 모델: text-embedding-3-small")
        print(f"  ✅ 임베딩 차원: {len(test_embedding)}")
        return True
    except Exception as e:
        print(f"  ❌ 임베딩 테스트 실패: {e}")
        return False


def verify_rag_pipeline() -> None:
    """RAG 파이프라인 확인"""
    print("\n4️⃣ RAG 파이프라인 확인")

    try:
        create_rag_graph()
        print("  ✅ LangGraph 생성 성공")

        # 간단한 테스트

        # 실제 실행은 하지 않고 구조만 확인
        print("  ✅ RAG 파이프라인 구조 확인 완료")
        return True
    except Exception as e:
        print(f"  ❌ RAG 파이프라인 확인 실패: {e}")

        traceback.print_exc()
        return False


def main() -> None:
    """메인 함수"""
    print("\n🔍 RAG 연결 상태 검증 시작...\n")

    results = {
        "vault": False,
        "qdrant": False,
        "embeddings": False,
        "rag_pipeline": False,
    }

    stats = {}

    # 검증 실행
    success, doc_count = verify_obsidian_vault()
    results["vault"] = success
    stats["documents"] = doc_count

    success, vector_count = verify_qdrant()
    results["qdrant"] = success
    stats["vectors"] = vector_count

    results["embeddings"] = verify_embeddings()
    results["rag_pipeline"] = verify_rag_pipeline()

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 검증 결과")
    print("=" * 60)

    for component, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {component}")

    print("\n" + "=" * 60)
    print("📋 현재 설정")
    print("=" * 60)
    print_config()

    print("\n📈 통계:")
    print(f"  - 문서 수: {stats.get('documents', 0)}개")
    print(f"  - 벡터 수: {stats.get('vectors', 0)}개")

    all_ready = all(results.values())

    if all_ready:
        if stats.get("vectors", 0) == 0:
            print("\n⚠️  모든 구성 요소 준비됨, 인덱싱 필요")
            print("💡 실행: python index_obsidian_to_qdrant.py --clear")
        else:
            print("\n✅ 모든 구성 요소 준비됨, RAG 시스템 사용 가능")
    else:
        print("\n⚠️  일부 구성 요소 준비되지 않음")

    print()


if __name__ == "__main__":
    main()
