from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from obsidian_loader import ObsidianLoader
from qdrant_client import QdrantClient

from AFO.config.settings import get_settings
from config import OBSIDIAN_VAULT_PATH, print_config

# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
#!/usr/bin/env python3
"""
RAG 시스템 전체 테스트 스크립트
"""


# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))


def test_obsidian_loader() -> None:
    """옵시디언 로더 테스트"""
    print("=" * 60)
    print("1️⃣ 옵시디언 문서 로더 테스트")
    print("=" * 60)

    vault_path = OBSIDIAN_VAULT_PATH

    try:
        loader = ObsidianLoader(vault_path)
        documents = loader.load_documents()

        print(f"✅ 문서 로드 성공: {len(documents)}개")

        if documents:
            sample = documents[0]
            print("\n📝 샘플 문서:")
            print(f"  파일: {sample.metadata.get('source')}")
            print(f"  태그: {sample.metadata.get('tags', [])[:5]}")
            print(f"  링크: {sample.metadata.get('links', [])[:5]}")
            print(f"  카테고리: {sample.metadata.get('category')}")

        return True, len(documents)
    except Exception as e:
        print(f"❌ 문서 로드 실패: {e}")

        traceback.print_exc()
        return False, 0


def test_qdrant_connection() -> None:
    """Qdrant 연결 테스트"""
    print("\n" + "=" * 60)
    print("2️⃣ Qdrant 연결 테스트")
    print("=" * 60)

    # 중앙 설정 사용 (Phase 1 리팩토링)
    try:
        qdrant_url = get_settings().QDRANT_URL
    except ImportError:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")

    try:
        client = QdrantClient(url=qdrant_url)
        collections = client.get_collections()

        print(f"✅ Qdrant 연결 성공: {qdrant_url}")
        print(f"📊 컬렉션 수: {len(collections.collections)}")

        for col in collections.collections:
            info = client.get_collection(col.name)
            print(f"  - {col.name}: {info.points_count}개 벡터")

        return True
    except Exception as e:
        print(f"❌ Qdrant 연결 실패: {e}")
        print("💡 Qdrant 서버가 실행 중인지 확인하세요:")
        print("   docker-compose up -d afo-qdrant")
        return False


def test_embeddings() -> None:
    """임베딩 모델 테스트"""
    print("\n" + "=" * 60)
    print("3️⃣ 임베딩 모델 테스트")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않음")
        return False

    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        test_embedding = embeddings.embed_query("테스트")

        print("✅ 임베딩 생성 성공")
        print(f"📊 임베딩 차원: {len(test_embedding)}")

        return True
    except Exception as e:
        print(f"❌ 임베딩 생성 실패: {e}")
        return False


def test_indexing(dry_run: bool = True) -> None:
    """인덱싱 테스트 (dry-run)"""
    print("\n" + "=" * 60)
    print("4️⃣ 인덱싱 테스트 (DRY RUN)")
    print("=" * 60)

    if dry_run:
        print("⚠️  DRY RUN 모드: 실제 인덱싱은 수행하지 않음")

    vault_path = OBSIDIAN_VAULT_PATH

    try:
        loader = ObsidianLoader(vault_path)
        documents = loader.load_documents()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        chunks = text_splitter.split_documents(documents)

        print("✅ 인덱싱 준비 완료")
        print(f"📊 원본 문서: {len(documents)}개")
        print(f"📊 생성될 청크: {len(chunks)}개")
        print(f"📊 평균 청크/문서: {len(chunks) / len(documents):.1f}개")

        return True, len(documents), len(chunks)
    except Exception as e:
        print(f"❌ 인덱싱 테스트 실패: {e}")

        traceback.print_exc()
        return False, 0, 0


def main() -> None:
    """메인 함수"""
    print("\n🧪 RAG 시스템 전체 테스트 시작...\n")

    results = {
        "loader": False,
        "qdrant": False,
        "embeddings": False,
        "indexing": False,
    }

    stats = {}

    # 1. 문서 로더 테스트
    success, doc_count = test_obsidian_loader()
    results["loader"] = success
    stats["documents"] = doc_count

    # 2. Qdrant 연결 테스트
    results["qdrant"] = test_qdrant_connection()

    # 3. 임베딩 테스트
    results["embeddings"] = test_embeddings()

    # 4. 인덱싱 테스트
    success, doc_count, chunk_count = test_indexing(dry_run=True)
    results["indexing"] = success
    stats["chunks"] = chunk_count

    # 설정 정보 출력

    print("\n" + "=" * 60)
    print("📋 현재 설정")
    print("=" * 60)
    print_config()

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✅ 모든 테스트 통과!")
        print("\n📊 통계:")
        print(f"  - 문서 수: {stats.get('documents', 0)}개")
        print(f"  - 예상 청크 수: {stats.get('chunks', 0)}개")
        print("\n💡 다음 단계:")
        print("  python index_obsidian_to_qdrant.py --clear")
    else:
        print("\n⚠️  일부 테스트 실패")
        print("\n💡 해결 방법:")
        if not results["qdrant"]:
            print("  - Qdrant 서버 실행: docker-compose up -d afo-qdrant")
        if not results["embeddings"]:
            print("  - OPENAI_API_KEY 설정: export OPENAI_API_KEY='your-key'")

    print()


if __name__ == "__main__":
    main()
