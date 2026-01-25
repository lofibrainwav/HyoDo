"""
LanceDB Vector Store Adapter for AFO Kingdom
眞善美孝永 - 최소 변경으로 최대 호환성
"""

import os
from abc import ABC, abstractmethod
from typing import Any

from config.settings import settings

# LanceDB import (optional)
try:
    import lancedb
    import pyarrow as pa

    LANCEDB_AVAILABLE = True
except ImportError:
    lancedb = None
    pa = None
    LANCEDB_AVAILABLE = False

# Qdrant import (기존 호환성 유지)
try:
    from qdrant_client import QdrantClient

    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None
    QDRANT_AVAILABLE = False


class VectorStoreAdapter(ABC):
    """벡터 스토어 어댑터 인터페이스"""

    @abstractmethod
    def search(self, embedding: list[float], top_k: int) -> list[dict[str, Any]]:
        """벡터 검색"""
        pass

    @abstractmethod
    def insert(self, data: list[dict[str, Any]]) -> bool:
        """데이터 삽입"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """스토어 사용 가능 여부"""
        pass


class LanceDBAdapter(VectorStoreAdapter):
    """LanceDB 어댑터 - 동적 차원 + float32 강제 적용"""

    def __init__(self) -> None:
        self.db_path = settings.LANCEDB_PATH
        self.collection_name = "afokingdom_knowledge"
        self.db = None
        self.table = None
        self.embed_dim = None  # 동적 차원 저장
        self._initialize()

    def _initialize(self) -> None:
        """LanceDB 초기화"""
        if not LANCEDB_AVAILABLE:
            return

        try:
            os.makedirs(self.db_path, exist_ok=True)
            self.db = lancedb.connect(self.db_path)

            # 테이블이 없으면 생성 (동적 차원으로)
            if self.collection_name not in self.db.table_names():
                # Reality Gate: 실제 임베딩 차원 감지
                self.embed_dim = self._detect_embedding_dimension()
                if self.embed_dim is None:
                    print("[LanceDB] 임베딩 차원 감지 실패 - 기본값 768 사용")
                    self.embed_dim = 768

                # PyArrow 스키마 정의 (동적 차원)
                schema = pa.schema(
                    [
                        ("id", pa.string()),
                        ("content", pa.string()),
                        ("source", pa.string()),
                        (
                            "vector",
                            pa.list_(pa.float32(), self.embed_dim),
                        ),  # 동적 크기 벡터
                    ]
                )
                self.table = self.db.create_table(self.collection_name, schema=schema)
                print(f"[LanceDB] 테이블 생성 완료: 차원={self.embed_dim}")
            else:
                self.table = self.db.open_table(self.collection_name)
                # 기존 테이블의 차원 확인
                if hasattr(self.table, "schema"):
                    vector_field = self.table.schema.field("vector")
                    if vector_field and hasattr(vector_field.type, "list_size"):
                        self.embed_dim = vector_field.type.list_size
                        print(f"[LanceDB] 기존 테이블 로드: 차원={self.embed_dim}")
                    elif vector_field and hasattr(vector_field.type, "value_type"):
                        # 호환성을 위한 폴백
                        try:
                            self.embed_dim = vector_field.type.num_elements
                            print(f"[LanceDB] 기존 테이블 로드 (폴백): 차원={self.embed_dim}")
                        except AttributeError:
                            print("[LanceDB] 기존 테이블 차원 확인 실패")

        except Exception as e:
            print(f"[LanceDB] 초기화 실패: {e}")
            self.db = None
            self.table = None

    def _detect_embedding_dimension(self) -> int | None:
        """Reality Gate: 실제 임베딩 차원 감지"""
        try:
            # Ollama API로 실제 차원 확인
            import requests

            ollama_host = settings.OLLAMA_BASE_URL
            embed_model = settings.EMBED_MODEL

            # /api/embed 엔드포인트 시도
            try:
                r = requests.post(
                    f"{ollama_host}/api/embed",
                    json={"model": embed_model, "input": "dimension check"},
                    timeout=min(settings.OLLAMA_TIMEOUT, 30),  # 최대 30초
                )
                r.raise_for_status()
                vec = r.json()["embeddings"][0]
                dim = len(vec)
                print(f"[Reality Gate] 실제 임베딩 차원 감지: {dim}D")
                return dim
            except Exception:
                # 폴백: /api/embeddings 시도
                r = requests.post(
                    f"{ollama_host}/api/embeddings",
                    json={"model": embed_model, "prompt": "dimension check"},
                    timeout=min(settings.OLLAMA_TIMEOUT, 30),  # 최대 30초
                )
                r.raise_for_status()
                vec = r.json()["embedding"]
                dim = len(vec)
                print(f"[Reality Gate] 실제 임베딩 차원 감지 (폴백): {dim}D")
                return dim

        except Exception as e:
            print(f"[Reality Gate] 차원 감지 실패: {e}")
            return None

    def search(self, embedding: list[float], top_k: int) -> list[dict[str, Any]]:
        """LanceDB 벡터 검색"""
        if not self.is_available() or not self.table:
            return []

        try:
            results = self.table.search(embedding).limit(top_k).to_list()

            # 결과 포맷팅 (Qdrant 호환)
            formatted = []
            for i, result in enumerate(results):
                formatted.append(
                    {
                        "id": result.get("id", f"lancedb_{i}"),
                        "content": result.get("content", ""),
                        "score": result.get("_distance", 0.0),  # LanceDB는 _distance 사용
                        "source": result.get("source", "lancedb"),
                        "metadata": result,
                    }
                )

            return formatted

        except Exception as e:
            print(f"[LanceDB] 검색 실패: {e}")
            return []

    def insert(self, data: list[dict[str, Any]]) -> bool:
        """LanceDB 데이터 삽입"""
        if not self.is_available() or not self.table:
            return False

        try:
            # LanceDB의 add 메소드는 리스트를 받음
            self.table.add(data)
            return True
        except Exception as e:
            print(f"[LanceDB] 삽입 실패: {e}")
            import traceback

            traceback.print_exc()
            return False

    def is_available(self) -> bool:
        """LanceDB 사용 가능 여부"""
        return LANCEDB_AVAILABLE and self.db is not None and self.table is not None


class QdrantAdapter(VectorStoreAdapter):
    """Qdrant 어댑터 (기존 호환성 유지)"""

    def __init__(self) -> None:
        self.client = None
        self.collection_name = "afokingdom_knowledge"
        self._initialize()

    def _initialize(self) -> None:
        """Qdrant 초기화"""
        if not QDRANT_AVAILABLE:
            return

        try:
            # 환경변수에서 호스트 정보 가져오기
            host = settings.QDRANT_HOST
            port = settings.QDRANT_PORT

            if host.startswith("http"):
                # URL 형태
                self.client = QdrantClient(url=host)
            else:
                # 호스트:포트 형태
                self.client = QdrantClient(host=host, port=port)

        except Exception as e:
            print(f"[Qdrant] 초기화 실패: {e}")
            self.client = None

    def search(self, embedding: list[float], top_k: int) -> list[dict[str, Any]]:
        """Qdrant 벡터 검색"""
        if not self.is_available() or not self.client:
            return []

        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=top_k,
                with_payload=True,
            )

            # 결과 포맷팅
            formatted = []
            for hit in search_result:
                payload = hit.payload or {}
                formatted.append(
                    {
                        "id": str(hit.id),
                        "content": payload.get("content", ""),
                        "score": float(hit.score),
                        "source": payload.get("source", "qdrant"),
                        "metadata": payload,
                    }
                )

            return formatted

        except Exception as e:
            print(f"[Qdrant] 검색 실패: {e}")
            return []

    def insert(self, data: list[dict[str, Any]]) -> bool:
        """Qdrant 데이터 삽입"""
        if not self.is_available() or not self.client:
            return False

        try:
            # Qdrant 포맷으로 변환
            points = []
            for item in data:
                point = {
                    "id": item.get("id"),
                    "vector": item.get("vector"),
                    "payload": {
                        "content": item.get("content", ""),
                        "source": item.get("source", "unknown"),
                    },
                }
                points.append(point)

            self.client.upsert(collection_name=self.collection_name, points=points)
            return True

        except Exception as e:
            print(f"[Qdrant] 삽입 실패: {e}")
            return False

    def is_available(self) -> bool:
        """Qdrant 사용 가능 여부"""
        return QDRANT_AVAILABLE and self.client is not None


# 전역 벡터 스토어 인스턴스
_vector_store_instance: VectorStoreAdapter | None = None


def get_vector_store() -> VectorStoreAdapter:
    """환경변수 기반 벡터 스토어 팩토리"""
    global _vector_store_instance

    if _vector_store_instance is not None:
        return _vector_store_instance

    # 환경변수에서 스토어 타입 결정
    store_type = settings.VECTOR_DB.lower()

    if store_type == "lancedb":
        _vector_store_instance = LanceDBAdapter()
    elif store_type == "chroma":
        # Chroma 어댑터 (향후 구현)
        _vector_store_instance = QdrantAdapter()  # 임시로 Qdrant 사용
    else:  # qdrant (기본값)
        _vector_store_instance = QdrantAdapter()

    return _vector_store_instance


def query_vector_store(embedding: list[float], top_k: int) -> list[dict[str, Any]]:
    """통합 벡터 검색 인터페이스"""
    store = get_vector_store()
    return store.search(embedding, top_k)


def insert_vector_store(data: list[dict[str, Any]]) -> bool:
    """통합 벡터 삽입 인터페이스"""
    store = get_vector_store()
    return store.insert(data)
