"""
Live IRS Crawler - 실제 IRS 웹사이트 크롤러

眞 (장영실 - Jang Yeong-sil): 기술적 확실성/타입 안전성
- 실제 IRS 웹사이트 연동
- requests + BeautifulSoup 기반 크롤링
- 캐싱 및 재시도 메커니즘
- 에러 처리 및 로깅
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

from .hash_utils import HashUtils
from .irs_config import IRSConfig

logger = logging.getLogger(__name__)


class CrawlStatus(Enum):
    """크롤링 상태"""

    SUCCESS = "success"  # 성공
    FAILED = "failed"  # 실패
    RATE_LIMITED = "rate_limited"  # 속도 제한
    NOT_MODIFIED = "not_modified"  # 변경 없음


@dataclass
class CrawlResult:
    """크롤링 결과"""

    status: CrawlStatus
    document_id: str
    document_type: str
    content: str
    hash: str
    crawled_at: str
    url: str
    error_message: str | None = None
    response_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "status": self.status.value,
            "document_id": self.document_id,
            "document_type": self.document_type,
            "hash": self.hash,
            "crawled_at": self.crawled_at,
            "url": self.url,
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms,
        }


class IRSLiveCrawler:
    """
    실제 IRS 웹사이트 크롤러

    주요 IRS 문서 24/7 모니터링:
    - Publication 17
    - Publication 463 (Travel, Gift, and Car Expenses)
    - Publication 505 (Tax Withholding)
    - Rev. Proc. 2024-40
    - FTB 문서 등
    """

    # IRS 주요 문서 URL
    IRS_DOCUMENTS = {
        "pub17": {
            "url": "https://www.irs.gov/pub/irs-pdf/p17.pdf",
            "type": "IRS Publication 17",
            "priority": "critical",
        },
        "pub463": {
            "url": "https://www.irs.gov/pub/irs-pdf/p463.pdf",
            "type": "IRS Publication 463",
            "priority": "high",
        },
        "pub505": {
            "url": "https://www.irs.gov/pub/irs-pdf/p505.pdf",
            "type": "IRS Publication 505",
            "priority": "medium",
        },
        "rev_proc_2024_40": {
            "url": "https://www.irs.gov/pub/irs-drop/rp-24-40.pdf",
            "type": "IRS Rev. Proc. 2024-40",
            "priority": "critical",
        },
    }

    # 캐싱 설정
    CACHE_DIR = Path("data/irs_monitor/cache")
    CACHE_EXPIRY_HOURS = 6  # 캐시 유효 기간 (시간)

    # 재시도 설정
    MAX_RETRIES = 3
    RETRY_BACKOFF = 2  # 지연 시간 (초)
    TIMEOUT = 30  # 요청 타임아웃 (초)
    RATE_LIMIT_DELAY = 5  # 속도 제한 지연 (초)

    def __init__(self, config: IRSConfig | None = None) -> None:
        self.config = config or IRSConfig()
        self.hash_utils = HashUtils()
        self.cache_dir = self.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 세션 설정 (재시도 메커니즘)
        self.session = self._create_session()

        # 마지막 크롤링 시간 추적
        self.last_crawl_times: dict[str, datetime] = {}

    def _create_session(self) -> requests.Session:
        """
        세션 생성 (재시도 메커니즘 포함)

        Returns:
            requests.Session
        """
        session = requests.Session()

        # 재시도 전략 설정
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # User-Agent 설정
        session.headers.update(
            {
                "User-Agent": "AFO-Kingdom-IRS-Monitor/1.0 (Tax Law Monitoring System)",
            }
        )

        return session

    def _get_cache_path(self, document_id: str) -> Path:
        """
        캐시 경로 조회

        Args:
            document_id: 문서 ID

        Returns:
            캐시 파일 경로
        """
        return self.cache_dir / f"{document_id}.cache"

    def _load_from_cache(self, document_id: str) -> CrawlResult | None:
        """
        캐시에서 로드

        Args:
            document_id: 문서 ID

        Returns:
            캐시된 결과
        """
        cache_path = self._get_cache_path(document_id)

        if not cache_path.exists():
            return None

        try:
            import json

            with open(cache_path, encoding="utf-8") as f:
                cache_data = json.load(f)

            # 캐시 유효기간 확인
            crawled_at = datetime.fromisoformat(cache_data["crawled_at"])
            cache_age = datetime.now() - crawled_at

            if cache_age.total_seconds() > self.CACHE_EXPIRY_HOURS * 3600:
                logger.info(f"캐시 만료: {document_id} (캐시 나이: {cache_age})")
                return None

            logger.info(f"캐시 사용: {document_id} (캐시 나이: {cache_age})")

            return CrawlResult(
                status=CrawlStatus.SUCCESS,
                document_id=cache_data["document_id"],
                document_type=cache_data["document_type"],
                content="",  # 캐시에는 내용을 저장하지 않음 (공간 절약)
                hash=cache_data["hash"],
                crawled_at=cache_data["crawled_at"],
                url=cache_data["url"],
                error_message=None,
                response_time_ms=0.0,
            )

        except Exception as e:
            logger.error(f"캐시 로드 실패: {document_id}, {e}")
            return None

    def _save_to_cache(self, result: CrawlResult) -> None:
        """
        캐시에 저장

        Args:
            result: 크롤링 결과
        """
        cache_path = self._get_cache_path(result.document_id)

        try:
            import json

            cache_data = result.to_dict()
            # 캐시에는 내용을 저장하지 않음
            cache_data["content"] = ""

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.info(f"캐시 저장: {result.document_id}")

        except Exception as e:
            logger.error(f"캐시 저장 실패: {result.document_id}, {e}")

    def crawl_document(
        self,
        document_id: str,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> CrawlResult:
        """
        문서 크롤링

        Args:
            document_id: 문서 ID (pub17, pub463, etc.)
            use_cache: 캐시 사용 여부
            force_refresh: 캐시 무시 강제 갱신

        Returns:
            크롤링 결과
        """
        # 문서 정보 확인
        if document_id not in self.IRS_DOCUMENTS:
            return CrawlResult(
                status=CrawlStatus.FAILED,
                document_id=document_id,
                document_type="Unknown",
                content="",
                hash="",
                crawled_at=datetime.now().isoformat(),
                url="",
                error_message=f"문서 ID 없음: {document_id}",
            )

        doc_info = self.IRS_DOCUMENTS[document_id]
        url = doc_info["url"]
        doc_type = doc_info["type"]

        # 캐시 확인
        if use_cache and not force_refresh:
            cached_result = self._load_from_cache(document_id)
            if cached_result:
                return cached_result

        # 속도 제한 확인
        if document_id in self.last_crawl_times:
            last_crawl = self.last_crawl_times[document_id]
            time_since_last_crawl = (datetime.now() - last_crawl).total_seconds()

            if time_since_last_crawl < self.RATE_LIMIT_DELAY:
                logger.warning(
                    f"속도 제한: {document_id} ({time_since_last_crawl:.1f}s < {self.RATE_LIMIT_DELAY}s)"
                )
                return CrawlResult(
                    status=CrawlStatus.RATE_LIMITED,
                    document_id=document_id,
                    document_type=doc_type,
                    content="",
                    hash="",
                    crawled_at=datetime.now().isoformat(),
                    url=url,
                    error_message=f"속도 제한: {self.RATE_LIMIT_DELAY}s 이후 다시 시도",
                )

        # 크롤링 시작
        start_time = time.time()

        try:
            logger.info(f"크롤링 시작: {document_id} ({url})")

            # 요청 전송
            response = self.session.get(
                url,
                timeout=self.TIMEOUT,
                stream=True,  # 대용량 파일 스트리밍
            )

            response.raise_for_status()

            # 콘텐츠 수집
            content = response.content
            content_str = content.decode("utf-8", errors="ignore")

            # 해시 계산
            content_hash = hashlib.sha256(content).hexdigest()[:32]

            # 응답 시간 계산
            response_time = (time.time() - start_time) * 1000  # ms

            # 마지막 크롤링 시간 업데이트
            self.last_crawl_times[document_id] = datetime.now()

            # 결과 생성
            result = CrawlResult(
                status=CrawlStatus.SUCCESS,
                document_id=document_id,
                document_type=doc_type,
                content=content_str,
                hash=content_hash,
                crawled_at=datetime.now().isoformat(),
                url=url,
                error_message=None,
                response_time_ms=response_time,
            )

            logger.info(
                f"크롤링 성공: {document_id} "
                f"(해시: {content_hash}, 응답 시간: {response_time:.0f}ms)"
            )

            # 캐시 저장
            self._save_to_cache(result)

            return result

        except RequestException as e:
            response_time = (time.time() - start_time) * 1000

            logger.error(f"크롤링 실패: {document_id}, {e}")

            return CrawlResult(
                status=CrawlStatus.FAILED,
                document_id=document_id,
                document_type=doc_type,
                content="",
                hash="",
                crawled_at=datetime.now().isoformat(),
                url=url,
                error_message=str(e),
                response_time_ms=response_time,
            )

    def crawl_all(
        self,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> dict[str, CrawlResult]:
        """
        모든 문서 크롤링

        Args:
            use_cache: 캐시 사용 여부
            force_refresh: 캐시 무시 강제 갱신

        Returns:
            문서별 크롤링 결과
        """
        results = {}

        for document_id in self.IRS_DOCUMENTS.keys():
            result = self.crawl_document(
                document_id,
                use_cache=use_cache,
                force_refresh=force_refresh,
            )
            results[document_id] = result

            # Critical 문서 후 순서로 지연
            doc_priority = self.IRS_DOCUMENTS[document_id]["priority"]
            if doc_priority != "critical":
                time.sleep(2)  # Critical 외 문서는 2초 지연

        return results

    def crawl_by_priority(
        self,
        priority: str,
        use_cache: bool = True,
    ) -> dict[str, CrawlResult]:
        """
        우선순위별 크롤링

        Args:
            priority: 우선순위 (critical, high, medium)
            use_cache: 캐시 사용 여부

        Returns:
            문서별 크롤링 결과
        """
        results = {}

        for document_id, doc_info in self.IRS_DOCUMENTS.items():
            if doc_info["priority"] == priority:
                result = self.crawl_document(
                    document_id,
                    use_cache=use_cache,
                )
                results[document_id] = result

        return results

    def clear_cache(self) -> int:
        """
        캐시 정리

        Returns:
            삭제된 캐시 파일 수
        """
        deleted_count = 0

        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
                deleted_count += 1
                logger.info(f"캐시 삭제: {cache_file}")
            except Exception as e:
                logger.error(f"캐시 삭제 실패: {cache_file}, {e}")

        return deleted_count

    def get_cache_stats(self) -> dict[str, Any]:
        """
        캐시 통계 조회

        Returns:
            캐시 통계
        """
        cache_files = list(self.cache_dir.glob("*.cache"))

        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "cache_count": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
        }

    def close(self) -> None:
        """세션 종료"""
        self.session.close()
        logger.info("세션 종료")

    def __enter__(self) -> IRSLiveCrawler:
        """Context Manager 진입"""
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        """Context Manager 종료"""
        self.close()
