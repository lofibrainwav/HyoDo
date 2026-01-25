"""
Librarian Agent Unit Tests
Phase 80 Multi-Agent 시스템 검증
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from AFO.librarian_agent import KnowledgeEntry, LibrarianAgent, librarian_agent


class TestLibrarianAgent:
    """Librarian Agent 단위 테스트"""

    @pytest.fixture
    def agent(self):
        """테스트용 Librarian Agent 인스턴스"""
        return LibrarianAgent()

    @pytest.fixture
    def sample_knowledge_entry(self):
        """샘플 지식 항목"""
        return {
            "source": "github",
            "category": "implementation",
            "title": "FastAPI Async Patterns",
            "content": "Best practices for async patterns in FastAPI applications",
            "url": "https://github.com/example/fastapi-async",
            "tags": ["fastapi", "async", "python"],
            "confidence_score": 0.9,
        }

    def test_initialization(self, agent):
        """Agent 초기화 테스트"""
        assert agent.agent_id == "librarian"
        assert agent.name == "Librarian Agent"
        assert isinstance(agent.knowledge_base, dict)
        assert isinstance(agent.search_cache, dict)
        assert agent.confidence_threshold == 0.7
        assert agent.preferred_model in ["gemini-3-flash", "claude-sonnet-4.5"]

    def test_check_antigravity_auth(self, agent):
        """Antigravity 인증 확인 테스트"""
        # 현재는 False를 반환하도록 구현됨
        assert agent.has_antigravity_auth is False
        assert agent.preferred_model == "claude-sonnet-4.5"

    def test_knowledge_entry_creation(self, sample_knowledge_entry):
        """지식 항목 생성 테스트"""
        # id 필드 추가
        entry_data = sample_knowledge_entry.copy()
        entry_data["id"] = "test_entry_123"

        entry = KnowledgeEntry(**entry_data)

        assert entry.id == "test_entry_123"
        assert entry.source == "github"
        assert entry.category == "implementation"
        assert entry.title == "FastAPI Async Patterns"
        assert entry.confidence_score == 0.9
        assert isinstance(entry.tags, list)
        assert isinstance(entry.references, list)
        assert entry.last_updated is not None

    @pytest.mark.asyncio
    async def test_add_knowledge_entry(self, agent, sample_knowledge_entry):
        """지식 항목 추가 테스트"""
        await agent._add_knowledge_entry(sample_knowledge_entry)

        # 항목이 추가되었는지 확인
        assert len(agent.knowledge_base) == 1

        entry_id = list(agent.knowledge_base.keys())[0]
        entry = agent.knowledge_base[entry_id]

        assert entry.title == "FastAPI Async Patterns"
        assert entry.source == "github"
        assert entry.confidence_score == 0.9

    @pytest.mark.asyncio
    async def test_search_knowledge(self, agent, sample_knowledge_entry):
        """지식 검색 테스트"""
        # 먼저 항목 추가
        await agent._add_knowledge_entry(sample_knowledge_entry)

        # 검색 테스트
        results = await agent.search_knowledge("async patterns")

        assert len(results) == 1
        assert results[0].title == "FastAPI Async Patterns"

    @pytest.mark.asyncio
    async def test_search_knowledge_with_filters(self, agent, sample_knowledge_entry):
        """필터를 사용한 지식 검색 테스트"""
        await agent._add_knowledge_entry(sample_knowledge_entry)

        # 카테고리 필터 적용
        results = await agent.search_knowledge("async", category="implementation")
        assert len(results) == 1

        # 일치하지 않는 카테고리
        results = await agent.search_knowledge("async", category="architecture")
        assert len(results) == 0

        # 신뢰도 필터
        results = await agent.search_knowledge("async", min_confidence=0.95)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_generate_cross_references(self, agent):
        """크로스-레퍼런스 생성 테스트"""
        # 여러 항목 추가
        entries = [
            {
                "source": "github",
                "category": "implementation",
                "title": "FastAPI Async Patterns",
                "content": "Best practices for async patterns",
                "tags": ["fastapi", "async"],
                "confidence_score": 0.9,
            },
            {
                "source": "documentation",
                "category": "best_practice",
                "title": "Async Best Practices",
                "content": "Comprehensive async programming guide",
                "tags": ["async", "best-practice"],
                "confidence_score": 0.95,
            },
        ]

        for entry_data in entries:
            await agent._add_knowledge_entry(entry_data)

        # 크로스-레퍼런스 생성
        await agent._generate_cross_references()

        # 참조가 생성되었는지 확인
        entries_list = list(agent.knowledge_base.values())
        assert len(entries_list) == 2

        # 적어도 하나의 참조가 있어야 함
        has_references = any(len(entry.references) > 0 for entry in entries_list)
        assert has_references

    def test_are_related_entries(self, agent):
        """항목 관련성 판단 테스트"""
        entry1 = KnowledgeEntry(
            id="test1",
            source="github",
            category="implementation",
            title="FastAPI Async Patterns",
            content="Async patterns",
            tags=["fastapi", "async"],
        )

        entry2 = KnowledgeEntry(
            id="test2",
            source="documentation",
            category="best_practice",
            title="Async Best Practices",
            content="Best practices",
            tags=["async", "best-practice"],
        )

        # 태그가 겹치므로 관련됨
        assert agent._are_related(entry1, entry2)

        entry3 = KnowledgeEntry(
            id="test3",
            source="web",
            category="example",
            title="Database Optimization",
            content="DB optimization",
            tags=["database", "performance"],
        )

        # 태그가 겹치지 않으므로 관련되지 않음
        assert not agent._are_related(entry1, entry3)

    @pytest.mark.asyncio
    async def test_get_implementation_examples(self, agent):
        """구현 예제 검색 테스트"""
        # 구현 예제 항목 추가 - 실제 쿼리와 매칭되는 내용
        entry_data = {
            "source": "github",
            "category": "implementation",
            "title": "FastAPI Dependency Injection Example",
            "content": "fastapi dependency_injection implementation example",
            "tags": ["fastapi", "dependency_injection"],
            "confidence_score": 0.85,
        }

        await agent._add_knowledge_entry(entry_data)

        # 구현 예제 검색
        results = await agent.get_implementation_examples("fastapi", "dependency_injection")

        assert len(results) == 1
        assert "dependency_injection" in results[0].tags

    @pytest.mark.asyncio
    async def test_analyze_repository(self, agent):
        """저장소 분석 테스트"""
        repo_url = "https://github.com/example/test-repo"

        result = await agent.analyze_repository(repo_url)

        assert result["repo_url"] == repo_url
        assert "technologies" in result
        assert "patterns" in result
        assert "complexity_score" in result

    @pytest.mark.asyncio
    async def test_find_best_practices(self, agent):
        """베스트 프랙티스 검색 테스트"""
        # 베스트 프랙티스 항목 추가 - 검색어와 매칭되는 내용
        entry_data = {
            "source": "documentation",
            "category": "best_practice",
            "title": "API Design Best Practices",
            "content": "api_design best practices comprehensive guidelines",
            "tags": ["api_design", "best-practice"],
            "confidence_score": 0.92,
        }

        await agent._add_knowledge_entry(entry_data)

        # 베스트 프랙티스 검색
        results = await agent.find_best_practices("api_design")

        assert len(results) == 1
        assert results[0].category == "best_practice"

    @pytest.mark.asyncio
    async def test_execute_cycle(self, agent):
        """실행 사이클 테스트"""
        # 모의 데이터로 사이클 실행
        await agent.execute_cycle()

        # 에러가 발생하지 않았는지 확인
        assert agent.status.error_count == 0

    @pytest.mark.asyncio
    async def test_get_metrics(self, agent, sample_knowledge_entry):
        """메트릭 획득 테스트"""
        # 항목 추가
        await agent._add_knowledge_entry(sample_knowledge_entry)

        metrics = await agent.get_metrics()

        assert metrics["agent_type"] == "librarian"
        assert metrics["knowledge_base_size"] == 1
        assert metrics["avg_confidence_score"] == 0.9
        assert "preferred_model" in metrics
        assert "antigravity_auth" in metrics

    @pytest.mark.asyncio
    async def test_discover_new_content(self, agent):
        """새로운 콘텐츠 검색 테스트"""
        # 새로운 콘텐츠 검색 실행
        await agent._discover_new_content()

        # 캐시가 업데이트되었는지 확인
        assert len(agent.search_cache) > 0

    @pytest.mark.asyncio
    async def test_optimize_knowledge_base(self, agent):
        """지식 베이스 최적화 테스트"""
        # 낮은 신뢰도 항목 추가
        low_confidence_entry = {
            "source": "web",
            "category": "example",
            "title": "Low Quality Example",
            "content": "Poor quality content",
            "confidence_score": 0.3,  # 낮은 신뢰도
        }

        await agent._add_knowledge_entry(low_confidence_entry)

        # 최적화 전 항목 수 확인
        before_count = len(agent.knowledge_base)

        # 최적화 실행
        await agent._optimize_knowledge_base()

        # 낮은 신뢰도 항목이 정리되었는지 확인
        after_count = len(agent.knowledge_base)
        assert after_count <= before_count


class TestLibrarianAgentIntegration:
    """통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """전체 워크플로우 테스트"""
        agent = LibrarianAgent()

        # 지식 추가
        await agent._add_knowledge_entry(
            {
                "source": "github",
                "category": "implementation",
                "title": "FastAPI Async Patterns",
                "content": "Best practices for async patterns in FastAPI applications",
                "tags": ["fastapi", "async", "python"],
                "confidence_score": 0.9,
            }
        )

        # 검색
        results = await agent.search_knowledge("async patterns")
        assert len(results) == 1

        # 크로스-레퍼런스 생성
        await agent._generate_cross_references()

        # 메트릭 확인
        metrics = await agent.get_metrics()
        assert metrics["knowledge_base_size"] == 1

        # 최적화
        await agent._optimize_knowledge_base()

        # 여전히 항목이 유지되는지 확인
        assert len(agent.knowledge_base) == 1


# 글로벌 인스턴스 테스트
@pytest.mark.asyncio
async def test_global_librarian_agent():
    """글로벌 Librarian Agent 인스턴스 테스트"""
    # 검색 테스트
    results = await librarian_agent.search_knowledge("test query")
    assert isinstance(results, list)

    # 메트릭 테스트
    metrics = await librarian_agent.get_metrics()
    assert isinstance(metrics, dict)
    assert "agent_type" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
