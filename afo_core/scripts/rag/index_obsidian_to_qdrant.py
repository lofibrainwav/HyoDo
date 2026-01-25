from __future__ import annotations

import argparse
import sys
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from obsidian_loader import ObsidianLoader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    OBSIDIAN_VAULT_PATH,
    QDRANT_COLLECTION_NAME,
    QDRANT_URL,
)

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
# mypy: ignore-errors
"""옵시디언 vault를 Qdrant 벡터 DB에 인덱싱"""


# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))


def create_collection_if_not_exists(
    client: QdrantClient, collection_name: str, embedding_dim: int = 1536
):
    """컬렉션이 없으면 생성"""
    try:
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name not in collection_names:
            print(f"📦 컬렉션 생성 중: {collection_name}")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
            )
            print("✅ 컬렉션 생성 완료")
        else:
            print(f"✅ 컬렉션 이미 존재: {collection_name}")
    except Exception as e:
        print(f"⚠️  컬렉션 확인 실패: {e}")


def index_obsidian_vault(
    vault_path: Path,
    qdrant_url: str,
    collection_name: str,
    embedding_model: str = EMBEDDING_MODEL,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    clear_existing: bool = False,
):
    """옵시디언 vault를 Qdrant에 인덱싱

    Args:
        vault_path: 옵시디언 vault 경로
        qdrant_url: Qdrant 서버 URL
        collection_name: 컬렉션 이름
        embedding_model: 임베딩 모델 이름
        chunk_size: 청크 크기
        chunk_overlap: 청크 오버랩
        clear_existing: 기존 데이터 삭제 여부

    """
    print("🔧 옵시디언 vault → Qdrant 인덱싱 시작...\n")

    # 1. 문서 로드
    print("1️⃣ 문서 로드 중...")
    loader = ObsidianLoader(vault_path)
    documents = loader.load_documents()
    print(f"   ✅ {len(documents)}개 문서 로드 완료")

    if not documents:
        print("⚠️  로드할 문서가 없습니다.")
        return

    # 2. 텍스트 분할
    print("\n2️⃣ 텍스트 분할 중...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   ✅ {len(chunks)}개 청크 생성 완료")

    # 3. Qdrant 클라이언트 연결
    print("\n3️⃣ Qdrant 연결 중...")
    client = QdrantClient(url=qdrant_url)

    # 4. 임베딩 모델 초기화
    print("\n4️⃣ 임베딩 모델 초기화 중...")
    embeddings = OpenAIEmbeddings(model=embedding_model)
    embedding_dim = len(embeddings.embed_query("test"))
    print(f"   ✅ 임베딩 차원: {embedding_dim}")

    # 5. 컬렉션 생성/확인
    print("\n5️⃣ 컬렉션 확인 중...")
    create_collection_if_not_exists(client, collection_name, embedding_dim)

    # 6. 기존 데이터 삭제 (선택적)
    if clear_existing:
        print("\n6️⃣ 기존 데이터 삭제 중...")
        try:
            client.delete_collection(collection_name)
            create_collection_if_not_exists(client, collection_name, embedding_dim)
            print("   ✅ 기존 데이터 삭제 완료")
        except Exception as e:
            print(f"   ⚠️  삭제 실패: {e}")

    # 7. 벡터 DB에 저장
    print("\n7️⃣ 벡터 DB에 저장 중...")
    vectorstore = Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embeddings,
    )

    vectorstore.add_documents(chunks)
    print(f"   ✅ {len(chunks)}개 청크 저장 완료")

    # 8. 결과 요약
    print("\n" + "=" * 60)
    print("✅ 인덱싱 완료!")
    print("=" * 60)
    print("📊 통계:")
    print(f"  - 원본 문서: {len(documents)}개")
    print(f"  - 생성된 청크: {len(chunks)}개")
    print(f"  - 컬렉션: {collection_name}")
    print(f"  - Qdrant URL: {qdrant_url}")
    print()


def main() -> None:
    """메인 함수"""

    parser = argparse.ArgumentParser(description="옵시디언 vault를 Qdrant에 인덱싱")
    parser.add_argument("--vault-path", type=str, default=str(OBSIDIAN_VAULT_PATH))
    parser.add_argument("--qdrant-url", type=str, default=QDRANT_URL)
    parser.add_argument("--collection", type=str, default=QDRANT_COLLECTION_NAME)
    parser.add_argument("--clear", action="store_true", help="기존 데이터 삭제")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=CHUNK_OVERLAP)

    args = parser.parse_args()

    index_obsidian_vault(
        vault_path=Path(args.vault_path),
        qdrant_url=args.qdrant_url,
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        clear_existing=args.clear,
    )


if __name__ == "__main__":
    main()
