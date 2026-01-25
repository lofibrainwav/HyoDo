"""API Compatibility Models

데이터 제공자 모델들.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class HTMLSectionData:
    """HTML 섹션 데이터 모델"""

    title: str
    content: str
    icon: str | None = None
    metadata: dict[str, Any] | None = None
