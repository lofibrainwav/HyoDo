"""
로깅 모듈 (SOLID: 단일 책임 원칙)

이 모듈은 검증 결과를 영구 저장하고 로깅하는 기능을 담당합니다.
- JSONL 형식 로그 저장
- 타임스탬프 및 메타데이터 추가
- 로그 파일 관리
"""

import json
import time
from pathlib import Path


class ValidationLogger:
    """
    검증 결과 로깅을 담당하는 클래스입니다.

    주요 기능:
    - JSONL 형식으로 결과 저장
    - 타임스탬프 및 메타데이터 자동 추가
    - 로그 파일 경로 관리
    """

    def __init__(self, log_dir: Path | None = None) -> None:
        """
        로거 초기화

        Args:
            log_dir: 로그 저장 디렉토리 (기본값: artifacts/code_validation_logs)
        """
        if log_dir is None:
            log_dir = Path("artifacts/code_validation_logs")
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_result(self, result: dict) -> Path:
        """
        검증 결과를 로그 파일에 저장합니다.

        Args:
            result: 검증 결과 딕셔너리

        Returns:
            Path: 저장된 로그 파일 경로
        """
        # 타임스탬프 및 메타데이터 추가
        enriched_result = self._enrich_result(result)

        # 파일명 생성 (타임스탬프 기반)
        timestamp = int(time.time())
        filename = f"validation_{timestamp}.jsonl"
        log_path = self.log_dir / filename

        # JSONL 형식으로 저장
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(enriched_result, ensure_ascii=False) + "\n")

        return log_path

    def _enrich_result(self, result: dict) -> dict:
        """
        결과에 메타데이터를 추가합니다.

        Args:
            result: 원본 결과

        Returns:
            dict: 메타데이터가 추가된 결과
        """
        enriched = result.copy()

        # 타임스탬프 추가 (없는 경우)
        if "as_of" not in enriched:
            enriched["as_of"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

        # 로그 메타데이터 추가
        enriched["_log_metadata"] = {
            "logged_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "logged_by": "TICKET-046_validation_system",
            "format_version": "1.0",
        }

        return enriched

    def get_recent_logs(self, limit: int = 10) -> list[Path]:
        """
        최근 로그 파일들을 반환합니다.

        Args:
            limit: 반환할 파일 개수

        Returns:
            list: 최근 로그 파일 경로 리스트
        """
        log_files = list(self.log_dir.glob("validation_*.jsonl"))
        # 타임스탬프 기준 정렬 (최신순)
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return log_files[:limit]

    def read_log(self, log_path: Path) -> dict:
        """
        로그 파일을 읽어옵니다.

        Args:
            log_path: 로그 파일 경로

        Returns:
            dict: 로그 내용

        Raises:
            FileNotFoundError: 파일이 없는 경우
            json.JSONDecodeError: JSON 파싱 실패 시
        """
        with open(log_path, encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            raise ValueError(f"Empty log file: {log_path}")

        return json.loads(content)


# 전역 로거 인스턴스
_default_logger = ValidationLogger()


def log_result(result: dict) -> Path:
    """
    검증 결과를 로그에 저장합니다 (편의 함수).

    Args:
        result: 검증 결과

    Returns:
        Path: 저장된 로그 파일 경로
    """
    return _default_logger.log_result(result)


def get_recent_logs(limit: int = 10) -> list[Path]:
    """
    최근 로그 파일들을 가져옵니다 (편의 함수).

    Args:
        limit: 가져올 파일 개수

    Returns:
        list: 로그 파일 경로 리스트
    """
    return _default_logger.get_recent_logs(limit)
