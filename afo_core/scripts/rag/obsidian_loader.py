from __future__ import annotations

import re
import site
import sys
from pathlib import Path
from typing import Optional, Union

import frontmatter
from langchain_core.documents import Document

from config import OBSIDIAN_VAULT_PATH

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""옵시디언 vault 문서 로더
Markdown 파일 로드 및 메타데이터 파싱
"""


# 사용자 site-packages 경로 추가

user_site_packages = site.getusersitepackages()
if user_site_packages:
    sys.path.insert(0, user_site_packages)

try:
    HAS_FRONTMATTER = True
except ImportError:
    HAS_FRONTMATTER = False
    print("⚠️  frontmatter 모듈이 설치되지 않았습니다. 기본 파싱 사용")
    print("   설치 권장: pip install --user python-frontmatter")

try:
    pass  # Placeholder
except ImportError:
    print("⚠️  langchain_core 모듈이 설치되지 않았습니다.")
    print("   설치: pip install --user langchain langchain-core")
    sys.exit(1)


class ObsidianLoader:
    """옵시디언 vault 문서 로더"""

    def __init__(self, vault_path: str | Path) -> None:
        """Args:
        vault_path: 옵시디언 vault 경로

        """
        self.vault_path = Path(vault_path)
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

    def load_documents(self, exclude_patterns: list[str] | None = None) -> list[Document]:
        """vault의 모든 Markdown 파일 로드

        Args:
            exclude_patterns: 제외할 파일 패턴 (예: [".obsidian", "templates"])

        Returns:
            Document 리스트

        """
        if exclude_patterns is None:
            exclude_patterns = [".obsidian", "templates", "dataview-queries"]

        documents = []

        for md_file in self.vault_path.rglob("*.md"):
            # 제외 패턴 확인
            if any(
                pattern in str(md_file.relative_to(self.vault_path)) for pattern in exclude_patterns
            ):
                continue

            try:
                doc = self._load_single_document(md_file)
                if doc:
                    documents.append(doc)
            except Exception as e:
                print(f"⚠️  파일 로드 실패: {md_file} - {e}")
                continue

        return documents

    def _load_single_document(self, file_path: Path) -> Document | None:
        """단일 문서 로드 및 메타데이터 추출"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Frontmatter 파싱
            if HAS_FRONTMATTER:
                post = frontmatter.loads(content)
                metadata = post.metadata.copy() if post.metadata else {}
                content = post.content
            else:
                # 기본 파싱 (frontmatter 없이)
                metadata = {}
                # 간단한 frontmatter 파싱 시도
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        # YAML 파싱 시도 (간단한 버전)
                        frontmatter_text = parts[1]
                        content = parts[2]
                        # 기본적인 키-값 추출
                        for line in frontmatter_text.split("\n"):
                            if ":" in line:
                                key, value = line.split(":", 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                metadata[key] = value

            # 파일 경로 정보 추가
            rel_path = file_path.relative_to(self.vault_path)
            metadata["source"] = str(rel_path)
            metadata["file_path"] = str(file_path)
            metadata["file_name"] = file_path.name

            # 옵시디언 링크 추출
            links = self._extract_links(content)
            metadata["links"] = links
            metadata["link_count"] = len(links)

            # 태그 추출
            tags = self._extract_tags(content, metadata)
            metadata["tags"] = tags

            # 카테고리 추출 (디렉토리 구조 기반)
            metadata["category"] = str(rel_path.parent) if rel_path.parent != Path() else "root"

            # 문서 타입 추출
            if "type" in metadata:
                metadata["doc_type"] = metadata["type"]
            elif "afo" in str(rel_path):
                metadata["doc_type"] = "afo"
            else:
                metadata["doc_type"] = "general"

            # 텍스트 전처리 (옵시디언 링크 정규화)
            content = self._normalize_obsidian_links(content)

            return Document(page_content=content, metadata=metadata)
        except Exception as e:
            print(f"⚠️  문서 파싱 실패: {file_path} - {e}")
            return None

    def _extract_links(self, content: str) -> list[str]:
        """옵시디언 링크 추출 [[링크]]"""
        link_pattern = r"\[\[([^\]]+)\]\]"
        links = re.findall(link_pattern, content)
        return list(set(links))  # 중복 제거

    def _extract_tags(self, content: str, metadata: dict) -> list[str]:
        """태그 추출 (#태그 또는 frontmatter tags)"""
        tags = set()

        # Frontmatter에서 태그 추출
        if "tags" in metadata:
            if isinstance(metadata["tags"], list):
                tags.update(metadata["tags"])
            elif isinstance(metadata["tags"], str):
                tags.add(metadata["tags"])

        # 본문에서 태그 추출 (#태그)
        tag_pattern = r"#([a-zA-Z0-9_-]+)"
        content_tags = re.findall(tag_pattern, content)
        tags.update(content_tags)

        return list(tags)

    def _normalize_obsidian_links(self, content: str) -> str:
        """옵시디언 링크를 일반 텍스트로 정규화"""
        # [[링크]] -> 링크
        content = re.sub(r"\[\[([^\]]+)\]\]", r"\1", content)
        # ![이미지|alt](path) -> alt 또는 path
        content = re.sub(r"!\[([^\]]*)\|?([^\]]*)\]\(([^\)]+)\)", r"\1 \3", content)
        return content

    def load_documents_by_category(self, category: str) -> list[Document]:
        """카테고리별 문서 로드"""
        all_docs = self.load_documents()
        return [doc for doc in all_docs if doc.metadata.get("category") == category]

    def load_documents_by_tag(self, tag: str) -> list[Document]:
        """태그별 문서 로드"""
        all_docs = self.load_documents()
        return [doc for doc in all_docs if tag in doc.metadata.get("tags", [])]


def main() -> None:
    """테스트"""

    vault_path = OBSIDIAN_VAULT_PATH
    loader = ObsidianLoader(vault_path)

    print("📚 옵시디언 vault 문서 로드 중...")
    documents = loader.load_documents()

    print(f"\n✅ 총 {len(documents)}개 문서 로드 완료")
    print("\n📊 카테고리별 문서 수:")
    categories = {}
    for doc in documents:
        cat = doc.metadata.get("category", "root")
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count}개")

    print("\n📝 샘플 문서:")
    if documents:
        sample = documents[0]
        print(f"  파일: {sample.metadata.get('source')}")
        print(f"  태그: {sample.metadata.get('tags', [])}")
        print(f"  링크: {sample.metadata.get('links', [])[:5]}")
        print(f"  내용 미리보기: {sample.page_content[:200]}...")


if __name__ == "__main__":
    main()
