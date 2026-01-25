"""
🎯 AFO Kingdom Explorer Agent (Phase 80)
코드베이스 탐색 및 패턴 분석 특화 에이전트

작성자: 승상 (Chancellor)
날짜: 2026-01-22

역할: 빠른 코드베이스 탐색, 패턴 매칭, 의존성 그래프 생성
모델: Grok Code (빠른 탐색용)
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from AFO.background_agents import BackgroundAgent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CodePattern:
    """코드 패턴 데이터 클래스"""

    pattern_id: str
    pattern_type: str  # 'function', 'class', 'import', 'decorator', 'async'
    name: str
    file_path: str
    line_number: int
    complexity_score: float
    dependencies: list[str]
    references: list[str]
    tags: list[str]


@dataclass
class FileAnalysis:
    """파일 분석 결과 데이터 클래스"""

    file_path: str
    language: str
    lines_of_code: int
    complexity_score: float
    patterns_found: list[CodePattern]
    dependencies: list[str]
    imports: list[str]
    functions: list[str]
    classes: list[str]


class ExplorerAgent(BackgroundAgent):
    """
    Explorer Agent: 코드베이스 탐색 및 패턴 분석 특화 에이전트

    역할:
    - 파일 시스템 및 코드 구조 분석
    - 패턴 매칭 및 코드 탐색
    - 의존성 그래프 생성
    - 코드 메트릭 계산
    """

    def __init__(self):
        super().__init__("explorer", "Explorer Agent")
        self.file_index: dict[str, FileAnalysis] = {}
        self.pattern_index: dict[str, list[CodePattern]] = {}
        self.dependency_graph: dict[str, set[str]] = {}
        self.search_cache: dict[str, list[dict[str, Any]]] = {}

        # 지원하는 언어 및 패턴
        self.supported_languages = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
        }

        # 코드 패턴 정규식 (Python 중심)
        self.patterns = {
            "function": re.compile(r"^\s*def\s+(\w+)\s*\("),
            "async_function": re.compile(r"^\s*async\s+def\s+(\w+)\s*\("),
            "class": re.compile(r"^\s*class\s+(\w+)"),
            "import": re.compile(r"^\s*(?:from\s+\w+\s+)?import\s+(.+)"),
            "decorator": re.compile(r"^\s*@(\w+)"),
            "method": re.compile(r"^\s*def\s+(\w+)\s*\(self"),
        }

        logger.info("Explorer Agent initialized with Grok Code model")

    async def execute_cycle(self) -> None:
        """
        Explorer Agent의 주요 실행 로직

        수행 작업:
        1. 코드베이스 스캔 및 인덱싱
        2. 패턴 분석 및 메트릭 계산
        3. 의존성 그래프 업데이트
        4. 코드 품질 분석
        """

        try:
            # 1. 코드베이스 스캔
            await self._scan_codebase()

            # 2. 패턴 분석
            await self._analyze_patterns()

            # 3. 의존성 분석
            await self._analyze_dependencies()

            # 4. 메트릭 계산
            await self._calculate_metrics()

            logger.info(f"Explorer cycle completed. Indexed {len(self.file_index)} files")

        except Exception as e:
            logger.error(f"Explorer cycle error: {e}")
            self.status.error_count += 1

    async def _scan_codebase(self) -> None:
        """코드베이스 스캔 및 기본 분석"""
        # 실제로는 list_files 도구 활용
        # 현재는 시뮬레이션

        # AFO Kingdom 프로젝트 구조 기반 시뮬레이션
        project_files = [
            "packages/afo-core/AFO/__init__.py",
            "packages/afo-core/AFO/background_agents.py",
            "packages/afo-core/AFO/librarian_agent.py",
            "packages/afo-core/api/api_server.py",
            "packages/dashboard/src/app/page.tsx",
            "packages/dashboard/src/components/Button.tsx",
        ]

        for file_path in project_files:
            if file_path not in self.file_index:
                try:
                    analysis = await self._analyze_file(file_path)
                    self.file_index[file_path] = analysis
                except Exception as e:
                    logger.warning(f"Failed to analyze {file_path}: {e}")

    async def _analyze_file(self, file_path: str) -> FileAnalysis:
        """단일 파일 분석"""
        # 실제로는 read_file 도구 활용
        # 현재는 시뮬레이션

        ext = Path(file_path).suffix
        language = self.supported_languages.get(ext, "unknown")

        # 시뮬레이션 데이터
        if language == "python":
            lines_of_code = 150
            complexity_score = 7.2
            patterns = await self._extract_patterns(file_path, language)
            dependencies = ["asyncio", "typing", "dataclasses"]
            imports = ["from typing import List, Dict, Optional", "import asyncio"]
            functions = ["execute_cycle", "get_metrics", "start_background_task"]
            classes = ["BackgroundAgent", "AgentStatus"]
        elif language in ["typescript", "javascript"]:
            lines_of_code = 120
            complexity_score = 6.8
            patterns = []
            dependencies = ["react", "next"]
            imports = ["import React from 'react'", "import { useState } from 'react'"]
            functions = ["handleClick", "useEffect"]
            classes = ["Button", "Component"]
        else:
            lines_of_code = 0
            complexity_score = 0.0
            patterns = []
            dependencies = []
            imports = []
            functions = []
            classes = []

        return FileAnalysis(
            file_path=file_path,
            language=language,
            lines_of_code=lines_of_code,
            complexity_score=complexity_score,
            patterns_found=patterns,
            dependencies=dependencies,
            imports=imports,
            functions=functions,
            classes=classes,
        )

    async def _extract_patterns(self, file_path: str, language: str) -> list[CodePattern]:
        """파일에서 코드 패턴 추출"""
        patterns = []

        # 실제로는 파일 내용 읽어서 분석
        # 현재는 시뮬레이션

        if "background_agents.py" in file_path:
            patterns.extend(
                [
                    CodePattern(
                        pattern_id=f"{file_path}_class_BackgroundAgent",
                        pattern_type="class",
                        name="BackgroundAgent",
                        file_path=file_path,
                        line_number=25,
                        complexity_score=8.5,
                        dependencies=["ABC", "asyncio"],
                        references=[],
                        tags=["abstract", "base_class"],
                    ),
                    CodePattern(
                        pattern_id=f"{file_path}_function_start_background_task",
                        pattern_type="async_function",
                        name="start_background_task",
                        file_path=file_path,
                        line_number=67,
                        complexity_score=6.2,
                        dependencies=["asyncio.sleep"],
                        references=[],
                        tags=["async", "lifecycle"],
                    ),
                ]
            )

        return patterns

    async def _analyze_patterns(self) -> None:
        """패턴 분석 및 인덱싱"""
        # 패턴 타입별로 그룹화
        for file_analysis in self.file_index.values():
            for pattern in file_analysis.patterns_found:
                if pattern.pattern_type not in self.pattern_index:
                    self.pattern_index[pattern.pattern_type] = []
                self.pattern_index[pattern.pattern_type].append(pattern)

        # 패턴 간 참조 관계 구축
        await self._build_pattern_references()

    async def _build_pattern_references(self) -> None:
        """패턴 간 참조 관계 구축"""
        # 클래스-메서드 관계 구축
        classes = self.pattern_index.get("class", [])
        methods = self.pattern_index.get("method", [])

        for method in methods:
            for class_pattern in classes:
                if method.file_path == class_pattern.file_path:
                    if method.pattern_id not in class_pattern.references:
                        class_pattern.references.append(method.pattern_id)
                    method.dependencies.append(class_pattern.pattern_id)

    async def _analyze_dependencies(self) -> None:
        """의존성 그래프 생성"""
        self.dependency_graph = {}

        for file_analysis in self.file_index.values():
            file_path = file_analysis.file_path
            self.dependency_graph[file_path] = set()

            # 파일 내 의존성
            for dep in file_analysis.dependencies:
                self.dependency_graph[file_path].add(dep)

            # 다른 파일에 대한 참조
            for pattern in file_analysis.patterns_found:
                for ref in pattern.references:
                    # 참조하는 파일 찾기
                    for other_file, other_analysis in self.file_index.items():
                        if any(p.pattern_id == ref for p in other_analysis.patterns_found):
                            self.dependency_graph[file_path].add(other_file)

    async def _calculate_metrics(self) -> None:
        """코드 메트릭 계산"""
        total_files = len(self.file_index)
        total_lines = sum(f.lines_of_code for f in self.file_index.values())
        avg_complexity = (
            sum(f.complexity_score for f in self.file_index.values()) / total_files
            if total_files > 0
            else 0
        )

        # 언어별 분포
        language_distribution = {}
        for analysis in self.file_index.values():
            language_distribution[analysis.language] = (
                language_distribution.get(analysis.language, 0) + 1
            )

        logger.info(
            f"Code metrics: {total_files} files, {total_lines} lines, "
            f"avg complexity {avg_complexity:.1f}"
        )

    async def get_metrics(self) -> dict[str, Any]:
        """Explorer Agent 메트릭 반환"""
        total_files = len(self.file_index)
        total_patterns = sum(len(patterns) for patterns in self.pattern_index.values())

        # 언어 분포
        language_counts = {}
        for analysis in self.file_index.values():
            language_counts[analysis.language] = language_counts.get(analysis.language, 0) + 1

        # 패턴 타입 분포
        pattern_counts = {}
        for pattern_type, patterns in self.pattern_index.items():
            pattern_counts[pattern_type] = len(patterns)

        return {
            "agent_type": "explorer",
            "files_indexed": total_files,
            "patterns_found": total_patterns,
            "dependencies_mapped": len(self.dependency_graph),
            "language_distribution": language_counts,
            "pattern_distribution": pattern_counts,
            "cache_size": len(self.search_cache),
        }

    # Public API methods

    async def search_code_patterns(
        self, pattern_type: str, name_filter: str | None = None
    ) -> list[CodePattern]:
        """
        코드 패턴 검색

        Args:
            pattern_type: 패턴 타입 ('function', 'class', 'method' 등)
            name_filter: 이름 필터 (선택사항)

        Returns:
            매칭되는 패턴 리스트
        """
        patterns = self.pattern_index.get(pattern_type, [])

        if name_filter:
            patterns = [p for p in patterns if name_filter.lower() in p.name.lower()]

        return patterns[:20]  # 최대 20개 반환

    async def analyze_file_dependencies(self, file_path: str) -> dict[str, Any]:
        """
        파일 의존성 분석

        Args:
            file_path: 분석할 파일 경로

        Returns:
            의존성 분석 결과
        """
        if file_path not in self.file_index:
            return {"error": "File not found in index"}

        analysis = self.file_index[file_path]
        dependencies = list(self.dependency_graph.get(file_path, set()))

        return {
            "file_path": file_path,
            "direct_dependencies": analysis.dependencies,
            "file_dependencies": dependencies,
            "imports": analysis.imports,
            "complexity_score": analysis.complexity_score,
        }

    async def find_similar_patterns(
        self, pattern: CodePattern, threshold: float = 0.7
    ) -> list[CodePattern]:
        """
        유사 패턴 찾기

        Args:
            pattern: 기준 패턴
            threshold: 유사도 임계값

        Returns:
            유사 패턴 리스트
        """
        similar_patterns = []

        # 같은 타입의 모든 패턴과 비교
        candidates = self.pattern_index.get(pattern.pattern_type, [])

        for candidate in candidates:
            if candidate.pattern_id == pattern.pattern_id:
                continue

            # 간단한 유사도 계산 (이름 및 태그 기반)
            name_similarity = self._calculate_name_similarity(pattern.name, candidate.name)
            tag_similarity = len(set(pattern.tags) & set(candidate.tags)) / max(
                len(pattern.tags | candidate.tags), 1
            )

            similarity = (name_similarity + tag_similarity) / 2

            if similarity >= threshold:
                similar_patterns.append(candidate)

        return similar_patterns[:10]

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """이름 유사도 계산 (단순 구현)"""
        # 실제로는 더 정교한 알고리즘 사용 (레벤슈타인 거리 등)
        words1 = set(name1.lower().split("_"))
        words2 = set(name2.lower().split("_"))
        common_words = words1 & words2
        total_words = words1 | words2
        return len(common_words) / len(total_words) if total_words else 0.0

    async def get_code_metrics(self) -> dict[str, Any]:
        """
        전체 코드베이스 메트릭

        Returns:
            코드 메트릭 요약
        """
        total_files = len(self.file_index)
        total_lines = sum(f.lines_of_code for f in self.file_index.values())
        total_functions = sum(len(f.functions) for f in self.file_index.values())
        total_classes = sum(len(f.classes) for f in self.file_index.values())

        avg_complexity = (
            sum(f.complexity_score for f in self.file_index.values()) / total_files
            if total_files > 0
            else 0
        )

        return {
            "total_files": total_files,
            "total_lines_of_code": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "average_complexity": avg_complexity,
            "languages_used": list({f.language for f in self.file_index.values()}),
            "dependency_graph_size": len(self.dependency_graph),
        }

    async def explore_directory(self, directory: str) -> dict[str, Any]:
        """
        디렉토리 탐색 및 분석

        Args:
            directory: 탐색할 디렉토리 경로

        Returns:
            디렉토리 분석 결과
        """
        # 실제로는 list_files 도구 활용
        # 현재는 시뮬레이션

        subdirs = []
        files = []

        if directory == "packages/afo-core":
            subdirs = ["AFO", "api", "infrastructure"]
            files = ["pyproject.toml", "README.md"]
        elif directory == "packages/dashboard":
            subdirs = ["src", "public"]
            files = ["package.json", "next.config.js"]

        return {
            "directory": directory,
            "subdirectories": subdirs,
            "files": files,
            "total_items": len(subdirs) + len(files),
        }


# 글로벌 인스턴스
explorer_agent = ExplorerAgent()


# 유틸리티 함수들
async def search_code_patterns(
    pattern_type: str, name_filter: str | None = None
) -> list[CodePattern]:
    """코드 패턴 검색 유틸리티"""
    return await explorer_agent.search_code_patterns(pattern_type, name_filter)


async def analyze_file_dependencies(file_path: str) -> dict[str, Any]:
    """파일 의존성 분석 유틸리티"""
    return await explorer_agent.analyze_file_dependencies(file_path)


async def get_code_metrics() -> dict[str, Any]:
    """코드 메트릭 조회 유틸리티"""
    return await explorer_agent.get_code_metrics()


async def explore_directory(directory: str) -> dict[str, Any]:
    """디렉토리 탐색 유틸리티"""
    return await explorer_agent.explore_directory(directory)


if __name__ == "__main__":
    # 직접 실행 시 데모
    async def demo():
        print("🎯 Explorer Agent Phase 80 데모")
        print("=" * 50)

        # 초기화
        agent = ExplorerAgent()

        # 코드베이스 스캔 시뮬레이션
        await agent._scan_codebase()

        # 메트릭 출력
        metrics = await agent.get_metrics()
        print("\n📊 Explorer Agent 메트릭:")
        print(f"  • 인덱싱된 파일: {metrics['files_indexed']}개")
        print(f"  • 발견된 패턴: {metrics['patterns_found']}개")
        print(f"  • 의존성 맵핑: {metrics['dependencies_mapped']}개")

        # 코드 패턴 검색 테스트
        print("\n🔍 코드 패턴 검색 테스트:")
        functions = await agent.search_code_patterns("function")
        for func in functions[:3]:
            print(f"  • {func.name} ({func.file_path}:{func.line_number})")

        # 코드 메트릭
        code_metrics = await agent.get_code_metrics()
        print("\n📈 코드베이스 메트릭:")
        print(f"  • 총 파일 수: {code_metrics['total_files']}")
        print(f"  • 총 코드 라인: {code_metrics['total_lines_of_code']}")
        print(f"  • 평균 복잡도: {code_metrics['average_complexity']:.1f}")
        print(f"  • 사용 언어: {', '.join(code_metrics['languages_used'])}")

        print("\n✅ Explorer Agent 데모 완료!")

    asyncio.run(demo())
