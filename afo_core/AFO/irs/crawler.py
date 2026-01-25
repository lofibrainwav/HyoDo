"""
IRS Document Crawler

웹 크롤링 및 문서 추출 로직
"""

import hashlib
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from .models import IRSConfig

logger = logging.getLogger(__name__)


class IRSCrawler:
    """IRS 문서 크롤러"""

    def __init__(self, config: IRSConfig | None = None) -> None:
        self.config = config or IRSConfig()

    async def initialize_session(self) -> aiohttp.ClientSession:
        """HTTP 세션 초기화"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        return aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.config.session_timeout),
        )

    async def extract_documents_from_page(
        self,
        session: aiohttp.ClientSession,
        soup: BeautifulSoup,
        base_url: str,
        source_name: str,
    ) -> list[dict[str, Any]]:
        """페이지에서 문서 링크 추출 및 메타데이터 수집"""
        documents = []

        link_patterns = {
            "publications": [r"/publications/p\\d+", r"/instructions\\d+", r"/forms/\\d+"],
            "revenue_procedures": [r"/documents/\\d+/\\d+/\\d+/\\d+", r"/federal-register/\\d+"],
            "notices": [r"/irs-notice-\\d+", r"/newsroom/notice-\\d+"],
            "court_rulings": [r"/opinion-\\d+", r"/tc-memo-\\d+"],
            "tax_legislation": [r"/bill/\\d+th-congress", r"/public-law/\\d+-\\d+"],
        }

        patterns = link_patterns.get(source_name, [])

        for pattern in patterns:
            links = soup.find_all("a", href=re.compile(pattern, re.IGNORECASE))

            for link in links:
                href = link.get("href")
                if not href:
                    continue

                full_url = urljoin(base_url, href)

                if self._should_exclude_url(full_url):
                    continue

                try:
                    doc_metadata = await self._extract_document_metadata(
                        session, full_url, source_name
                    )
                    if doc_metadata:
                        documents.append(doc_metadata)
                except Exception as e:
                    logger.warning(f"Failed to extract metadata from {full_url}: {e}")

        return documents

    async def _extract_document_metadata(
        self,
        session: aiohttp.ClientSession,
        url: str,
        source_name: str,
    ) -> dict[str, Any] | None:
        """문서 URL에서 메타데이터 추출"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                title = self._extract_title(soup, url)
                preview = self._extract_preview(soup)
                doc_type = self._classify_document_type(title, preview, url)

                if not doc_type:
                    return None

                doc_id = hashlib.sha256(url.encode()).hexdigest()

                return {
                    "id": doc_id,
                    "url": url,
                    "title": title,
                    "preview": preview,
                    "source": source_name,
                    "document_type": doc_type["type"],
                    "category": doc_type["category"],
                    "subcategory": doc_type["subcategory"],
                    "collected_at": datetime.now().isoformat(),
                    "content_hash": hashlib.sha256(html.encode()).hexdigest(),
                }

        except Exception as e:
            logger.warning(f"Metadata extraction failed for {url}: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """페이지에서 제목 추출"""
        title_selectors = ["h1", "title", ".document-title", ".page-title"]

        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title:
                    return title

        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        if path_parts:
            last_part = path_parts[-1]
            title = re.sub(r"[-\\d_]", " ", last_part).strip()
            if title:
                return title.title()

        return f"IRS Document from {parsed.netloc}"

    def _extract_preview(self, soup: BeautifulSoup) -> str:
        """페이지에서 내용 미리보기 추출"""
        content_selectors = ["main", ".content", ".document-content", "article"]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                text = content_elem.get_text(strip=True)
                preview = text[:500] + "..." if len(text) > 500 else text
                if preview.strip():
                    return preview

        text = soup.get_text(strip=True)
        return text[:300] + "..." if len(text) > 300 else text

    def _classify_document_type(self, title: str, preview: str, url: str) -> dict[str, str] | None:
        """문서 타입 분류"""
        text_to_check = f"{title} {preview} {url}".lower()

        for doc_type, config in self.config.document_types.items():
            pattern = config["pattern"]
            if re.search(pattern, text_to_check, re.IGNORECASE):
                return {
                    "type": doc_type,
                    "category": config["category"],
                    "subcategory": config["subcategory"],
                }

        return None

    def _should_exclude_url(self, url: str) -> bool:
        """URL 제외 여부 확인"""
        url_lower = url.lower()

        for pattern in self.config.exclude_patterns:
            if re.search(pattern, url_lower):
                return True

        exclude_extensions = [".jpg", ".jpeg", ".png", ".gif", ".css", ".js", ".ico"]
        return any(url_lower.endswith(ext) for ext in exclude_extensions)

    async def find_additional_pages(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """추가 페이지 URL 찾기 (페이지네이션)"""
        additional_pages = []
        pagination_selectors = [".pagination a", ".pager a", '[rel="next"]']

        for selector in pagination_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get("href")
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in additional_pages:
                        additional_pages.append(full_url)

        return additional_pages[: self.config.max_pages_per_source]

    @staticmethod
    def deduplicate_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """중복 문서 제거"""
        seen_urls: set[str] = set()
        unique_docs = []

        for doc in documents:
            url = doc.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_docs.append(doc)

        return unique_docs
