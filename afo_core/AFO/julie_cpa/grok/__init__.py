"""Grok AI Engine Package.

x.AI의 Grok 모델을 활용한 재무 데이터 분석 시스템.
웹 인터페이스 및 공식 API를 통한 하이브리드 접근 제공.
"""

from __future__ import annotations

from .config import GrokConfig
from .engine import GrokEngine

__all__ = ["GrokEngine", "GrokConfig"]
