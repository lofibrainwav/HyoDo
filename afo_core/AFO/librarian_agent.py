"""
🎯 AFO Kingdom Librarian Agent (Phase 80)
문서 조사 및 지식 통합 특화 에이전트

작성자: 승상 (Chancellor)
날짜: 2026-01-22

역할: Multi-repo 분석, 문서 검색, 구현 예제 제공
모델: Gemini 3 Flash (Antigravity auth 시) 또는 Claude Sonnet 4.5
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from AFO.background_agents import BackgroundAgent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class KnowledgeEntry:
    """지식 항목 데이터 클래스"""

    id: str
    source: str  # 'github', 'documentation', 'web', 'local'
    category: str  # 'implementation', 'architecture', 'best_practice', 'example'
    title: str
    content: str
    url: str | None = None
    tags: list[str] = None
    confidence_score: float = 0.0
    last_updated: float = None
    references: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_updated is None:
            self.last_updated = time.time()
        if self.references is None:
            self.references = []


class LibrarianAgent(BackgroundAgent):
    """
    Librarian Agent: 문서 조사 및 지식 통합 특화 에이전트

    역할:
    - Multi-repo 분석 및 문서 검색
    - 관련 구현 예제 자동 검색
    - 지식 베이스 구축 및 유지
    - 크로스-레퍼런스 생성
    """

    def __init__(self):
        super().__init__("librarian", "Librarian Agent")
        self.knowledge_base: dict[str, KnowledgeEntry] = {}
        self.search_cache: dict[str, list[dict[str, Any]]] = {}
        self.repo_index: dict[str, dict[str, Any]] = {}
        self.confidence_threshold = 0.7

        # Antigravity auth 확인 (Gemini 3 Flash 사용 가능 여부)
        self.has_antigravity_auth = self._check_antigravity_auth()

        # 모델 선택
        self.preferred_model = (
            "gemini-3-flash" if self.has_antigravity_auth else "claude-sonnet-4.5"
        )

        logger.info(f"Librarian Agent initialized with model: {self.preferred_model}")

    def _check_antigravity_auth(self) -> bool:
        """Antigravity 인증 상태 확인"""
        # 실제로는 환경 변수나 설정 파일에서 확인
        # 현재는 시뮬레이션
        return False  # 개발 단계에서는 Claude 사용

    async def execute_cycle(self) -> None:
        """
        Librarian Agent의 주요 실행 로직

        수행 작업:
        1. 지식 베이스 유지보수 (오래된 항목 업데이트)
        2. 새로운 관련 문서/예제 검색
        3. 크로스-레퍼런스 업데이트
        4. 지식 베이스 최적화
        """

        try:
            # 1. 오래된 지식 업데이트
            await self._update_stale_knowledge()

            # 2. 새로운 관련 콘텐츠 검색
            await self._discover_new_content()

            # 3. 크로스-레퍼런스 생성
            await self._generate_cross_references()

            # 4. 지식 베이스 정리
            await self._optimize_knowledge_base()

            logger.info(
                f"Librarian cycle completed. Knowledge base size: {len(self.knowledge_base)}"
            )

        except Exception as e:
            logger.error(f"Librarian cycle error: {e}")
            self.status.error_count += 1

    async def _update_stale_knowledge(self) -> None:
        """오래된 지식 항목 업데이트"""
        current_time = time.time()
        stale_threshold = 7 * 24 * 60 * 60  # 7일

        stale_entries = [
            entry_id
            for entry_id, entry in self.knowledge_base.items()
            if current_time - entry.last_updated > stale_threshold
        ]

        for entry_id in stale_entries[:5]:  # 최대 5개씩 업데이트
            try:
                await self._refresh_knowledge_entry(entry_id)
            except Exception as e:
                logger.warning(f"Failed to refresh knowledge entry {entry_id}: {e}")

        if stale_entries:
            logger.info(f"Updated {min(5, len(stale_entries))} stale knowledge entries")

    async def _refresh_knowledge_entry(self, entry_id: str) -> None:
        """특정 지식 항목 새로고침"""
        entry = self.knowledge_base[entry_id]

        if entry.source == "github":
            # GitHub 저장소 업데이트 확인
            await self._check_repo_updates(entry.url)
        elif entry.source == "web":
            # 웹 문서 업데이트 확인
            await self._check_web_content_updates(entry.url)

        entry.last_updated = time.time()

    async def _discover_new_content(self) -> None:
        """새로운 관련 콘텐츠 검색"""
        # 현재 프로젝트와 관련된 주제들
        topics = [
            "python async patterns",
            "fastapi best practices",
            "ai agent orchestration",
            "trinity score implementation",
            "background agent patterns",
        ]

        for topic in topics:
            try:
                # 검색 캐시 확인
                if topic in self.search_cache:
                    cache_time = self.search_cache[topic].get("timestamp", 0)
                    if time.time() - cache_time < 24 * 60 * 60:  # 24시간 캐시
                        continue

                # 새로운 콘텐츠 검색
                new_entries = await self._search_topic_content(topic)

                # 유망한 항목들 추가
                for entry_data in new_entries[:3]:  # 토픽당 최대 3개
                    await self._add_knowledge_entry(entry_data)

                # 캐시 업데이트
                self.search_cache[topic] = {"timestamp": time.time(), "results": new_entries}

            except Exception as e:
                logger.warning(f"Failed to discover content for topic '{topic}': {e}")

    async def _search_topic_content(self, topic: str) -> list[dict[str, Any]]:
        """특정 토픽에 대한 콘텐츠 검색"""
        # 실제로는 brave_web_search, github_search 등의 도구 활용
        # 현재는 시뮬레이션

        simulated_results = [
            {
                "source": "github",
                "category": "implementation",
                "title": f"{topic} - Example Implementation",
                "content": f"Implementation example for {topic} with best practices",
                "url": f"https://github.com/example/{topic.replace(' ', '-')}",
                "tags": [topic.split()[0], "example"],
                "confidence_score": 0.85,
            },
            {
                "source": "documentation",
                "category": "best_practice",
                "title": f"{topic} - Best Practices Guide",
                "content": f"Comprehensive guide for {topic} implementation",
                "url": f"https://docs.example.com/{topic.replace(' ', '-')}",
                "tags": [topic.split()[0], "guide", "best-practice"],
                "confidence_score": 0.92,
            },
        ]

        return simulated_results

    async def _generate_cross_references(self) -> None:
        """크로스-레퍼런스 생성"""
        # 유사한 항목들 간의 연결 생성
        entries = list(self.knowledge_base.values())

        for i, entry_a in enumerate(entries):
            for entry_b in entries[i + 1 :]:
                if self._are_related(entry_a, entry_b):
                    # 상호 참조 추가
                    if entry_b.id not in entry_a.references:
                        entry_a.references.append(entry_b.id)
                    if entry_a.id not in entry_b.references:
                        entry_b.references.append(entry_a.id)

        logger.info("Cross-references generated between related knowledge entries")

    def _are_related(self, entry_a: KnowledgeEntry, entry_b: KnowledgeEntry) -> bool:
        """두 지식 항목이 관련 있는지 판단"""
        # 태그 기반 유사성 계산
        common_tags = set(entry_a.tags) & set(entry_b.tags)
        if len(common_tags) > 0:
            return True

        # 제목 유사성 (단순 키워드 매칭)
        title_words_a = set(entry_a.title.lower().split())
        title_words_b = set(entry_b.title.lower().split())
        common_words = title_words_a & title_words_b
        return len(common_words) >= 2  # 2개 이상 공통 단어

    async def _optimize_knowledge_base(self) -> None:
        """지식 베이스 최적화"""
        # 낮은 신뢰도 항목 정리
        low_confidence = [
            entry_id
            for entry_id, entry in self.knowledge_base.items()
            if entry.confidence_score < 0.5
        ]

        for entry_id in low_confidence:
            del self.knowledge_base[entry_id]

        # 중복 항목 병합
        await self._merge_duplicate_entries()

        # 캐시 정리
        old_cache_keys = [
            key
            for key, data in self.search_cache.items()
            if time.time() - data.get("timestamp", 0) > 7 * 24 * 60 * 60  # 7일
        ]

        for key in old_cache_keys:
            del self.search_cache[key]

    async def _merge_duplicate_entries(self) -> None:
        """중복 항목 병합"""
        # 간단한 중복 감지 및 병합 로직
        # 실제로는 더 정교한 알고리즘 필요
        pass

    async def _add_knowledge_entry(self, entry_data: dict[str, Any]) -> None:
        """새로운 지식 항목 추가"""
        entry_id = f"{entry_data['source']}_{hash(entry_data['title'])}"

        if entry_id in self.knowledge_base:
            # 기존 항목 업데이트
            existing = self.knowledge_base[entry_id]
            existing.content = entry_data["content"]
            existing.confidence_score = entry_data["confidence_score"]
            existing.last_updated = time.time()
        else:
            # 새 항목 생성
            entry = KnowledgeEntry(
                id=entry_id,
                source=entry_data["source"],
                category=entry_data["category"],
                title=entry_data["title"],
                content=entry_data["content"],
                url=entry_data.get("url"),
                tags=entry_data.get("tags", []),
                confidence_score=entry_data.get("confidence_score", 0.5),
            )
            self.knowledge_base[entry_id] = entry

    async def get_metrics(self) -> dict[str, Any]:
        """Librarian Agent 메트릭 반환"""
        total_entries = len(self.knowledge_base)
        avg_confidence = (
            sum(entry.confidence_score for entry in self.knowledge_base.values()) / total_entries
            if total_entries > 0
            else 0
        )

        # 카테고리별 분포
        category_counts = {}
        for entry in self.knowledge_base.values():
            category_counts[entry.category] = category_counts.get(entry.category, 0) + 1

        # 소스별 분포
        source_counts = {}
        for entry in self.knowledge_base.values():
            source_counts[entry.source] = source_counts.get(entry.source, 0) + 1

        return {
            "agent_type": "librarian",
            "knowledge_base_size": total_entries,
            "avg_confidence_score": avg_confidence,
            "cache_size": len(self.search_cache),
            "category_distribution": category_counts,
            "source_distribution": source_counts,
            "preferred_model": self.preferred_model,
            "antigravity_auth": self.has_antigravity_auth,
        }

    # Public API methods

    async def search_knowledge(
        self, query: str, category: str | None = None, min_confidence: float = 0.0
    ) -> list[KnowledgeEntry]:
        """
        지식 베이스에서 관련 정보 검색

        Args:
            query: 검색 쿼리
            category: 특정 카테고리로 필터링
            min_confidence: 최소 신뢰도 점수

        Returns:
            관련 지식 항목 리스트
        """
        query_lower = query.lower()
        results = []

        for entry in self.knowledge_base.values():
            if entry.confidence_score < min_confidence:
                continue
            if category and entry.category != category:
                continue
            if (
                query_lower in entry.title.lower()
                or query_lower in entry.content.lower()
                or any(query_lower in tag for tag in entry.tags)
            ):
                results.append(entry)

        # 관련도 순으로 정렬 (단순 구현)
        results.sort(key=lambda x: x.confidence_score, reverse=True)
        return results[:10]  # 최대 10개 반환

    async def get_implementation_examples(
        self, technology: str, pattern: str
    ) -> list[KnowledgeEntry]:
        """
        특정 기술/패턴에 대한 구현 예제 검색

        Args:
            technology: 기술명 (예: "fastapi", "asyncio")
            pattern: 패턴 (예: "dependency_injection", "middleware")

        Returns:
            구현 예제 리스트
        """
        query = f"{technology} {pattern} implementation example"
        return await self.search_knowledge(query, category="implementation", min_confidence=0.8)

    async def analyze_repository(self, repo_url: str) -> dict[str, Any]:
        """
        GitHub 저장소 분석

        Args:
            repo_url: 저장소 URL

        Returns:
            분석 결과
        """
        # 실제로는 git clone + 분석 수행
        # 현재는 시뮬레이션

        return {
            "repo_url": repo_url,
            "technologies": ["python", "fastapi", "asyncio"],
            "patterns": ["dependency_injection", "async_patterns"],
            "complexity_score": 7.5,
            "documentation_quality": 8.2,
        }

    async def find_best_practices(self, domain: str) -> list[KnowledgeEntry]:
        """
        특정 도메인의 베스트 프랙티스 검색

        Args:
            domain: 도메인 (예: "api_design", "error_handling")

        Returns:
            베스트 프랙티스 항목 리스트
        """
        return await self.search_knowledge(domain, category="best_practice", min_confidence=0.85)


# 글로벌 인스턴스
librarian_agent = LibrarianAgent()


# 유틸리티 함수들
async def search_knowledge_base(query: str) -> list[KnowledgeEntry]:
    """지식 베이스 검색 유틸리티"""
    return await librarian_agent.search_knowledge(query)


async def get_implementation_examples(tech: str, pattern: str) -> list[KnowledgeEntry]:
    """구현 예제 검색 유틸리티"""
    return await librarian_agent.get_implementation_examples(tech, pattern)


async def analyze_codebase(repo_url: str) -> dict[str, Any]:
    """코드베이스 분석 유틸리티"""
    return await librarian_agent.analyze_repository(repo_url)


if __name__ == "__main__":
    # 직접 실행 시 데모
    async def demo():
        print("🎯 Librarian Agent Phase 80 데모")
        print("=" * 50)

        # 초기화
        agent = LibrarianAgent()

        # 몇 개의 지식 항목 추가
        sample_entries = [
            {
                "source": "github",
                "category": "implementation",
                "title": "FastAPI Async Patterns",
                "content": "Best practices for async patterns in FastAPI applications",
                "url": "https://github.com/example/fastapi-async",
                "tags": ["fastapi", "async", "python"],
                "confidence_score": 0.9,
            },
            {
                "source": "documentation",
                "category": "best_practice",
                "title": "AI Agent Orchestration Patterns",
                "content": "Comprehensive guide to orchestrating multiple AI agents",
                "url": "https://docs.example.com/ai-orchestration",
                "tags": ["ai", "agents", "orchestration"],
                "confidence_score": 0.95,
            },
        ]

        for entry_data in sample_entries:
            await agent._add_knowledge_entry(entry_data)

        # 검색 테스트
        print("\n🔍 지식 검색 테스트:")
        results = await agent.search_knowledge("async patterns")
        for result in results:
            print(f"  • {result.title} (신뢰도: {result.confidence_score:.2f})")

        # 메트릭 출력
        metrics = await agent.get_metrics()
        print("\n📊 Librarian Agent 메트릭:")
        print(f"  • 지식 베이스 크기: {metrics['knowledge_base_size']}")
        print(f"  • 평균 신뢰도: {metrics['avg_confidence_score']:.2f}")
        print(f"  • 선호 모델: {metrics['preferred_model']}")
        print(f"  • Antigravity 인증: {metrics['antigravity_auth']}")

        print("\n✅ Librarian Agent 데모 완료!")

    asyncio.run(demo())
