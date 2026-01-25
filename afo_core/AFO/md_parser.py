from __future__ import annotations

import logging
import re
import sys
from collections import Counter

logger = logging.getLogger(__name__)
from dataclasses import dataclass

"""
MD 파서: 형님이 작성한 MD 파일을 파싱하여 티켓 생성 데이터로 변환
MD→티켓 자동화의 핵심 컴포넌트
"""


@dataclass
class ParsedMD:
    """파싱된 MD 데이터"""

    goal: str = ""
    files_to_create: list[str] | None = None
    files_to_update: list[str] | None = None
    raw_notes: str = ""
    constraints: list[str] | None = None

    def __post_init__(self) -> None:
        if self.files_to_create is None:
            self.files_to_create = []
        if self.files_to_update is None:
            self.files_to_update = []
        if self.constraints is None:
            self.constraints = []


class MDParser:
    """
    MD 파일 파서
    형님이 사용하는 표준 포맷을 파싱하여 구조화된 데이터로 변환
    """

    def __init__(self) -> None:
        # 정규식 패턴들 - 대괄호 필수
        self.patterns = {
            "goal": re.compile(
                r"^\[GOAL\]\s*\n(.*?)(?=\n\[|\Z)",
                re.MULTILINE | re.IGNORECASE | re.DOTALL,
            ),
            "files_to_create": re.compile(
                r"^\[FILES TO CREATE/UPDATE\]\s*\n(.*?)(?=\n\[|\Z)",
                re.MULTILINE | re.IGNORECASE | re.DOTALL,
            ),
            "raw_notes": re.compile(
                r"^\[RAW NOTES\]\s*\n(.*?)(?=\n\[|\Z)",
                re.MULTILINE | re.IGNORECASE | re.DOTALL,
            ),
            "constraints": re.compile(
                r"^\[CONSTRAINTS\]\s*\n(.*?)(?=\Z)",
                re.MULTILINE | re.IGNORECASE | re.DOTALL,
            ),
        }

    def parse_md(self, content: str) -> ParsedMD:
        """
        MD 콘텐츠를 파싱하여 구조화된 데이터로 변환

        Args:
            content: MD 파일의 전체 내용

        Returns:
            ParsedMD: 파싱된 구조화 데이터
        """
        parsed = ParsedMD()

        # 각 섹션 파싱
        parsed.goal = self._extract_section(content, "goal")
        files_section = self._extract_section(content, "files_to_create")
        parsed.raw_notes = self._extract_section(content, "raw_notes")
        constraints_section = self._extract_section(content, "constraints")

        # 파일 목록 파싱
        parsed.files_to_create, parsed.files_to_update = self._parse_files_section(files_section)

        # 제약사항 파싱
        parsed.constraints = self._parse_constraints_section(constraints_section)

        return parsed

    def _extract_section(self, content: str, section_name: str) -> str:
        """특정 섹션을 추출"""
        pattern = self.patterns.get(section_name)
        if not pattern:
            return ""

        match = pattern.search(content)
        if match:
            text = match.group(1).strip()
            # 마크다운 헤더와 리스트 심볼 제거
            text = re.sub(r"^[#*+-]\s*", "", text, flags=re.MULTILINE)
            return text

        return ""

    def _parse_files_section(self, files_content: str) -> tuple[list[str], list[str]]:
        """파일 섹션을 파싱하여 생성/업데이트 파일 목록으로 분리"""
        create_files = []
        update_files = []

        if not files_content:
            return create_files, update_files

        lines = files_content.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 파일 경로 추출 (마크다운 리스트 심볼 제거)
            file_path = re.sub(r"^[#*+-]\s*", "", line).strip()

            if file_path:
                # 간단한 휴리스틱: 새 파일은 보통 docs/나 새로운 모듈
                if (
                    "docs/" in file_path
                    or "new" in file_path.lower()
                    or not self._file_exists_in_repo(file_path)
                ):
                    create_files.append(file_path)
                else:
                    update_files.append(file_path)

        return create_files, update_files

    def _parse_constraints_section(self, constraints_content: str) -> list[str]:
        """제약사항 섹션을 파싱"""
        constraints = []

        if not constraints_content:
            return constraints

        lines = constraints_content.split("\n")

        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # 마크다운 리스트 심볼 제거
                constraint = re.sub(r"^[#*+-]\s*", "", line).strip()
                if constraint:
                    constraints.append(constraint)

        return constraints

    def _file_exists_in_repo(self, file_path: str) -> bool:
        """파일이 리포지토리에 존재하는지 확인 (간단한 체크)"""
        # 실제 구현에서는 파일 시스템 체크
        # 여기서는 간단한 휴리스틱만 사용
        return False  # 보수적으로 새 파일로 취급

    def extract_keywords(self, text: str) -> list[str]:
        """텍스트에서 키워드 추출 (매칭 엔진용)"""
        keywords = []

        # 명사구 추출 (간단한 구현)
        # 실제로는 더 정교한 NLP 처리 필요
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())

        # 불용어 제거
        stopwords = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "an",
            "a",
        }
        keywords = [word for word in words if word not in stopwords]

        # 빈도 기반 필터링 (가장 빈번한 단어들)

        word_counts = Counter(keywords)
        top_keywords = [word for word, count in word_counts.most_common(10) if count > 1]

        return top_keywords

    def validate_md_format(self, content: str) -> list[str]:
        """MD 포맷 유효성 검증"""
        errors = []

        required_sections = ["goal"]
        recommended_sections = ["files_to_create", "raw_notes"]

        content_lower = content.lower()

        for section in required_sections:
            if f"[{section}]" not in content_lower and f"## {section}" not in content_lower:
                errors.append(f"Required section '{section}' is missing")

        for section in recommended_sections:
            if f"[{section}]" not in content_lower and f"## {section}" not in content_lower:
                errors.append(f"Recommended section '{section}' is missing")

        return errors


def main() -> None:
    """CLI 테스트"""

    if len(sys.argv) < 2:
        logger.info("Usage: python md_parser.py <md_file>")
        return

    md_file = sys.argv[1]

    try:
        with open(md_file, encoding="utf-8") as f:
            content = f.read()

        parser = MDParser()
        parsed = parser.parse_md(content)

        logger.info("=== Parsed MD ===")
        logger.info(f"Goal: {parsed.goal}")
        logger.info(f"Files to create: {parsed.files_to_create}")
        logger.info(f"Files to update: {parsed.files_to_update}")
        logger.info(f"Raw notes: {parsed.raw_notes}")
        logger.info(f"Constraints: {parsed.constraints}")

        # 키워드 추출 테스트
        all_text = f"{parsed.goal} {parsed.raw_notes}"
        keywords = parser.extract_keywords(all_text)
        logger.info(f"Keywords: {keywords}")

        # 유효성 검증
        errors = parser.validate_md_format(content)
        if errors:
            logger.info(f"Validation errors: {errors}")

    except Exception as e:
        logger.info(f"Error: {e}")


if __name__ == "__main__":
    main()
