"""
IRS Source Registry Models

데이터 모델 및 설정
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IRSConfig:
    """IRS 크롤러 설정"""

    base_urls: dict[str, str] = field(
        default_factory=lambda: {
            "publications": "https://www.irs.gov/publications",
            "revenue_procedures": "https://www.federalregister.gov/agencies/internal-revenue-service",
            "notices": "https://www.irs.gov/newsroom/notices",
            "court_rulings": "https://www.ustaxcourt.gov",
            "tax_legislation": "https://www.congress.gov/browse?collectionCode=PLAW&year=2025",
        }
    )

    document_types: dict[str, dict[str, str]] = field(
        default_factory=lambda: {
            "publication": {
                "pattern": r"irs.*pub.*\d+",
                "category": "irs_tax",
                "subcategory": "publications",
            },
            "revenue_procedure": {
                "pattern": r"rev.*proc.*\d+",
                "category": "irs_tax",
                "subcategory": "revenue_procedures",
            },
            "notice": {
                "pattern": r"notice.*\d+",
                "category": "irs_tax",
                "subcategory": "notices",
            },
            "court_ruling": {
                "pattern": r"t\\.c\\.memo.*\\d+",
                "category": "irs_tax",
                "subcategory": "court_rulings",
            },
        }
    )

    crawl_delay: float = 1.0
    max_pages_per_source: int = 5
    session_timeout: int = 30

    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            r"privacy.*policy",
            r"terms.*service",
            r"contact.*us",
            r"about.*irs",
        ]
    )


@dataclass
class CollectionStats:
    """수집 통계"""

    last_collection: str | None = None
    total_documents: int = 0
    documents_by_type: dict[str, int] = field(default_factory=dict)
    collection_duration: float | None = None
    errors: list[str] = field(default_factory=list)
    success: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_collection": self.last_collection,
            "total_documents": self.total_documents,
            "documents_by_type": self.documents_by_type,
            "collection_duration": self.collection_duration,
            "errors": self.errors,
            "success": self.success,
        }
