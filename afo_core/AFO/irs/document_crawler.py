"""IRS Document Crawler.

Downloads IRS documents with caching, retry logic, and rate limiting.
Follows IRS.gov robots.txt guidelines.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

# IRS domain and rate limiting
IRS_BASE_URL = "https://www.irs.gov"
IRS_ROBOTS_DELAY = 1.0  # seconds between requests
IRS_USER_AGENT = "AFO-Kingdom-IRS-Monitor/1.0 (Tax Document Monitoring)"


@dataclass
class DownloadResult:
    """Result of a document download."""

    success: bool
    url: str
    content: bytes | None
    content_hash: str
    etag: str | None
    last_modified: str | None
    content_type: str | None
    size_bytes: int
    error_message: str | None = None
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "url": self.url,
            "content_hash": self.content_hash,
            "etag": self.etag,
            "last_modified": self.last_modified,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }


class IRSDocumentCrawler:
    """Crawler for IRS documents with caching and retry logic."""

    def __init__(
        self,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = IRS_ROBOTS_DELAY,
    ) -> None:
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: float | None = None
        self._session: aiohttp.ClientSession | None = None

        logger.info("IRSDocumentCrawler initialized")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={
                    "User-Agent": IRS_USER_AGENT,
                    "Accept": "application/pdf, text/html, */*",
                },
            )
        return self._session

    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        import time

        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)

        self._last_request_time = time.time()

    def _calculate_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()

    async def download_document(
        self,
        url: str,
        expected_etag: str | None = None,
    ) -> DownloadResult:
        """Download a single document with rate limiting.

        Args:
            url: Document URL
            expected_etag: Optional ETag for conditional download

        Returns:
            Download result with content and metadata
        """
        await self._rate_limit()

        session = await self._get_session()
        headers: dict[str, str] = {}

        if expected_etag:
            headers["If-None-Match"] = expected_etag

        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 304:
                    # Not modified
                    logger.info(f"Document not modified: {url}")
                    return DownloadResult(
                        success=True,
                        url=url,
                        content=None,  # Not modified
                        content_hash="",
                        etag=expected_etag,
                        last_modified=response.headers.get("Last-Modified"),
                        content_type=response.headers.get("Content-Type"),
                        size_bytes=0,
                    )

                response.raise_for_status()

                content = await response.read()
                content_hash = self._calculate_hash(content)

                logger.info(f"Downloaded {len(content)} bytes from {url}")

                return DownloadResult(
                    success=True,
                    url=url,
                    content=content,
                    content_hash=content_hash,
                    etag=response.headers.get("ETag"),
                    last_modified=response.headers.get("Last-Modified"),
                    content_type=response.headers.get("Content-Type"),
                    size_bytes=len(content),
                )

        except aiohttp.ClientError as e:
            logger.error(f"Download failed for {url}: {e}")
            return DownloadResult(
                success=False,
                url=url,
                content=None,
                content_hash="",
                etag=None,
                last_modified=None,
                content_type=None,
                size_bytes=0,
                error_message=str(e),
            )

    async def download_with_retry(
        self,
        url: str,
        expected_etag: str | None = None,
    ) -> DownloadResult:
        """Download with exponential backoff retry.

        Args:
            url: Document URL
            expected_etag: Optional ETag for conditional download

        Returns:
            Download result
        """
        result: DownloadResult | None = None

        for attempt in range(self.max_retries):
            result = await self.download_document(url, expected_etag)

            if result.success or (result.error_message and "404" in result.error_message):
                # Success or permanent failure (404)
                result.retry_count = attempt
                return result

            # Retry with exponential backoff
            if attempt < self.max_retries - 1:
                delay = 2**attempt  # 1, 2, 4 seconds
                logger.warning(f"Retry {attempt + 1}/{self.max_retries} for {url} after {delay}s")
                await asyncio.sleep(delay)

        # Max retries exceeded
        if result is not None:
            result.retry_count = self.max_retries
            return result

        # This should never happen, but satisfies type checker
        return DownloadResult(
            success=False,
            url=url,
            content=None,
            content_hash="",
            etag=None,
            last_modified=None,
            content_type=None,
            size_bytes=0,
            error_message="Max retries exceeded",
            retry_count=self.max_retries,
        )

    async def download_multiple(
        self,
        urls: dict[str, str],
    ) -> dict[str, DownloadResult]:
        """Download multiple documents concurrently.

        Args:
            urls: Dictionary of document_id -> URL

        Returns:
            Dictionary of document_id -> DownloadResult
        """
        results: dict[str, DownloadResult] = {}

        # Download sequentially to respect rate limits
        for doc_id, url in urls.items():
            result = await self.download_with_retry(url)
            results[doc_id] = result

        return results

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("IRSDocumentCrawler session closed")

    async def __aenter__(self) -> IRSDocumentCrawler:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()


__all__ = [
    "DownloadResult",
    "IRSDocumentCrawler",
    "IRS_BASE_URL",
]
