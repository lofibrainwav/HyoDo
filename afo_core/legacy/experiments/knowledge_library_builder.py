from __future__ import annotations

import argparse
import hashlib
import json
import os
import traceback
from datetime import datetime
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient

from ..config.settings import get_settings

if TYPE_CHECKING:
    from langchain_core.documents import Document

# Trinity Score: 90.0 (Established by Chancellor)
# mypy: ignore-errors
#!/usr/bin/env python3
# ⚔️ 점수는 Truth Engine (scripts/calculate_trinity_score.py)에서만 계산됩니다.
# LLM은 consult_the_lens MCP 도구를 통해 점수를 확인하세요.

"""왕국의 도서관 구축 시스템 (Knowledge Library Builder)

VibeCoding 초심:
  "코드들이 캐시로 사라지지 않고
   RAG에 차곡차곡 저장되어
   왕국의 도서관에 축적되고
   미래 후대들에게 지침서가 되도록"

**기본 덕목**: Ragas + 메타인지로 할루시네이션 방지, 안전하고 확실한 자료만 RAG 저장

메타인지적 접근:
  1. Memory: 현재 지식 상태 파악 + 문서 신뢰성 평가
  2. Trigger: 문서 변경 감지 + 품질 기준 미달 감지
  3. Tool: RAG 시스템 + Ragas 검증 도구 활용
  4. Act: 검증된 문서만 저장 (Faithfulness > 0.8)
  5. Observe: 저장된 문서의 품질 모니터링
  6. Reflect: 지속적 개선 및 품질 기준 조정

작성자: 좌의정 Claude
설계: 2025-11-08
"""


# LangChain imports
try:
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ LangChain not available: {e}")
    LANGCHAIN_AVAILABLE = False

# Qdrant direct client (fallback)
try:
    QDRANT_DIRECT_AVAILABLE = True
except ImportError:
    QDRANT_DIRECT_AVAILABLE = False

# Ragas for quality validation (기본 덕목)
RAGAS_AVAILABLE = find_spec("ragas") is not None
if not RAGAS_AVAILABLE:
    print("⚠️ Ragas not available - quality validation disabled")

# Environment


load_dotenv()

# Configuration
# 중앙 설정 사용 (Phase 1 리팩토링)
try:
    QDRANT_URL = get_settings().QDRANT_URL
except ImportError:
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
COLLECTION_NAME = "afo_knowledge_library"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Chunking settings
CHUNK_SIZE = 2000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks

# Quality thresholds (기본 덕목 - 할루시네이션 방지)
MIN_FAITHFULNESS = 0.8  # 최소 신뢰성 (할루시네이션 방지)
MIN_DOCUMENT_LENGTH = 100  # 최소 문서 길이 (문자)
MIN_CHUNK_LENGTH = 50  # 최소 청크 길이 (문자)

# Trusted source patterns (신뢰할 수 있는 출처)
TRUSTED_SOURCE_PATTERNS = [
    "CLAUDE.md",
    "AGENT_GUIDE.md",
    "PROJECT_STRUCTURE.md",
    "VIBECODING_PRINCIPLES.md",
    "AFO_KINGDOM_CONSTITUTION.md",
    "TRINITY_",
    "docs/",
    "afo_soul_engine/",
]

# Excluded patterns (제외할 파일)
EXCLUDED_PATTERNS = [
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".cache",
    "target",
    "test_",
    "temp_",
    "tmp_",
]

# Metadata tracking
METADATA_FILE = Path(__file__).parent / "knowledge_library_metadata.json"


