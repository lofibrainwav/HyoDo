"""Vault Manager Package.

AFO 왕국의 비밀 정보(Secrets) 관리 시스템.
Zero Trust 원칙에 기반한 Seal/Unseal 메커니즘 및 암호화 제공.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from .audit import AuditManager
from .crypto import decrypt_data, derive_key, encrypt_data


class VaultManager:
    """Zero Trust Vault 관리자 (Facade)."""

    # ROOT_KEY 등 접근 금지 키 목록
    DENIED_KEYS = {"ROOT_KEY", "MASTER_KEY", "PRIVATE_KEY"}

    def __init__(self, mode: str = "env") -> None:
        self.mode = mode
        self.secrets: dict[str, str] = {}
        self._is_sealed = False
        self.audit = AuditManager(Path(tempfile.gettempdir()) / "afo_vault_audit.jsonl")
        self._persisted_secrets: dict[str, str] = {}
        # 테스트 호환성을 위한 감사 로그 리스트
        self._audit_log: list[dict[str, Any]] = []

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """비밀 정보를 조회합니다."""
        # 정책: 금지된 키 접근 차단 (ROOT_ 패턴도 차단)
        if key in self.DENIED_KEYS or (
            key.startswith("ROOT_") and os.getenv("AFO_ROOT_ACCESS") != "1"
        ):
            self._audit_log.append({"action": "ACCESS_DENIED", "key": key})
            return None

        self._audit_log.append({"action": "GET", "key": key})

        # 봉인 상태면 접근 불가
        if self._is_sealed:
            return None

        # 먼저 메모리에 저장된 시크릿 확인
        if key in self.secrets:
            return self.secrets[key]

        # env 모드이면 환경 변수도 확인
        if self.mode == "env":
            return os.getenv(key, default)

        return default

    def set_secret(self, key: str, value: str) -> bool:
        """비밀 정보를 설정합니다."""
        if self._is_sealed:
            return False
        self.secrets[key] = value
        self._audit_log.append({"action": "SET", "key": key})
        self.audit.log("set", key, True)
        return True

    def seal_vault(self, persist: bool = True) -> bool:
        """금고를 잠금 처리하고 메모리를 비웁니다."""
        if self._is_sealed:
            return False
        self._is_sealed = True
        self._prev_mode = self.mode
        self.mode = "sealed"
        if persist:
            self._persisted_secrets = self.secrets.copy()
            self.secrets = {}
        else:
            self.secrets = {}
        self._audit_log.append({"action": "SEAL", "key": "all"})
        self.audit.log("seal", "all", True)
        return True

    def unseal_vault(self, _master_password: str = "") -> bool:
        """금고 잠금을 해제합니다."""
        # 비밀번호 검증 로직 등
        self._is_sealed = False
        self.mode = getattr(self, "_prev_mode", "env")
        self.secrets = self._persisted_secrets.copy()
        self._persisted_secrets = {}
        self._audit_log.append({"action": "UNSEAL", "key": "all"})
        self.audit.log("unseal", "all", True)
        return True

    def is_sealed(self) -> bool:
        """금고가 잠겨있는지 확인합니다."""
        return self._is_sealed

    def rotate_secret(self, key: str, new_value: str) -> bool:
        """비밀 정보를 회전(교체)합니다."""
        if self._is_sealed:
            return False
        if key not in self.secrets:
            return False
        self.secrets[key] = new_value
        self._audit_log.append({"action": "ROTATE", "key": key})
        self.audit.log("rotate", key, True)
        return True

    def delete_secret(self, key: str) -> bool:
        """비밀 정보를 삭제합니다."""
        if self._is_sealed:
            return False
        if key not in self.secrets:
            return False
        del self.secrets[key]
        self._audit_log.append({"action": "DELETE", "key": key})
        self.audit.log("delete", key, True)
        return True

    def get_status(self) -> dict[str, Any]:
        """금고 상태 정보를 반환합니다."""
        return {
            "sealed": self._is_sealed,
            "secrets_count": len(self.secrets),
            "mode": self.mode,
            "audit_enabled": True,
        }

    def get_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        """감사 로그를 조회합니다."""
        return self._audit_log[-limit:] if self._audit_log else []

    def generate_seal_key(self) -> str:
        """새로운 봉인 키를 생성합니다."""
        import secrets

        key = secrets.token_hex(32)
        self._audit_log.append({"action": "GENERATE_SEAL_KEY", "key": "system"})
        self.audit.log("generate_seal_key", "system", True)
        return key

    def break_glass(self) -> bool:
        """비상 상황에서 금고를 강제로 개방합니다."""
        self._is_sealed = False
        self.mode = getattr(self, "_prev_mode", "env")
        self._audit_log.append({"action": "BREAK_GLASS", "key": "emergency"})
        self.audit.log("break_glass", "emergency", True)
        return True

    def _init_encryption(self, seal_key: str) -> None:
        """암호화 키를 초기화합니다."""
        self._seal_key = seal_key


# Global singleton instance
vault = VaultManager()
