"""
Context7 Memory 통합 모듈

Context7 지식 베이스와 Mem0를 통합하여
지식 베이스의 영속성과 검색 기능을 강화합니다.

Trinity Score 목표: 永 1.0 달성
"""

import time
from pathlib import Path
from typing import Any

from AFO.memory.mem0_client import AFO_MemoryClient, get_memory_client


class Context7MemoryManager:
    """
    Context7 지식 베이스와 Mem0 통합 관리자

    기능:
    - Context7 문서 메모리화
    - 지식 검색 강화
    - 사용자별 컨텍스트 유지
    - 성능 최적화
    """

    def __init__(self, memory_client: AFO_MemoryClient | None = None) -> None:
        """
        Context7 메모리 매니저 초기화

        Args:
            memory_client: Mem0 클라이언트 (없으면 기본 클라이언트 사용)
        """
        self.memory_client = memory_client or get_memory_client()
        self.context7_docs = self._load_context7_docs()
        self.performance_stats = {
            "docs_memorized": 0,
            "search_calls": 0,
            "total_latency_ms": 0,
        }

    def _load_context7_docs(self) -> list[dict[str, Any]]:
        """
        Context7 문서 목록 로딩

        Returns:
            List[Dict]: Context7 문서 정보
        """
        docs_path = Path("docs")
        context7_docs = []

        # 주요 Context7 문서들
        context7_files = [
            "CONTEXT7_COMPLETE_USAGE_GUIDE.md",
            "CONTEXT7_INTEGRATION_COMPLETE.md",
            "CONTEXT7_INTEGRATION_GUIDE.md",
            "CONTEXT7_LEGACY_INTEGRATION_COMPLETE.md",
            "CONTEXT7_SEQUENTIAL_THINKING_SKILLS_MASTER_INDEX.md",
            "CONTEXT7_SKILLS_REGISTRY_FINAL_VERIFICATION.md",
        ]

        for doc_file in context7_files:
            doc_path = docs_path / doc_file
            if doc_path.exists():
                context7_docs.append(
                    {
                        "path": str(doc_path),
                        "filename": doc_file,
                        "title": doc_file.replace(".md", "").replace("_", " "),
                        "category": "context7",
                    }
                )

        return context7_docs

    def memorize_context7_docs(self, user_id: str = "system") -> dict[str, Any]:
        """
        Context7 문서를 Mem0에 메모리화

        Args:
            user_id: 메모리 저장 사용자 ID

        Returns:
            Dict: 메모리화 결과
        """
        start_time = time.time()
        results = []

        for doc_info in self.context7_docs:
            try:
                # 문서 내용 읽기 (간단한 요약 생성)
                doc_path = Path(doc_info["path"])
                with open(doc_path, encoding="utf-8") as f:
                    content = f.read()

                # 문서 요약 생성 (첫 500자 + 주요 섹션)
                summary = self._generate_doc_summary(content, doc_info["filename"])

                # Mem0에 저장
                result = self.memory_client.add_memory(
                    content=summary,
                    user_id=user_id,
                    metadata={
                        "source": "context7",
                        "doc_type": "documentation",
                        "filename": doc_info["filename"],
                        "category": doc_info["category"],
                        "memorized_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    },
                    session_id="context7_initialization",
                    run_id=f"context7_memorize_{doc_info['filename']}",
                )

                results.append(
                    {
                        "doc": doc_info["filename"],
                        "success": result["success"],
                        "latency_ms": result["latency_ms"],
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "doc": doc_info["filename"],
                        "success": False,
                        "error": str(e),
                    }
                )

        total_latency = (time.time() - start_time) * 1000
        success_count = sum(1 for r in results if r["success"])

        self.performance_stats["docs_memorized"] = len(results)
        self.performance_stats["total_latency_ms"] += total_latency

        return {
            "operation": "memorize_context7_docs",
            "total_docs": len(results),
            "successful": success_count,
            "failed": len(results) - success_count,
            "total_latency_ms": total_latency,
            "results": results,
        }

    def _generate_doc_summary(self, content: str, filename: str) -> str:
        """
        문서 내용 기반 요약 생성

        Args:
            content: 문서 전체 내용
            filename: 파일명

        Returns:
            str: 생성된 요약
        """
        lines = content.split("\n")
        summary_parts = []

        # 제목 추출
        for line in lines[:10]:  # 처음 10줄에서 제목 찾기
            if line.startswith("#"):
                summary_parts.append(line.strip("# \t"))
                break

        # 주요 섹션 추출 (## 헤더)
        sections = []
        for line in lines:
            if line.startswith("## "):
                sections.append(line.lstrip("#").strip())

        if sections:
            summary_parts.append(f"주요 섹션: {', '.join(sections[:5])}")

        # 내용 요약 (첫 300자)
        content_start = content.find("---")  # 프론트매터 이후
        if content_start == -1:
            content_start = 0
        else:
            content_start += 3

        content_summary = content[content_start : content_start + 300].strip()
        if content_summary:
            summary_parts.append(f"내용: {content_summary}...")

        # 파일 정보
        summary_parts.append(f"파일: {filename}")

        return " | ".join(summary_parts)

    def search_context7_knowledge(
        self, query: str, user_id: str = "system", limit: int = 5
    ) -> dict[str, Any]:
        """
        Context7 지식 베이스 검색

        Args:
            query: 검색 쿼리
            user_id: 사용자 ID
            limit: 최대 결과 수

        Returns:
            Dict: 검색 결과
        """
        start_time = time.time()

        try:
            # Mem0에서 Context7 관련 메모리 검색
            search_result = self.memory_client.search_memory(
                query=query, user_id=user_id, limit=limit
            )

            # Context7 문서만 필터링
            context7_results = []
            if search_result["success"]:
                for result in search_result["results"]:
                    metadata = result.get("metadata", {})
                    if metadata.get("source") == "context7":
                        context7_results.append(result)

            latency = (time.time() - start_time) * 1000
            self.performance_stats["search_calls"] += 1
            self.performance_stats["total_latency_ms"] += latency

            return {
                "success": True,
                "query": query,
                "total_found": len(context7_results),
                "results": context7_results,
                "latency_ms": latency,
                "user_id": user_id,
            }

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "latency_ms": latency,
                "user_id": user_id,
            }

    def get_context7_stats(self, user_id: str = "system") -> dict[str, Any]:
        """
        Context7 메모리 통계 조회

        Args:
            user_id: 사용자 ID

        Returns:
            Dict: Context7 메모리 통계
        """
        try:
            # 모든 Context7 메모리 조회
            all_memories = self.memory_client.get_all_memories(user_id=user_id)

            context7_memories = []
            if all_memories["success"]:
                for memory in all_memories["memories"]:
                    metadata = memory.get("metadata", {})
                    if metadata.get("source") == "context7":
                        context7_memories.append(memory)

            return {
                "success": True,
                "total_memories": len(context7_memories),
                "docs_memorized": self.performance_stats["docs_memorized"],
                "search_calls": self.performance_stats["search_calls"],
                "avg_latency_ms": (
                    self.performance_stats["total_latency_ms"]
                    / max(self.performance_stats["search_calls"], 1)
                ),
                "memorized_docs": [doc["filename"] for doc in self.context7_docs],
                "user_id": user_id,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
            }

    def enhance_query_with_context7(self, query: str, user_id: str = "system") -> str:
        """
        Context7 지식을 활용하여 쿼리 강화

        Args:
            query: 원본 쿼리
            user_id: 사용자 ID

        Returns:
            str: Context7 지식으로 강화된 쿼리
        """
        # 관련 Context7 지식 검색
        search_result = self.search_context7_knowledge(query=query, user_id=user_id, limit=3)

        if not search_result["success"] or not search_result["results"]:
            return query

        # 관련 지식을 쿼리에 추가
        context_parts = []
        for result in search_result["results"][:2]:  # 최대 2개
            memory = result.get("memory", "")
            if len(memory) > 100:  # 너무 긴 경우 요약
                memory = memory[:100] + "..."
            context_parts.append(memory)

        if context_parts:
            enhanced_query = f"{query} [Context7 Knowledge: {' | '.join(context_parts)}]"
            return enhanced_query

        return query
