"""
IRS Source Registry

메인 레지스트리 클래스
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from .crawler import IRSCrawler
from .integrations import IRSIntegrations
from .models import CollectionStats, IRSConfig

logger = logging.getLogger(__name__)


class IRSSourceRegistry:
    """IRS Source Registry - 자동 IRS 문서 수집 시스템"""

    def __init__(self, config: IRSConfig | None = None) -> None:
        self.config = config or IRSConfig()
        self.crawler = IRSCrawler(self.config)
        self.stats = CollectionStats()

        # Multimodal RAG 초기화 (지연 로딩)
        self._multimodal_rag = None
        self._integrations: IRSIntegrations | None = None

    @property
    def integrations(self) -> IRSIntegrations:
        """통합 모듈 (지연 로딩)"""
        if self._integrations is None:
            try:
                from multimodal_rag import MultimodalRAGEngine

                self._multimodal_rag = MultimodalRAGEngine()
            except ImportError:
                self._multimodal_rag = None
            self._integrations = IRSIntegrations(self._multimodal_rag)
        return self._integrations

    async def collect_all_sources(self) -> dict[str, Any]:
        """모든 IRS 소스에서 문서 수집"""
        start_time = datetime.now()
        session = await self.crawler.initialize_session()

        try:
            all_documents: list[dict[str, Any]] = []

            for source_name, base_url in self.config.base_urls.items():
                logger.info(f"Collecting from {source_name}: {base_url}")

                try:
                    documents = await self._collect_from_source(session, source_name, base_url)
                    all_documents.extend(documents)
                    logger.info(f"Collected {len(documents)} documents from {source_name}")
                    await asyncio.sleep(self.config.crawl_delay)

                except Exception as e:
                    error_msg = f"Failed to collect from {source_name}: {e!s}"
                    logger.error(error_msg)
                    self.stats.errors.append(error_msg)

            unique_documents = self.crawler.deduplicate_documents(all_documents)

            await self.integrations.add_to_multimodal_rag(unique_documents)
            await self.integrations.register_to_context7(unique_documents)

            end_time = datetime.now()
            self.stats.last_collection = end_time.isoformat()
            self.stats.total_documents = len(unique_documents)
            self.stats.documents_by_type = self._count_by_type(unique_documents)
            self.stats.collection_duration = (end_time - start_time).total_seconds()
            self.stats.success = True

            return {
                "success": True,
                "total_collected": len(unique_documents),
                "documents": unique_documents,
                "stats": self.stats.to_dict(),
            }

        except Exception as e:
            self.stats.errors.append(f"Collection failed: {e!s}")
            return {"success": False, "error": str(e), "stats": self.stats.to_dict()}

        finally:
            await session.close()

    async def _collect_from_source(
        self,
        session: Any,
        source_name: str,
        base_url: str,
    ) -> list[dict[str, Any]]:
        """특정 소스에서 문서 수집"""
        from bs4 import BeautifulSoup

        documents: list[dict[str, Any]] = []

        async with session.get(base_url) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            page_documents = await self.crawler.extract_documents_from_page(
                session, soup, base_url, source_name
            )
            documents.extend(page_documents)

            if len(documents) < 50:
                additional_pages = await self.crawler.find_additional_pages(soup, base_url)

                for page_url in additional_pages:
                    try:
                        async with session.get(page_url) as page_response:
                            if page_response.status == 200:
                                page_html = await page_response.text()
                                page_soup = BeautifulSoup(page_html, "html.parser")
                                page_docs = await self.crawler.extract_documents_from_page(
                                    session, page_soup, page_url, source_name
                                )
                                documents.extend(page_docs)

                        await asyncio.sleep(self.config.crawl_delay)

                    except Exception as e:
                        logger.warning(f"Failed to crawl additional page {page_url}: {e}")

        return documents

    async def monitor_updates(self) -> None:
        """실시간 IRS 업데이트 모니터링"""
        logger.info("Starting IRS Update Monitor...")

        last_check = datetime.now()
        check_interval = timedelta(hours=6)

        while True:
            try:
                now = datetime.now()

                if now - last_check >= check_interval:
                    logger.info(f"Checking for IRS updates at {now.isoformat()}")

                    result = await self.collect_all_sources()

                    if result.get("success") and result.get("total_collected", 0) > 0:
                        logger.info(f"Found {result['total_collected']} new/updated documents")
                        await self.integrations.classify_with_tax_classifier(result["documents"])
                    else:
                        logger.info("No new documents found")

                    last_check = now

                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(300)

    @staticmethod
    def _count_by_type(documents: list[dict[str, Any]]) -> dict[str, int]:
        """문서 타입별 개수 계산"""
        counts: dict[str, int] = {}
        for doc in documents:
            doc_type = doc.get("document_type", "unknown")
            counts[doc_type] = counts.get(doc_type, 0) + 1
        return counts

    def get_collection_stats(self) -> dict[str, Any]:
        """수집 통계 반환"""
        return {
            **self.stats.to_dict(),
            "source_urls": list(self.config.base_urls.keys()),
        }
