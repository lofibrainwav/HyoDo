"""E2E Simulation Utilities.

테스트 경로 설정, 샘플 문서 생성 및 결과 로깅 유틸리티.
"""

from __future__ import annotations

import hashlib
import json
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_simulation_paths() -> dict[str, Path]:
    """테스트용 가상 경로 환경을 설정합니다."""
    base_path = Path(tempfile.gettempdir()) / "afo_e2e_test"
    paths = {
        "base": base_path,
        "irs_docs": base_path / "irs_docs",
        "ssot": base_path / "ssot",
        "logs": base_path / "logs",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def create_sample_irs_document(version: str, changes: dict[str, str] | None = None) -> str:
    """테스트용 모의 IRS 문서를 생성합니다."""
    return f"IRS Regulation Version {version}\nChanges: {json.dumps(changes or {})}"


def calculate_content_hash(content: str) -> str:
    """내용의 SHA-256 해시를 계산합니다."""
    return hashlib.sha256(content.encode()).hexdigest()


def log_test_result(test_name: str, status: str, message: str) -> None:
    """테스트 결과를 표준화된 형식으로 로깅합니다."""
    emoji = "✅" if status == "passed" else "❌"
    logger.info(f"{emoji} [{test_name}] {status.upper()}: {message}")
