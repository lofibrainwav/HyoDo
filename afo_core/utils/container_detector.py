from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from AFO.config.settings import get_settings

# Trinity Score: 90.0 (Established by Chancellor)
# 🧭 Trinity Score: 眞95% 善90% 美85% 孝95% | Total: 91%
# 이 파일은 AFO 왕국의 眞善美孝 철학을 구현합니다

"""
Docker 컨테이너 자동 감지 유틸리티 모듈

眞 (Truth): 정확한 컨테이너 이름 감지
善 (Goodness): 재사용 가능한 코드로 유지보수성 향상
美 (Beauty): 깔끔한 인터페이스와 자동화
孝 (Serenity): 형님의 평온을 위한 투명한 동작
"""


class ContainerDetector:
    """Docker 컨테이너 이름 자동 감지 클래스"""

    def __init__(self, project_prefix: str = "afo") -> None:
        """
        Args:
            project_prefix: Docker 컨테이너 이름 접두사 (기본: "afo")
        """
        self.project_prefix = project_prefix
        self._cache: dict[str, Any] = {}  # 성능 향상을 위한 캐시

    def detect_redis_container(self) -> str:
        """Redis 컨테이너 이름 자동 감지"""
        if "redis" in self._cache:
            return str(self._cache["redis"])

        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=redis",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            # grep {self.project_prefix} | head -1 로직을 파이썬으로 구현
            names = [name for name in result.stdout.splitlines() if self.project_prefix in name]
            container_name = names[0].strip() if names else ""
            if container_name:
                self._cache["redis"] = str(container_name)
                return str(container_name)
        except Exception:
            pass

        # Fallback: 기본 이름
        default = f"{self.project_prefix}-redis-1"
        self._cache["redis"] = default
        return default

    def detect_postgres_container(self) -> str:
        """PostgreSQL 컨테이너 이름 자동 감지"""
        if "postgres" in self._cache:
            return str(self._cache["postgres"])

        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=postgres",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            # grep {self.project_prefix} | head -1 로직을 파이썬으로 구현
            names = [name for name in result.stdout.splitlines() if self.project_prefix in name]
            container_name = names[0].strip() if names else ""
            if container_name:
                self._cache["postgres"] = container_name
                return container_name
        except Exception:
            pass

        # Fallback: 기본 이름
        default = f"{self.project_prefix}-postgres-1"
        self._cache["postgres"] = default
        return default

    def detect_api_wallet_path(self) -> str:
        """API Wallet 파일 경로 자동 감지"""
        if "api_wallet_path" in self._cache:
            return str(self._cache["api_wallet_path"])

        # 여러 가능한 경로 시도
        # Phase 2-4: settings 사용
        try:
            settings = get_settings()
            afo_home = settings.AFO_HOME or ""
            afo_soul_engine_home = settings.AFO_SOUL_ENGINE_HOME or ""
        except Exception:
            afo_home = os.getenv("AFO_HOME", "")
            afo_soul_engine_home = os.getenv("AFO_SOUL_ENGINE_HOME", "")

        possible_paths = [
            (
                Path(afo_home) / "afo_soul_engine" / "api_wallet_storage.json"
                if afo_home
                else Path()
            ),
            (
                Path(afo_soul_engine_home) / "api_wallet_storage.json"
                if afo_soul_engine_home
                else Path()
            ),
            Path.home() / "AFO" / "afo_soul_engine" / "api_wallet_storage.json",
            Path("/Users/brnestrm/AFO/afo_soul_engine/api_wallet_storage.json"),
            Path("/home/user/AFO/afo_soul_engine/api_wallet_storage.json"),
            Path(__file__).parent.parent / "api_wallet_storage.json",  # 상대 경로
        ]

        for path in possible_paths:
            if path.exists():
                self._cache["api_wallet_path"] = str(path)
                return str(path)

        # 기본 경로 사용 (파일이 없을 수도 있음)
        default = str(Path(__file__).parent.parent / "api_wallet_storage.json")
        self._cache["api_wallet_path"] = default
        return default

    def get_all_containers(self) -> dict[str, str]:
        """모든 감지된 컨테이너 이름 반환"""
        return {
            "redis": self.detect_redis_container(),
            "postgres": self.detect_postgres_container(),
        }

    def clear_cache(self) -> None:
        """캐시 초기화 (테스트용)"""
        self._cache.clear()


# 싱글톤 인스턴스 (편의성)
_default_detector = ContainerDetector()


def get_redis_container() -> str:
    """Redis 컨테이너 이름 반환 (편의 함수)"""
    return _default_detector.detect_redis_container()


def get_postgres_container() -> str:
    """PostgreSQL 컨테이너 이름 반환 (편의 함수)"""
    return _default_detector.detect_postgres_container()


def get_api_wallet_path() -> str:
    """API Wallet 파일 경로 반환 (편의 함수)"""
    return _default_detector.detect_api_wallet_path()
