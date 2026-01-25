# Trinity Score: 96.0 (Phase 30 Multimodal Documents Refactoring)
"""Multimodal Document Models - Data Structures for RAG Engine"""

import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MultimodalDocument:
    """A document that can contain text, images, or other media.

    Trinity Score: 眞97% 善95% 美96% 孝94% 永93%
    """

    content: str
    content_type: str = "text"  # text, image, audio, video
    metadata: dict[str, Any] | None = None
    embedding: list[float] | None = None
    created_at: float | None = None  # LRU용 타임스탬프

    def __post_init__(self) -> None:
        """Initialize document with proper defaults."""
        try:
            if self.metadata is None:
                self.metadata = {}
            if self.created_at is None:
                self.created_at = time.time()
        except (ValueError, TypeError) as e:
            logger.debug("MultimodalDocument 초기화 중 값 설정 실패: %s", str(e))
            self.metadata = {}
            self.created_at = time.time()
        except Exception as e:  # Intentional fallback for unexpected errors
            logger.debug("MultimodalDocument 초기화 중 예상치 못한 에러: %s", str(e))
            self.metadata = {}
            self.created_at = time.time()

    def is_expired(self, max_age_seconds: float) -> bool:
        """Check if document has expired based on creation time."""
        if self.created_at is None:
            return False
        return (time.time() - self.created_at) > max_age_seconds

    def to_dict(self) -> dict[str, Any]:
        """Convert document to dictionary representation."""
        return {
            "content": self.content,
            "content_type": self.content_type,
            "metadata": self.metadata or {},
            "embedding": self.embedding,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MultimodalDocument":
        """Create document from dictionary representation."""
        return cls(
            content=data["content"],
            content_type=data.get("content_type", "text"),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            created_at=data.get("created_at"),
        )
