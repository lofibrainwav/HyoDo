# Trinity Score: 95.0 (Obsidian Librarian - Knowledge Curator)
"""
옵시디언 사서 시스템 (Obsidian Librarian System)

AFO 왕국의 기록관이자 지식 큐레이터
Trinity 철학 기반 지식 관리 및 학습 지원 시스템

역할:
- 모든 지식의 체계적 기록 및 분류 (孝 - Serenity)
- Trinity 철학 기반 지식 구조화 (眞善美 - Truth, Goodness, Beauty)
- 실시간 지식 갱신 및 검증 (永 - Eternity)
- 사서-학습자 간 지식 중개 (美 - Beauty)
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from AFO.services.context7_service import get_context7_instance
from AFO.services.obsidian_types import (
    Document,
    DocumentList,
    GraphNode,
    LearningMaterialInfo,
    LearningPathResult,
    LearningPhase,
    LibrarianInitStatus,
    LibrarianStatus,
    RecordingResult,
    SessionData,
    TrinityDistribution,
)

logger = logging.getLogger(__name__)


class ObsidianLibrarian:
    """옵시디언 사서 - 지식 관리 및 학습 지원"""

    def __init__(self) -> None:
        self.context7 = get_context7_instance()
        self.obsidian_vault = Path("docs")  # 옵시디언 볼트 경로
        self.knowledge_graph: dict[str, Any] = {}
        self.trinity_categories = {
            "truth": [],  # 眞 - 기술적 확실성 (Truth)
            "goodness": [],  # 善 - 윤리·안정성 (Goodness)
            "beauty": [],  # 美 - 단순함·우아함 (Beauty)
            "serenity": [],  # 孝 - 평온·연속성 (Serenity)
            "eternity": [],  # 永 - 영속성·레거시 (Eternity)
        }

    async def initialize_librarian(self) -> LibrarianInitStatus:
        """사서 시스템 초기화 및 지식 베이스 구축"""
        try:
            # Context7에서 모든 문서 로드
            all_documents = await self.context7.list_all_documents()

            # Trinity 철학 기반 분류
            for doc in all_documents.get("items", []):
                trinity_category = self._classify_document_by_trinity(doc)
                self.trinity_categories[trinity_category].append(doc)

            # 지식 그래프 구축
            self.knowledge_graph = await self._build_knowledge_graph(all_documents)

            logger.info(
                f"✅ 옵시디언 사서 초기화 완료 - {len(all_documents.get('items', []))}개 문서 분류됨"
            )

            return {
                "status": "initialized",
                "total_documents": len(all_documents.get("items", [])),
                "trinity_distribution": {k: len(v) for k, v in self.trinity_categories.items()},
                "knowledge_graph_nodes": len(self.knowledge_graph),
            }

        except Exception as e:
            logger.error(f"옵시디언 사서 초기화 실패: {e}")
            return {"status": "failed", "error": str(e)}

    def _classify_document_by_trinity(self, document: Document) -> str:
        """Trinity 철학 기반 문서 분류"""
        content = document.get("content", "").lower()
        title = document.get("title", "").lower()
        keywords = document.get("keywords", [])
        tags = document.get("tags", [])

        # 키워드 및 태그 결합
        all_keywords = set(keywords + tags)

        # 眞 (Truth) - 기술적 확실성
        truth_keywords = {
            "architecture",
            "code",
            "api",
            "database",
            "infrastructure",
            "algorithm",
            "implementation",
            "technical",
            "system",
            "framework",
            "langgraph",
            "chancellor",
            "graph",
            "node",
            "workflow",
        }
        if any(k in content or k in title or k in all_keywords for k in truth_keywords):
            return "truth"

        # 善 (Goodness) - 윤리·안정성
        goodness_keywords = {
            "security",
            "testing",
            "monitoring",
            "stability",
            "reliability",
            "validation",
            "verification",
            "audit",
            "compliance",
            "safety",
            "error",
            "handling",
            "robust",
            "resilient",
            "trustworthy",
        }
        if any(k in content or k in title or k in all_keywords for k in goodness_keywords):
            return "goodness"

        # 美 (Beauty) - 단순함·우아함
        beauty_keywords = {
            "ui",
            "ux",
            "design",
            "interface",
            "user",
            "experience",
            "simplicity",
            "elegant",
            "clean",
            "intuitive",
            "beautiful",
            "harmony",
            "aesthetic",
            "polish",
            "refined",
        }
        if any(k in content or k in title or k in all_keywords for k in beauty_keywords):
            return "beauty"

        # 孝 (Serenity) - 평온·연속성
        serenity_keywords = {
            "process",
            "workflow",
            "consistency",
            "harmony",
            "balance",
            "collaboration",
            "integration",
            "coordination",
            "orchestration",
            "continuous",
            "deployment",
            "pipeline",
        }
        if any(k in content or k in title or k in all_keywords for k in serenity_keywords):
            return "serenity"

        # 永 (Eternity) - 영속성·레거시
        eternity_keywords = {
            "legacy",
            "migration",
            "evolution",
            "history",
            "preservation",
            "documentation",
            "knowledge",
            "archive",
            "maintenance",
            "sustainability",
            "longevity",
            "permanence",
            "tradition",
            "heritage",
        }
        if any(k in content or k in title or k in all_keywords for k in eternity_keywords):
            return "eternity"

        # 기본 분류: serenity (평온·연속성)
        return "serenity"

    async def _build_knowledge_graph(self, documents: DocumentList) -> dict[str, GraphNode]:
        """지식 그래프 구축"""
        graph = {}

        for doc in documents.get("items", []):
            doc_id = doc.get("id")
            if not doc_id:
                continue

            # 문서 노드 생성
            graph[doc_id] = {
                "type": "document",
                "title": doc.get("title", ""),
                "category": doc.get("category", ""),
                "trinity_category": self._classify_document_by_trinity(doc),
                "keywords": doc.get("keywords", []),
                "tags": doc.get("tags", []),
                "connections": [],
            }

            # 연결 관계 구축 (키워드 기반)
            keywords = set(doc.get("keywords", []) + doc.get("tags", []))
            for other_id, other_doc in graph.items():
                if other_id == doc_id:
                    continue

                other_keywords = set(other_doc.get("keywords", []) + other_doc.get("tags", []))
                overlap = keywords & other_keywords

                if overlap:
                    # 연결 강도 계산
                    strength = len(overlap) / max(len(keywords), len(other_keywords), 1)
                    if strength > 0.1:  # 10% 이상 겹치면 연결
                        graph[doc_id]["connections"].append(
                            {
                                "target_id": other_id,
                                "strength": strength,
                                "shared_keywords": list(overlap),
                            }
                        )

        return graph

    async def generate_learning_path(
        self, topic: str, learner_level: str = "intermediate"
    ) -> LearningPathResult:
        """주제별 개인화된 학습 경로 생성"""
        try:
            # Context7으로 관련 지식 검색
            search_results = await self.context7.retrieve_context(topic, limit=20)

            learning_materials = []
            for doc in search_results.get("results", []):
                trinity_category = self._classify_document_by_trinity(doc)

                # 학습 난이도 평가
                complexity_score = self._assess_document_complexity(doc)

                # 학습 우선순위 계산 (Trinity + 난이도 기반)
                trinity_priority = self._get_trinity_priority(trinity_category)
                priority_score = trinity_priority * 0.7 + (1 - complexity_score) * 0.3

                learning_material = {
                    "id": doc.get("id"),
                    "title": doc.get("title"),
                    "trinity_category": trinity_category,
                    "complexity_score": complexity_score,
                    "priority_score": priority_score,
                    "relevance_score": doc.get("score", 0),
                    "preview": (
                        doc.get("content", "")[:200] + "..."
                        if len(doc.get("content", "")) > 200
                        else doc.get("content", "")
                    ),
                    "estimated_read_time": self._estimate_read_time(doc),
                    "prerequisites": self._identify_prerequisites(doc),
                    "learning_objectives": self._extract_learning_objectives(doc),
                }

                learning_materials.append(learning_material)

            # 우선순위 및 난이도별 정렬
            learning_materials.sort(key=lambda x: (-x["priority_score"], x["complexity_score"]))

            # 학습자 레벨에 맞는 필터링
            filtered_materials = self._filter_by_learner_level(learning_materials, learner_level)

            # 학습 경로 구조화
            learning_path = self._structure_learning_path(filtered_materials, topic)

            return {
                "topic": topic,
                "learner_level": learner_level,
                "total_materials": len(learning_materials),
                "filtered_materials": len(filtered_materials),
                "learning_path": learning_path,
                "estimated_total_time": sum(
                    m.get("estimated_read_time", 0) for m in filtered_materials
                ),
                "trinity_distribution": self._analyze_trinity_distribution(filtered_materials),
            }

        except Exception as e:
            logger.error(f"학습 경로 생성 실패: {e}")
            return {"error": f"학습 경로 생성 실패: {e}"}

    def _assess_document_complexity(self, document: Document) -> float:
        """문서 복잡도 평가 (0-1)"""
        content = document.get("content", "")
        content_length = len(content)

        # 길이 기반 복잡도
        if content_length > 10000:
            base_complexity = 0.8
        elif content_length > 5000:
            base_complexity = 0.6
        elif content_length > 2000:
            base_complexity = 0.4
        else:
            base_complexity = 0.2

        # 기술 용어 밀도 분석
        technical_terms = [
            "architecture",
            "algorithm",
            "implementation",
            "infrastructure",
            "asynchronous",
            "concurrent",
            "distributed",
            "optimization",
            "abstraction",
            "polymorphism",
            "inheritance",
            "composition",
        ]

        term_count = sum(1 for term in technical_terms if term in content.lower())
        term_density = term_count / max(len(content.split()), 1) * 100

        # 용어 밀도 기반 조정
        if term_density > 2:
            complexity_adjustment = 0.3
        elif term_density > 1:
            complexity_adjustment = 0.2
        else:
            complexity_adjustment = 0.0

        return min(1.0, base_complexity + complexity_adjustment)

    def _get_trinity_priority(self, trinity_category: str) -> float:
        """Trinity 카테고리별 우선순위 점수"""
        priorities = {
            "truth": 1.0,  # 眞 - 기초 지식 (최고 우선순위)
            "goodness": 0.9,  # 善 - 안정성 (높은 우선순위)
            "beauty": 0.7,  # 美 - 사용성 (중간 우선순위)
            "serenity": 0.8,  # 孝 - 조화 (중간-높은 우선순위)
            "eternity": 0.6,  # 永 - 유지보수 (낮은 우선순위)
        }
        return priorities.get(trinity_category, 0.5)

    def _filter_by_learner_level(
        self, materials: list[LearningMaterialInfo], level: str
    ) -> list[LearningMaterialInfo]:
        """학습자 레벨에 맞는 자료 필터링"""
        if level == "beginner":
            # 초보자: 낮은 복잡도 자료만
            return [m for m in materials if m["complexity_score"] < 0.4]
        elif level == "intermediate":
            # 중급자: 중간 복잡도 자료
            return [m for m in materials if 0.3 <= m["complexity_score"] <= 0.7]
        elif level == "advanced":
            # 고급자: 높은 복잡도 자료 포함
            return [m for m in materials if m["complexity_score"] >= 0.4]
        else:
            # 기본: 모든 자료
            return materials

    def _structure_learning_path(
        self, materials: list[LearningMaterialInfo], topic: str
    ) -> list[LearningPhase]:
        """학습 경로 구조화"""
        structured_path = []

        # 단계별 학습 구조
        phases = [
            {"name": "기초 지식 습득", "trinity_focus": ["truth"], "max_items": 3},
            {
                "name": "안정성 및 신뢰성 학습",
                "trinity_focus": ["goodness"],
                "max_items": 2,
            },
            {
                "name": "사용성 및 디자인 이해",
                "trinity_focus": ["beauty"],
                "max_items": 2,
            },
            {
                "name": "통합 및 조화 학습",
                "trinity_focus": ["serenity"],
                "max_items": 2,
            },
            {
                "name": "지속 가능성 및 유지보수",
                "trinity_focus": ["eternity"],
                "max_items": 2,
            },
        ]

        for phase in phases:
            phase_materials = [
                m for m in materials if m["trinity_category"] in phase["trinity_focus"]
            ][: phase["max_items"]]

            if phase_materials:
                structured_path.append(
                    {
                        "phase": phase["name"],
                        "trinity_focus": phase["trinity_focus"],
                        "materials": phase_materials,
                        "estimated_time": sum(
                            m.get("estimated_read_time", 0) for m in phase_materials
                        ),
                    }
                )

        return structured_path

    def _estimate_read_time(self, document: Document) -> int:
        """읽기 시간 추정 (분)"""
        content = document.get("content", "")
        word_count = len(content.split())

        # 평균 읽기 속도: 분당 200단어
        read_time_minutes = word_count / 200

        # 복잡도에 따른 조정
        complexity = self._assess_document_complexity(document)
        adjustment_factor = 1 + (complexity * 0.5)  # 복잡할수록 더 오래 걸림

        estimated_time = int(read_time_minutes * adjustment_factor)

        # 최소 5분, 최대 120분
        return max(5, min(120, estimated_time))

    def _identify_prerequisites(self, document: Document) -> list[str]:
        """선수 지식 식별"""
        content = document.get("content", "").lower()
        prerequisites = []

        # 기술 스택 기반 선수 지식
        if "python" in content and "fastapi" in content:
            prerequisites.append("Python 기초 프로그래밍")
        if "langgraph" in content:
            prerequisites.append("그래프 기반 워크플로우 이해")
        if "async" in content or "await" in content:
            prerequisites.append("비동기 프로그래밍 개념")
        if "docker" in content:
            prerequisites.append("컨테이너화 및 Docker 기초")

        return prerequisites

    def _extract_learning_objectives(self, document: Document) -> list[str]:
        """학습 목표 추출"""
        content = document.get("content", "")
        objectives = []

        # 내용 기반 학습 목표 추론
        if "architecture" in content.lower():
            objectives.append("시스템 아키텍처 설계 원칙 이해")
        if "security" in content.lower():
            objectives.append("보안 모범 사례 및 구현 방법 학습")
        if "testing" in content.lower():
            objectives.append("효과적인 테스트 전략 및 도구 활용")
        if "performance" in content.lower():
            objectives.append("성능 최적화 기법 및 모니터링 방법 습득")

        return objectives

    def _analyze_trinity_distribution(
        self, materials: list[LearningMaterialInfo]
    ) -> TrinityDistribution:
        """Trinity 분포 분석"""
        distribution = {
            "truth": 0,
            "goodness": 0,
            "beauty": 0,
            "serenity": 0,
            "eternity": 0,
        }

        for material in materials:
            category = material.get("trinity_category", "serenity")
            distribution[category] += 1

        return distribution

    async def record_learning_session(self, session_data: SessionData) -> RecordingResult:
        """학습 세션 기록"""
        try:
            # 옵시디언 파일로 기록
            session_file = (
                self.obsidian_vault / "learning_sessions" / f"session_{session_data['trace_id']}.md"
            )

            session_file.parent.mkdir(parents=True, exist_ok=True)

            # 마크다운 형식으로 기록
            content = f"""# 학습 세션: {session_data["topic"]}

