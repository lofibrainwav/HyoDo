import hashlib
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class IRSCrawler:
    """IRS 웹사이트 크롤러 및 변경 감지"""

    def __init__(self, monitoring_urls: dict[str, str]) -> None:
        self.monitoring_urls = monitoring_urls
        self.content_hashes: dict[str, str] = {}
        self.last_check_times: dict[str, datetime] = {}
        self.session_timeout = 30

    async def collect_baseline_hashes(self, session: aiohttp.ClientSession) -> None:
        """초기 베이스라인 해시 수집"""
        logger.info("Collecting baseline content hashes...")

        for source_name, url in self.monitoring_urls.items():
            try:
                content_hash = await self._get_page_hash(session, url)
                if content_hash:
                    self.content_hashes[url] = content_hash
                    self.last_check_times[url] = datetime.now()
                    logger.debug(f"Baseline collected for {source_name}: {content_hash[:8]}...")
            except Exception as e:
                logger.warning(f"Failed to collect baseline for {source_name}: {e}")

        logger.info(f"Collected baseline hashes for {len(self.content_hashes)} sources")

    async def detect_changes(
        self, session: aiohttp.ClientSession, url: str
    ) -> tuple[bool, dict[str, Any]]:
        """특정 URL에서 변경 감지"""
        try:
            current_hash = await self._get_page_hash(session, url)

            if not current_hash:
                return False, {}

            previous_hash = self.content_hashes.get(url)

            if previous_hash and previous_hash != current_hash:
                # 변경 감지됨 - 상세 정보 수집
                change_details = await self._get_change_details(session, url)
                # 해시 업데이트 (감지 후 바로 업데이트하여 중복 방지?) -> Service에서 호출 시점에 따라 결정?
                # 여기서는 감지되었음만 리턴하고 해시 업데이트는 호출자가 판단?
                # 아니면 여기서 업데이트? 보통은 여기서 업데이트함.
                # 하지만 Service에서 Event 생성 실패하면 다시 감지해야 할 수도 있음.
                # 그러나 hash가 바뀌었으면 이미 바뀐 상태.
                # 여기서는 업데이트하지 않고 Service가 성공적으로 처리하면 업데이트하도록 하는게 안전하지만,
                # 코드가 복잡해지므로 기존 로직처럼 여기서 업데이트하거나 호출자가 함.
                # 기존 로직: detect_changes가 불리면 내부 해시 업데이트 로직이 있음.

                # 하지만 분리된 구조에서는 상태 변경을 명시적으로 하는 게 좋음.
                # 여기서는 상태 변경 없이 결과만 리턴하고, update_hash 메서드를 따로 두거나,
                # 이 메서드가 hash를 업데이트한다고 명시.

                # 기존 로직을 그대로 가져오려면:
                # self.content_hashes[url] = current_hash # 기존에는 변경 없을 때만 업데이트했음?
                # 기존 코드 289 라인: 변경 감지 시 리턴하고, 변경 없을 때만 업데이트.
                # 즉 변경 감지 시에는 해시 업데이트를 안 하고 리턴 -> 다음 주기에 또 감지됨 -> 계속 감지됨?
                # 아, 아마도 변경 처리가 성공하면 해시를 업데이트해야 하는데 기존 코드는 변경 감지 시 해시 업데이트를 건너뛰고 있음.
                # 284 라인: if diff: return True
                # 290 라인: hash update (if diff is false)
                # 이렇게 되면 변경이 발생하면 다음번에도 계속 변경으로 감지될 텐데?
                # 아, _process_detected_changes 호출 후 loop가 다시 돌 때...
                # 기존 코드 버그일 수도 있고 의도일 수도 있음.
                # 일단 기존 로직을 개선하여: 변경 감지 시 상세정보 리턴. 해시 업데이트 메서드 제공.
                pass
            else:
                self.content_hashes[url] = current_hash
                return False, {}

            # 변경 감지됨
            change_details = await self._get_change_details(session, url)

            # 해시 업데이트 (중복 감지 방지를 위해 여기서 업데이트)
            self.content_hashes[url] = current_hash
            self.last_check_times[url] = datetime.now()

            return True, change_details

        except Exception as e:
            logger.warning(f"Error detecting changes for {url}: {e}")
            return False, {}

    async def _get_page_hash(self, session: aiohttp.ClientSession, url: str) -> str | None:
        """페이지 콘텐츠의 해시 계산"""
        try:
            async with session.get(url, timeout=self.session_timeout) as response:
                if response.status != 200:
                    return None

                content = await response.text()
                soup = BeautifulSoup(content, "html.parser")
                main_content = self._extract_main_content(soup)

                if main_content:
                    normalized_content = re.sub(r"\s+", " ", main_content.strip())
                    return hashlib.sha256(normalized_content.encode()).hexdigest()

        except Exception as e:
            logger.debug(f"Error getting page hash for {url}: {e}")

        return None

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """페이지에서 주요 콘텐츠 추출"""
        content_selectors = [
            "main",
            ".content",
            ".main-content",
            "article",
            ".entry-content",
            ".post-content",
            "#content",
            ".irs-content",
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                return content_elem.get_text(separator=" ", strip=True)

        return soup.get_text(separator=" ", strip=True)

    async def _get_change_details(self, session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
        """변경 상세 정보 수집"""
        try:
            async with session.get(url, timeout=self.session_timeout) as response:
                if response.status != 200:
                    return {}

                content = await response.text()
                soup = BeautifulSoup(content, "html.parser")
                latest_items = self._extract_latest_items(soup, url)

                return {
                    "url": url,
                    "latest_items": latest_items,
                    "detected_at": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.warning(f"Error getting change details for {url}: {e}")
            return {}

    def _extract_latest_items(self, soup: BeautifulSoup, url: str) -> list[dict[str, str]]:
        """페이지에서 최신 항목들 추출"""
        latest_items = []

        if "publications" in url:
            items = soup.select(".publication-item, .pub-item, article")
            for item in items[:5]:
                title_elem = item.select_one("h3, h4, .title, a")
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link_elem = item.select_one("a")
                    item_url = (
                        urljoin(url, link_elem["href"])
                        if link_elem and link_elem.get("href")
                        else url
                    )
                    latest_items.append({"title": title, "url": item_url, "type": "publication"})

        elif "notices" in url:
            items = soup.select(".notice-item, .news-item, article")
            for item in items[:5]:
                title_elem = item.select_one("h3, h4, .title, a")
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link_elem = item.select_one("a")
                    item_url = (
                        urljoin(url, link_elem["href"])
                        if link_elem and link_elem.get("href")
                        else url
                    )
                    latest_items.append({"title": title, "url": item_url, "type": "notice"})
        else:
            content_blocks = soup.select("article, .post, .entry")
            for block in content_blocks[:3]:
                title = block.get_text(strip=True)[:100] + "..."
                latest_items.append({"title": title, "url": url, "type": "content_update"})

        return latest_items