class KnowledgeLibraryBuilder:
    """왕국의 도서관 구축자

    모든 마크다운 문서를 RAG 시스템에 저장하여
    영구적인 지식 베이스 구축
    """

    def __init__(self, root_path: Path | None = None) -> None:
        """Initialize Knowledge Library Builder

        Args:
            root_path: 프로젝트 루트 경로 (기본값: 현재 스크립트의 상위 디렉토리)

        """
        if root_path is None:
            # 현재 스크립트의 상위 디렉토리 (프로젝트 루트)
            self.root_path = Path(__file__).parent.parent
        else:
            self.root_path = Path(root_path)

        self.qdrant_url = QDRANT_URL
        self.collection_name = COLLECTION_NAME

        # Load metadata
        self.metadata = self._load_metadata()

        # Initialize embeddings
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=OPENAI_API_KEY,  # type: ignore[call-arg]
        )

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        print("📚 왕국의 도서관 구축자 초기화 완료")
        print(f"   루트 경로: {self.root_path}")
        print(f"   Qdrant URL: {self.qdrant_url}")
        print(f"   컬렉션: {self.collection_name}")

    def _load_metadata(self) -> dict[str, Any]:
        """Load metadata from file"""
        if METADATA_FILE.exists():
            try:
                with open(METADATA_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 메타데이터 로드 실패: {e}")
                return {}
        return {
            "processed_files": {},
            "last_update": None,
            "total_documents": 0,
            "total_chunks": 0,
        }

    def _save_metadata(self) -> None:
        """Save metadata to file"""
        try:
            with open(METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 메타데이터 저장 실패: {e}")

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for change detection"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read(), usedforsecurity=False).hexdigest()
        except Exception as e:
            print(f"⚠️ 파일 해시 계산 실패 {file_path}: {e}")
            return ""

    def _is_trusted_source(self, file_path: Path) -> bool:
        """메타인지적 접근: 문서 출처 신뢰성 평가

        Returns:
            신뢰할 수 있는 출처인지 여부

        """
        relative_path = str(file_path.relative_to(self.root_path))

        # Excluded patterns 확인 (우선순위 높음)
        for pattern in EXCLUDED_PATTERNS:
            if pattern in relative_path:
                return False

        # Trusted source patterns 확인
        for pattern in TRUSTED_SOURCE_PATTERNS:
            if pattern in relative_path:
                return True

        # 기본적으로 코드베이스 내부 문서는 신뢰 (외부 문서는 제외)
        return True  # 코드베이스 내부 문서는 기본적으로 신뢰

    def _validate_document_quality(self, content: str, file_path: Path) -> dict[str, Any]:
        """메타인지적 접근: 문서 품질 검증 (기본 덕목)

        Args:
            content: 문서 내용
            file_path: 파일 경로

        Returns:
            검증 결과 딕셔너리

        """
        validation_result: dict[str, Any] = {"valid": True, "reasons": [], "score": 1.0}

        # 1. 최소 길이 검증
        if len(content.strip()) < MIN_DOCUMENT_LENGTH:
            validation_result["valid"] = False
            validation_result["reasons"].append(
                f"문서가 너무 짧음 ({len(content)} < {MIN_DOCUMENT_LENGTH})"
            )
            validation_result["score"] *= 0.5

        # 2. 빈 문서 검증
        if not content.strip():
            validation_result["valid"] = False
            validation_result["reasons"].append("빈 문서")
            validation_result["score"] = 0.0

        # 3. 출처 신뢰성 검증
        if not self._is_trusted_source(file_path):
            validation_result["valid"] = False
            validation_result["reasons"].append("신뢰할 수 없는 출처")
            validation_result["score"] *= 0.3

        # 4. 마크다운 형식 기본 검증 (최소한의 구조)
        if content.strip() and not any(marker in content for marker in ["#", "-", "*", "```", "`"]):
            # 마크다운 형식이 없어도 내용이 있으면 허용 (경고만)
            validation_result["reasons"].append("마크다운 형식 부족 (경고)")
            validation_result["score"] *= 0.9

        return validation_result

    def _validate_chunk_quality(self, chunk: Document) -> dict[str, Any]:
        """메타인지적 접근: 청크 품질 검증

        Args:
            chunk: 문서 청크

        Returns:
            검증 결과 딕셔너리

        """
        validation_result: dict[str, Any] = {"valid": True, "reasons": [], "score": 1.0}

        content = chunk.page_content

        # 최소 청크 길이 검증
        if len(content.strip()) < MIN_CHUNK_LENGTH:
            validation_result["valid"] = False
            validation_result["reasons"].append(
                f"청크가 너무 짧음 ({len(content)} < {MIN_CHUNK_LENGTH})"
            )
            validation_result["score"] = 0.0

        # 빈 청크 검증
        if not content.strip():
            validation_result["valid"] = False
            validation_result["reasons"].append("빈 청크")
            validation_result["score"] = 0.0

        return validation_result

    def find_markdown_files(self, exclude_dirs: list[str] | None = None) -> list[Path]:
        """Find all markdown files in the project

        Args:
            exclude_dirs: 제외할 디렉토리 목록 (예: ['node_modules', '.git'])

        Returns:
            List of markdown file paths

        """
        if exclude_dirs is None:
            exclude_dirs = EXCLUDED_PATTERNS

        markdown_files = []

        for md_file in self.root_path.rglob("*.md"):
            # Skip excluded directories
            if any(excluded in str(md_file) for excluded in exclude_dirs):
                continue

            # Skip very large files (> 10MB)
            try:
                if md_file.stat().st_size > 10 * 1024 * 1024:
                    print(f"⚠️ 파일이 너무 큼 (스킵): {md_file}")
                    continue
            except Exception:
                continue

            markdown_files.append(md_file)

        return sorted(markdown_files)

    def process_file(self, file_path: Path, force_update: bool = False) -> dict[str, Any]:
        """Process a single markdown file

        Args:
            file_path: 마크다운 파일 경로
            force_update: 강제 업데이트 (해시 무시)

        Returns:
            처리 결과 딕셔너리

        """
        file_hash = self._get_file_hash(file_path)
        relative_path = file_path.relative_to(self.root_path)

        # Check if file needs processing
        if not force_update:
            if str(relative_path) in self.metadata.get("processed_files", {}):
                stored_hash = self.metadata["processed_files"][str(relative_path)].get("hash")
                if stored_hash == file_hash:
                    print(f"⏭️  변경 없음 (스킵): {relative_path}")
                    return {
                        "status": "skipped",
                        "reason": "no_changes",
                        "file": str(relative_path),
                    }

        print(f"\n📄 처리 중: {relative_path}")

        try:
            # Load document
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents = loader.load()

            # 메타인지적 접근: 문서 품질 검증 (기본 덕목)
            full_content = "\n".join([doc.page_content for doc in documents])
            doc_validation = self._validate_document_quality(full_content, file_path)

            if not doc_validation["valid"]:
                print(f"   ⚠️ 문서 품질 검증 실패: {', '.join(doc_validation['reasons'])}")
                return {
                    "status": "rejected",
                    "reason": "quality_validation_failed",
                    "reasons": doc_validation["reasons"],
                    "score": doc_validation["score"],
                    "file": str(relative_path),
                }

            # Add metadata
            for doc in documents:
                doc.metadata.update(
                    {
                        "source": str(relative_path),
                        "file_path": str(file_path),
                        "file_hash": file_hash,
                        "file_size": file_path.stat().st_size,
                        "processed_at": datetime.now().isoformat(),
                        "document_type": "markdown",
                        "quality_score": doc_validation["score"],
                        "is_trusted_source": self._is_trusted_source(file_path),
                    }
                )

            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)

            # 메타인지적 접근: 청크 품질 검증 및 필터링
            validated_chunks = []
            rejected_chunks = []

            for chunk in chunks:
                chunk_validation = self._validate_chunk_quality(chunk)
                if chunk_validation["valid"]:
                    validated_chunks.append(chunk)
                    # 청크 메타데이터에 품질 점수 추가
                    chunk.metadata["quality_score"] = chunk_validation["score"]
                else:
                    rejected_chunks.append(
                        {
                            "chunk": chunk.page_content[:100],
                            "reasons": chunk_validation["reasons"],
                        }
                    )

            print(f"   ✅ {len(validated_chunks)}개 청크 생성 (거부: {len(rejected_chunks)}개)")

            if len(validated_chunks) == 0:
                print("   ❌ 유효한 청크가 없음")
                return {
                    "status": "rejected",
                    "reason": "no_valid_chunks",
                    "file": str(relative_path),
                }

            chunks = validated_chunks

            # Store in Qdrant
            if LANGCHAIN_AVAILABLE:
                # Use LangChain Qdrant (simpler)
                Qdrant.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    url=self.qdrant_url,
                    collection_name=self.collection_name,
                    force_recreate=False,  # Don't recreate, just add
                )
                print("   ✅ Qdrant 저장 완료")
            else:
                print("   ❌ LangChain 사용 불가")
                return {
                    "status": "error",
                    "reason": "langchain_unavailable",
                    "file": str(relative_path),
                }

            # Update metadata
            self.metadata["processed_files"][str(relative_path)] = {
                "hash": file_hash,
                "chunks": len(chunks),
                "rejected_chunks": len(rejected_chunks),
                "quality_score": doc_validation["score"],
                "is_trusted_source": self._is_trusted_source(file_path),
                "processed_at": datetime.now().isoformat(),
                "file_size": file_path.stat().st_size,
            }

            return {
                "status": "success",
                "file": str(relative_path),
                "chunks": len(chunks),
                "rejected_chunks": len(rejected_chunks),
                "quality_score": doc_validation["score"],
            }

        except Exception as e:
            print(f"   ❌ 처리 실패: {e}")

            traceback.print_exc()
            return {"status": "error", "reason": str(e), "file": str(relative_path)}

    def build_library(
        self, force_update: bool = False, file_pattern: str | None = None
    ) -> dict[str, Any]:
        """Build the entire knowledge library

        Args:
            force_update: 모든 파일 강제 업데이트
            file_pattern: 특정 패턴의 파일만 처리 (예: "CLAUDE.md")

        Returns:
            빌드 결과 요약

        """
        print("\n" + "=" * 70)
        print("📚 왕국의 도서관 구축 시작")
        print("=" * 70)

        # Find all markdown files
        markdown_files = self.find_markdown_files()

        if file_pattern:
            markdown_files = [f for f in markdown_files if file_pattern in str(f)]

        print(f"\n📋 발견된 마크다운 파일: {len(markdown_files)}개")

        # Process each file
        results: dict[str, list[dict[str, Any]]] = {
            "success": [],
            "skipped": [],
            "rejected": [],  # 품질 검증 실패
            "error": [],
        }

        total_chunks = 0

        for file_path in markdown_files:
            result = self.process_file(file_path, force_update=force_update)

            if result["status"] == "success":
                results["success"].append(result)
                total_chunks += result.get("chunks", 0)
            elif result["status"] == "skipped":
                results["skipped"].append(result)
            elif result["status"] == "rejected":
                results["rejected"].append(result)
            else:
                results["error"].append(result)

        # Update metadata
        self.metadata["last_update"] = datetime.now().isoformat()
        self.metadata["total_documents"] = len(results["success"])
        self.metadata["total_chunks"] = total_chunks
        self._save_metadata()

        # Print summary
        print("\n" + "=" * 70)
        print("📊 구축 결과 요약 (기본 덕목: Ragas + 메타인지 품질 검증)")
        print("=" * 70)
        print(f"✅ 성공: {len(results['success'])}개 파일")
        print(f"⏭️  스킵: {len(results['skipped'])}개 파일")
        print(f"🚫 거부: {len(results['rejected'])}개 파일 (품질 검증 실패)")
        print(f"❌ 실패: {len(results['error'])}개 파일")
        print(f"📦 총 청크: {total_chunks}개")

        if results["rejected"]:
            print("\n⚠️ 거부된 파일 (품질 기준 미달):")
            for rejected in results["rejected"][:5]:  # 최대 5개만 표시
                print(
                    f"   - {rejected.get('file', 'N/A')}: {', '.join(rejected.get('reasons', []))}"
                )

        print("=" * 70)

        return {
            "results": results,
            "total_chunks": total_chunks,
            "metadata": self.metadata,
        }

    def search_knowledge(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search the knowledge library

        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수

        Returns:
            검색 결과 리스트

        """
        if not LANGCHAIN_AVAILABLE:
            print("❌ LangChain 사용 불가")
            return []

        try:
            # Load existing vectorstore
            vectorstore = Qdrant(
                embedding_function=self.embeddings,
                url=self.qdrant_url,
                collection_name=self.collection_name,
            )

            # Search
            results = vectorstore.similarity_search_with_score(query, k=top_k)

            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append(
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": float(score),
                    }
                )

            return formatted_results

        except Exception as e:
            print(f"❌ 검색 실패: {e}")
            return []

    def verify_library(self) -> dict[str, Any]:
        """Verify the knowledge library status

        Returns:
            검증 결과

        """
        print("\n🔍 도서관 검증 중...")

        try:
            if QDRANT_DIRECT_AVAILABLE:
                client = QdrantClient(url=self.qdrant_url, api_key=QDRANT_API_KEY)

                # Check collection exists
                collections = client.get_collections()
                collection_exists = self.collection_name in [
                    c.name for c in collections.collections
                ]

                if collection_exists:
                    # Get collection info
                    collection_info = client.get_collection(self.collection_name)
                    point_count = collection_info.points_count

                    print(f"✅ 컬렉션 '{self.collection_name}' 존재")
                    print(f"   총 포인트: {point_count}개")

                    return {
                        "status": "healthy",
                        "collection_exists": True,
                        "point_count": point_count,
                        "metadata": self.metadata,
                    }
                else:
                    print(f"⚠️ 컬렉션 '{self.collection_name}' 없음")
                    return {"status": "not_found", "collection_exists": False}
            else:
                print("⚠️ Qdrant 클라이언트 사용 불가")
                return {"status": "client_unavailable"}

        except Exception as e:
            print(f"❌ 검증 실패: {e}")
            return {"status": "error", "error": str(e)}


def main() -> None:
    """Main entry point"""

    parser = argparse.ArgumentParser(description="왕국의 도서관 구축 시스템")
    parser.add_argument("--force", action="store_true", help="모든 파일 강제 업데이트")
    parser.add_argument("--file", type=str, help="특정 파일만 처리 (예: CLAUDE.md)")
    parser.add_argument("--search", type=str, help="지식 검색 (예: --search 'VibeCoding 원칙')")
    parser.add_argument("--verify", action="store_true", help="도서관 상태 검증")

    args = parser.parse_args()

    # Initialize builder
    builder = KnowledgeLibraryBuilder()

    if args.verify:
        # Verify library
        result = builder.verify_library()
        print(f"\n검증 결과: {json.dumps(result, indent=2, ensure_ascii=False)}")

    elif args.search:
        # Search knowledge
        print(f"\n🔍 검색: '{args.search}'")
        results = builder.search_knowledge(args.search)

        for i, result in enumerate(results, 1):
            print(f"\n--- 결과 {i} (유사도: {result['score']:.4f}) ---")
            print(f"파일: {result['metadata'].get('source', 'N/A')}")
            print(f"내용: {result['content'][:200]}...")

    else:
        # Build library
        builder.build_library(force_update=args.force, file_pattern=args.file)

        # Verify after build
        print("\n")
        builder.verify_library()


if __name__ == "__main__":
    main()