**세션 ID**: {session_data["trace_id"]}
**학습 일시**: {asyncio.get_event_loop().time()}

## 학습 자료
{chr(10).join(f"- {m['title']} ({m['trinity_category']})" for m in session_data.get("materials_used", []))}

## 실행 결과
- **성공 여부**: {session_data.get("execution_result", {}).get("success", "Unknown")}
- **Trinity Score**: {session_data.get("performance_analysis", {}).get("trinity_score", 0):.1f}

## 학습 평가
- **등급**: {session_data.get("assessment", {}).get("overall_grade", "N/A")}
- **개선도**: {session_data.get("assessment", {}).get("improvement", 0):.1f}점

## 성능 분석
- **평균 실행 시간**: {session_data.get("performance_analysis", {}).get("performance_analysis", {}).get("avg_execution_time", 0):.2f}초
- **성공률**: {session_data.get("performance_analysis", {}).get("performance_analysis", {}).get("success_rate", 0):.1%}

## 개선 권고사항
{chr(10).join(f"- {rec}" for rec in session_data.get("recommendations", []))}
"""

            with open(session_file, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"✅ 학습 세션 기록 완료: {session_file}")

            return {
                "status": "recorded",
                "file_path": str(session_file),
                "session_id": session_data["trace_id"],
            }

        except Exception as e:
            logger.error(f"학습 세션 기록 실패: {e}")
            return {"status": "failed", "error": str(e)}

    async def get_librarian_status(self) -> LibrarianStatus:
        """사서 시스템 상태 조회"""
        return {
            "status": "active",
            "trinity_categories": {k: len(v) for k, v in self.trinity_categories.items()},
            "knowledge_graph_size": len(self.knowledge_graph),
            "obsidian_vault_path": str(self.obsidian_vault),
            "context7_integration": self.context7 is not None,
        }


# 싱글톤 인스턴스
obsidian_librarian = ObsidianLibrarian()


async def get_obsidian_librarian() -> ObsidianLibrarian:
    """옵시디언 사서 인스턴스 조회 (싱글톤)"""
    return obsidian_librarian


async def initialize_obsidian_librarian() -> LibrarianInitStatus:
    """옵시디언 사서 시스템 초기화"""
    try:
        return await obsidian_librarian.initialize_librarian()
    except Exception as e:
        logger.error(f"옵시디언 사서 초기화 실패: {e}")
        return {"status": "failed", "error": str(e)}
