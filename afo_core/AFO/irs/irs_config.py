"""
IRS Monitor Configuration - IRS 문서 모니터링 설정

眞 (장영실 - Jang Yeong-sil): 아키텍처 설계
- IRS URL 설정
- 모니터링 주기 설정
- 해시 알고리즘 설정
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class IRSURLConfig:
    """IRS URL 설정"""

    critical_documents: dict[str, str] = field(
        default_factory=lambda: {
            "publication_17": "https://www.irs.gov/pub/irs-pdf/p17.pdf",
            "rev_proc_2024_40": "https://www.irs.gov/pub/irs-drop/revproc/2024-40.pdf",
            "ftb_guidelines": "https://www.ftb.ca.gov/forms/2024/2024-1001.pdf",
            "energy_credit": "https://www.irs.gov/pub/irs-pdf/p5963.pdf",
            "ev_credit": "https://www.irs.gov/pub/irs-pdf/p8834.pdf",
            "bonus_depreciation": "https://www.irs.gov/pub/irs-pdf/p946.pdf",
        }
    )

    regular_documents: dict[str, str] = field(
        default_factory=lambda: {
            "notices": "https://www.irs.gov/newsroom/notices",
            "revenue_procedures": "https://www.irs.gov/businesses/corporations/revenue-procedures",
            "tax_legislation": "https://www.congress.gov/browse?collectionCode=PLAW&year=2025",
            "court_rulings": "https://www.ustaxcourt.gov/UstaxCourtInformat",
            "ftb_notices": "https://www.ftb.ca.gov/forms-search/notices",
        }
    )

    fallback_urls: dict[str, str] = field(
        default_factory=lambda: {
            "publication_17": "https://www.treasury.gov/resource-center/tax-policy/pages/tax-providers",
            "rev_proc_2024_40": "https://www.federalregister.gov/agencies/internal-revenue-service",
        }
    )


@dataclass
class IRSMonitoringConfig:
    """IRS 모니터링 설정"""

    url_config: IRSURLConfig = field(default_factory=IRSURLConfig)

    critical_interval_hours: int = 6
    regular_interval_hours: int = 24
    max_concurrent_checks: int = 5

    hash_algorithm: str = "sha256"
    hash_encoding: str = "utf-8"

    timeout_seconds: int = 30
    download_timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: int = 5

    storage_path: Path = Path("data/irs_monitor")
    hash_cache_path: Path = Path("data/irs_monitor/hashes.json")
    change_log_path: Path = Path("data/irs_monitor/changes.json")

    history_retention_days: int = 365
    max_change_history: int = 1000

    notify_on_change: bool = True
    notify_on_critical: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "url_config": {
                "critical_documents": self.url_config.critical_documents,
                "regular_documents": self.url_config.regular_documents,
                "fallback_urls": self.url_config.fallback_urls,
            },
            "critical_interval_hours": self.critical_interval_hours,
            "regular_interval_hours": self.regular_interval_hours,
            "max_concurrent_checks": self.max_concurrent_checks,
            "hash_algorithm": self.hash_algorithm,
            "hash_encoding": self.hash_encoding,
            "timeout_seconds": self.timeout_seconds,
            "download_timeout_seconds": self.download_timeout_seconds,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "storage_path": str(self.storage_path),
            "hash_cache_path": str(self.hash_cache_path),
            "change_log_path": str(self.change_log_path),
            "history_retention_days": self.history_retention_days,
            "max_change_history": self.max_change_history,
            "notify_on_change": self.notify_on_change,
            "notify_on_critical": self.notify_on_critical,
        }


class IRSConfigManager:
    """IRS 설정 관리자"""

    @staticmethod
    def get_default_config() -> IRSMonitoringConfig:
        """기본 설정 반환"""
        return IRSMonitoringConfig()

    @staticmethod
    def load_config(config_path: Path) -> IRSMonitoringConfig:
        """설정 파일에서 로드"""
        import json

        if not config_path.exists():
            return IRSConfigManager.get_default_config()

        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        return IRSMonitoringConfig(**data)

    @staticmethod
    def save_config(config: IRSMonitoringConfig, config_path: Path) -> None:
        """설정 파일에 저장"""
        import json

        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)


# Alias for backward compatibility
IRSConfig = IRSMonitoringConfig

__all__ = [
    "IRSConfig",
    "IRSURLConfig",
    "IRSMonitoringConfig",
    "IRSConfigManager",
]
