"""
매칭 엔진: MD 파싱 결과를 골격 인덱스와 매칭하여 기존 구현 제안
MD→티켓 자동화의 핵심 로직
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from .md_parser import ParsedMD
from .skeleton_index import ModuleInfo, SkeletonIndex


@dataclass
class MatchCandidate:
    """매칭 후보"""

    module: ModuleInfo
    similarity_score: float
    matched_keywords: list[str]
    match_reason: str


@dataclass
class MatchingResult:
    """매칭 결과"""

    candidates: list[MatchCandidate]
    best_match: MatchCandidate | None
    confidence_score: float
    recommendations: list[str]


class MatchingEngine:
    """
    MD 파싱 결과를 골격 인덱스와 매칭하는 엔진
    기존 구현을 재사용하여 티켓 생성을 최적화
    """

    def __init__(self, skeleton_index: SkeletonIndex) -> None:
        self.skeleton_index = skeleton_index
        self.keyword_weights = {
            "authentication": ["auth", "login", "oauth", "jwt", "security"],
            "api": ["api", "endpoint", "rest", "graphql", "http"],
            "database": ["db", "database", "sql", "postgres", "redis", "vector"],
            "frontend": ["ui", "component", "react", "nextjs", "dashboard"],
            "backend": ["server", "api", "fastapi", "service", "logic"],
            "testing": ["test", "pytest", "unittest", "coverage"],
            "documentation": ["docs", "readme", "guide", "tutorial"],
            "configuration": ["config", "settings", "environment", "env"],
            "deployment": ["docker", "kubernetes", "deploy", "ci", "cd"],
            "monitoring": ["health", "metrics", "logging", "observability"],
        }

    def find_candidates(self, parsed_md: ParsedMD) -> MatchingResult:
        """
        파싱된 MD를 기반으로 기존 구현 매칭

        Args:
            parsed_md: 파싱된 MD 데이터

        Returns:
            MatchingResult: 매칭 결과와 추천사항
        """
        # 키워드 추출
        keywords = self._extract_combined_keywords(parsed_md)

        # 모든 모듈에 대해 유사도 계산
        candidates = []
        all_modules = self._get_all_modules()

        for module in all_modules:
            similarity, matched_keywords, reason = self._calculate_similarity(
                keywords, module, parsed_md
            )
            if similarity > 0.1:  # 최소 유사도 threshold
                candidates.append(
                    MatchCandidate(
                        module=module,
                        similarity_score=similarity,
                        matched_keywords=matched_keywords,
                        match_reason=reason,
                    )
                )

        # 유사도 기준 정렬
        candidates.sort(key=lambda x: x.similarity_score, reverse=True)
        candidates = candidates[:10]  # 상위 10개만

        # 최고 매칭과 신뢰도 계산
        best_match = candidates[0] if candidates else None
        confidence_score = best_match.similarity_score if best_match else 0.0

        # 추천사항 생성
        recommendations = self._generate_recommendations(parsed_md, candidates)

        return MatchingResult(
            candidates=candidates,
            best_match=best_match,
            confidence_score=confidence_score,
            recommendations=recommendations,
        )

    def _extract_combined_keywords(self, parsed_md: ParsedMD) -> list[str]:
        """MD에서 키워드 추출 (파서 + 추가 분석)"""
        keywords = []

        # MD 파서의 키워드 추출 활용
        from .md_parser import MDParser

        parser = MDParser()

        # 모든 텍스트에서 키워드 추출
        all_text = f"{parsed_md.goal} {parsed_md.raw_notes}"
        all_files = (parsed_md.files_to_create or []) + (parsed_md.files_to_update or [])
        for file in all_files:
            all_text += f" {file}"

        base_keywords = parser.extract_keywords(all_text)
        keywords.extend(base_keywords)

        # 파일명에서 키워드 추출
        for file_path in all_files:
            file_keywords = self._extract_keywords_from_path(file_path)
            keywords.extend(file_keywords)

        # 제약사항에서 키워드 추출
        for constraint in parsed_md.constraints or []:
            constraint_keywords = parser.extract_keywords(constraint)
            keywords.extend(constraint_keywords)

        # 중복 제거 및 정제
        return list(set(keywords))

    def _extract_keywords_from_path(self, file_path: str) -> list[str]:
        """파일 경로에서 키워드 추출"""
        keywords = []

        # 경로 컴포넌트 분리
        parts = file_path.replace("/", " ").replace("_", " ").replace("-", " ").split()

        for part in parts:
            part = part.lower()
            if len(part) > 2 and part not in ["packages", "docs", "src", "api", "core"]:
                keywords.append(part)

        return keywords

    def _get_all_modules(self) -> list[ModuleInfo]:
        """골격 인덱스에서 모든 모듈 가져오기"""
        all_modules = []

        # 패키지 모듈들
        for folder_modules in self.skeleton_index.packages.values():
            all_modules.extend(folder_modules)

        # 서비스 모듈들
        for folder_modules in self.skeleton_index.services.values():
            all_modules.extend(folder_modules)

        # 설정 파일들
        for folder_modules in self.skeleton_index.configs.values():
            all_modules.extend(folder_modules)

        return all_modules

    def _calculate_similarity(
        self, keywords: list[str], module: ModuleInfo, parsed_md: ParsedMD
    ) -> tuple[float, list[str], str]:
        """
        키워드와 모듈 간 유사도 계산

        Returns:
            (유사도 점수, 매칭된 키워드들, 매칭 이유)
        """
        matched_keywords = []
        score = 0.0
        reasons = []

        # 1. 모듈명/설명과 키워드 매칭
        module_text = f"{module.name} {module.description} {module.path}".lower()

        for keyword in keywords:
            if keyword in module_text:
                matched_keywords.append(keyword)
                score += 0.3  # 기본 매칭 점수

                # 정확한 단어 매칭은 더 높은 점수
                if re.search(r"\b" + re.escape(keyword) + r"\b", module_text):
                    score += 0.2

        # 2. 도메인별 키워드 가중치 적용
        domain_score = self._calculate_domain_score(keywords, module)
        score += domain_score

        # 3. 파일 경로 유사성
        file_score = self._calculate_file_similarity(parsed_md, module)
        score += file_score

        # 4. 의존성 패턴 분석
        dependency_score = self._analyze_dependency_patterns(keywords, module)
        score += dependency_score

        # 매칭 이유 생성
        if matched_keywords:
            reasons.append(f"키워드 매칭: {', '.join(matched_keywords[:3])}")
        if domain_score > 0:
            reasons.append("도메인 관련성 높음")
        if file_score > 0:
            reasons.append("파일 구조 유사")
        if dependency_score > 0:
            reasons.append("의존성 패턴 일치")

        match_reason = "; ".join(reasons) if reasons else "낮은 유사성"

        return min(score, 1.0), matched_keywords, match_reason  # 최대 1.0

    def _calculate_domain_score(self, keywords: list[str], module: ModuleInfo) -> float:
        """도메인별 키워드 가중치 계산"""
        score = 0.0

        for keyword in keywords:
            for domain, domain_keywords in self.keyword_weights.items():
                if keyword in domain_keywords:
                    # 모듈이 해당 도메인과 관련 있는지 체크
                    module_text = f"{module.name} {module.type} {module.path}".lower()
                    if any(domain_kw in module_text for domain_kw in domain_keywords):
                        score += 0.4  # 도메인 매칭 보너스
                        break

        return score

    def _calculate_file_similarity(self, parsed_md: ParsedMD, module: ModuleInfo) -> float:
        """파일 경로 유사성 계산"""
        score = 0.0

        all_files = (parsed_md.files_to_create or []) + (parsed_md.files_to_update or [])
        for file_path in all_files:
            # 경로 구조 유사성
            file_parts = set(file_path.split("/"))
            module_parts = set(module.path.split("/"))

            overlap = len(file_parts & module_parts)
            if overlap > 0:
                score += 0.2 * (overlap / max(len(file_parts), len(module_parts)))

        return min(score, 0.3)  # 최대 0.3

    def _analyze_dependency_patterns(self, keywords: list[str], module: ModuleInfo) -> float:
        """의존성 패턴 분석"""
        score = 0.0

        # 키워드 기반 의존성 예측
        predicted_deps = self._predict_dependencies_from_keywords(keywords)

        # 실제 모듈 의존성과 비교
        for pred_dep in predicted_deps:
            if any(pred_dep in dep for dep in module.dependencies):
                score += 0.25

        return min(score, 0.4)  # 최대 0.4

    def _predict_dependencies_from_keywords(self, keywords: list[str]) -> list[str]:
        """키워드로부터 예상되는 의존성 예측"""
        predicted_deps = []

        # 간단한 규칙 기반 예측
        if "api" in keywords or "fastapi" in keywords:
            predicted_deps.extend(["fastapi", "uvicorn", "pydantic"])
        if "database" in keywords or "postgres" in keywords:
            predicted_deps.extend(["sqlalchemy", "psycopg2"])
        if "redis" in keywords:
            predicted_deps.extend(["redis", "redis-py"])
        if "auth" in keywords or "jwt" in keywords:
            predicted_deps.extend(["pyjwt", "bcrypt"])

        return predicted_deps

    def _generate_recommendations(
        self, parsed_md: ParsedMD, candidates: list[MatchCandidate]
    ) -> list[str]:
        """매칭 결과를 바탕으로 추천사항 생성"""
        recommendations = []

        if not candidates:
            recommendations.append("기존 구현 패턴을 찾을 수 없습니다. 새로운 모듈을 생성하세요.")
            return recommendations

        # 최고 매칭 기반 추천
        best = candidates[0]
        if best.similarity_score > 0.7:
            recommendations.append(f"높은 확률로 {best.module.path} 패턴을 재사용하세요.")
        elif best.similarity_score > 0.4:
            recommendations.append(f"{best.module.path}를 참고하여 새로운 구현을 시작하세요.")
        else:
            recommendations.append("여러 후보를 검토하여 가장 적합한 패턴을 선택하세요.")

        # 파일 생성/업데이트 추천
        if parsed_md.files_to_create:
            recommendations.append(f"새 파일 생성: {', '.join(parsed_md.files_to_create[:3])}")

        if parsed_md.files_to_update:
            recommendations.append(f"기존 파일 수정: {', '.join(parsed_md.files_to_update[:3])}")

        # 제약사항 고려
        if parsed_md.constraints:
            recommendations.append(
                "제약사항을 반드시 준수하세요: " + ", ".join(parsed_md.constraints[:2])
            )

        return recommendations


def main() -> None:
    """CLI 테스트"""
    import sys

    from .skeleton_index import SkeletonIndexer

    if len(sys.argv) < 2:
        logger.info("Usage: python matching_engine.py <md_file>")
        return

    md_file = sys.argv[1]

    try:
        # 골격 인덱스 로드
        indexer = SkeletonIndexer()
        try:
            skeleton_index = indexer.load_index()
            logger.info(f"기존 인덱스 로드됨: {skeleton_index.last_updated}")
        except Exception:
            logger.info("새 인덱스 생성 중...")
            skeleton_index = indexer.scan_folders()
            indexer.save_index(skeleton_index)

        # MD 파싱
        from .md_parser import MDParser

        with open(md_file, encoding="utf-8") as f:
            content = f.read()

        parser = MDParser()
        parsed_md = parser.parse_md(content)

        # 매칭 실행
        engine = MatchingEngine(skeleton_index)
        result = engine.find_candidates(parsed_md)

        logger.info("=== Matching Results ===")
        logger.info(f"Candidates found: {len(result.candidates)}")
        logger.info(f"Confidence score: {result.confidence_score:.2f}")

        if result.best_match:
            logger.info(f"Best match: {result.best_match.module.path}")
            logger.info(f"Similarity: {result.best_match.similarity_score:.2f}")
            logger.info(f"Reason: {result.best_match.match_reason}")

        logger.info("\nRecommendations:")
        for rec in result.recommendations:
            logger.info(f"- {rec}")

    except Exception as e:
        logger.info(f"Error: {e}")


if __name__ == "__main__":
    main()
