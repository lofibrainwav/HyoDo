"""
Encryption Utils - 데이터 암호화 유틸리티

善 (Yi Sun-sin): 보안/리스크 평가
- Fernet 암호화 (cryptography 라이브러리)
- 보안 키 생성 및 관리
- 데이터 보호
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    Fernet = None
    InvalidToken = None

logger = logging.getLogger(__name__)


class EncryptionUtils:
    """암호화 유틸리티 클래스"""

    def __init__(self) -> None:
        """암호화 유틸리티 초기화"""
        if Fernet is None:
            logger.warning("cryptography 라이브러리가 설치되지 않음")
            return

        logger.info("암호화 유틸리티 초기화 완료")

    def generate_key(self) -> str:
        """
        Fernet 키 생성

        Returns:
            URL-safe base64 인코딩된 32-byte 키
        """
        key = Fernet.generate_key()
        logger.debug(f"Fernet 키 생성: 길이={len(key)}")
        return key

    def validate_key(self, key: str) -> bool:
        """
        Fernet 키 유효성 검증

        Args:
            key: 검증할 키

        Returns:
            True if 유효함, False if 무효함
        """
        try:
            Fernet(key)
            logger.debug("Fernet 키 유효성 검증: PASS")
            return True
        except Exception as e:
            logger.warning(f"Fernet 키 유효성 검증: FAIL - {e}")
            return False

    def encrypt(self, data: str | bytes, key: str | None = None, encoding: str = "utf-8") -> str:
        """
        데이터 암호화

        Args:
            data: 암호화할 데이터
            key: Fernet 키 (None이면 자동 생성)
            encoding: 문자열 인코딩

        Returns:
            Base64 인코딩된 암호문

        Raises:
            ValueError: 데이터가 None
            Exception: 암호화 실패
        """
        if Fernet is None:
            raise RuntimeError("cryptography 라이브러리가 설치되지 않음")

        if data is None:
            raise ValueError("데이터가 None입니다")

        if key is None:
            key = self.generate_key()

        if not self.validate_key(key):
            raise ValueError("무효한 Fernet 키")

        if isinstance(data, str):
            data = data.encode(encoding)

        fernet = Fernet(key)
        encrypted = fernet.encrypt(data)
        encrypted_b64 = encrypted.decode(encoding)

        logger.debug(f"암호화 완료: 원본={len(data)}바이트, 암호문={len(encrypted_b64)}바이트")

        return encrypted_b64

    def decrypt(self, encrypted_data: str, key: str | None = None, encoding: str = "utf-8") -> str:
        """
        데이터 복호화

        Args:
            encrypted_data: 암호문 (Base64 인코딩)
            key: Fernet 키
            encoding: 문자열 인코딩

        Returns:
            복호화된 문자열

        Raises:
            ValueError: 암호문이 None
            Exception: 복호화 실패
        """
        if Fernet is None:
            raise RuntimeError("cryptography 라이브러리가 설치되지 않음")

        if encrypted_data is None:
            raise ValueError("암호문이 None입니다")

        if key is None:
            raise ValueError("키가 None입니다")

        if not self.validate_key(key):
            raise ValueError("무효한 Fernet 키")

        fernet = Fernet(key)

        try:
            decrypted = fernet.decrypt(encrypted_data)
            decrypted_str = decrypted.decode(encoding)

            logger.debug(
                f"복호화 완료: 암호문={len(encrypted_data)}바이트, 원본={len(decrypted_str)}바이트"
            )

            return decrypted_str
        except InvalidToken as e:
            logger.error(f"복호화 실패: {e}")
            raise

    def encrypt_dict(
        self, data: dict[str, Any], key: str | None = None, exclude_keys: set[str] | None = None
    ) -> dict[str, Any]:
        """
        딕셔너리 암호화 (민감 키 제외)

        Args:
            data: 암호화할 딕셔너리
            key: Fernet 키 (None이면 자동 생성)
            exclude_keys: 제외할 키 집합

        Returns:
            암호화된 딕셔너리
        """
        if exclude_keys is None:
            exclude_keys = set()

        encrypted = {}

        for k, value in data.items():
            if k in exclude_keys:
                encrypted[k] = value
            elif isinstance(value, (str, int, float, bool)):
                encrypted[k] = self.encrypt(str(value), k)
            elif isinstance(value, dict):
                encrypted[k] = self.encrypt_dict(value, k, exclude_keys)
            else:
                encrypted[k] = value  # Keep other types as-is

        logger.debug(f"딕셔너리 암호화 완료: {len(encrypted)}개 키, 제외={len(exclude_keys)}개 키")

        return encrypted

    def decrypt_dict(
        self,
        encrypted_data: dict[str, Any],
        key: str | None = None,
        exclude_keys: set[str] | None = None,
    ) -> dict[str, Any]:
        """
        딕셔너리 복호화 (민감 키 제외)

        Args:
            encrypted_data: 암호화된 딕셔너리
            key: Fernet 키 (None이면 자동 생성)
            exclude_keys: 제외할 키 집합

        Returns:
            복호화된 딕셔너리
        """
        if exclude_keys is None:
            exclude_keys = set()

        decrypted = {}

        for k, value in encrypted_data.items():
            if k in exclude_keys:
                decrypted[k] = value
            elif isinstance(value, str) and k.endswith("_encrypted"):
                decrypted[k] = self.decrypt(value, k)
            elif isinstance(value, dict):
                decrypted[k] = self.decrypt_dict(value, k, exclude_keys)
            else:
                decrypted[k] = value  # Keep other types as-is

        logger.debug(f"딕셔너리 복호화 완료: {len(decrypted)}개 키")

        return decrypted

    def hash_data(self, data: str, algorithm: str = "sha256") -> str:
        """
        데이터 해시 (암호화된 값 비교용)

        Args:
            data: 해시할 데이터
            algorithm: 해시 알고리즘

        Returns:
            16진수 해시 문자열
        """
        import hashlib

        hash_obj = hashlib.new(algorithm)
        hash_obj.update(data.encode())

        hex_hash = hash_obj.hexdigest()

        logger.debug(f"데이터 해시: 알고리즘={algorithm}, 해시={hex_hash[:16]}...")

        return hex_hash


class SecureKeyManager:
    """보안 키 관리자"""

    def __init__(self, key_file: str = "data/encryption.key") -> None:
        self.key_file = key_file
        self.key: str | None = None

    def initialize(self) -> str:
        """키 관리자 초기화"""
        from pathlib import Path

        key_path = Path(self.key_file)

        if key_path.exists():
            with open(key_path) as f:
                self.key = f.read().strip()
            logger.info("기존 키 로드 완료")
        else:
            self.key = self._encryption_utils().generate_key()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(key_path, "w") as f:
                f.write(self.key)
            logger.info("새 키 생성 완료")

        return self.key

    def rotate_key(self) -> str:
        """키 교체"""
        new_key = self._encryption_utils().generate_key()

        logger.info("키 교체 완료")

        return new_key

    def get_key(self) -> str:
        """키 반환"""
        if self.key is None:
            raise ValueError("키 관리자가 초기화되지 않음")

        return self.key


# Convenience Functions
def generate_key() -> str:
    """Fernet 키 생성 (편의 함수)"""
    return EncryptionUtils().generate_key()


def encrypt(data: str | bytes, key: str | None = None, encoding: str = "utf-8") -> str:
    """데이터 암호화 (편의 함수)"""
    return EncryptionUtils().encrypt(data, key, encoding)


def decrypt(encrypted_data: str, key: str | None = None, encoding: str = "utf-8") -> str:
    """데이터 복호화 (편의 함수)"""
    return EncryptionUtils().decrypt(encrypted_data, key, encoding)


def encrypt_dict(
    data: dict[str, Any], key: str | None = None, exclude_keys: set[str] | None = None
) -> dict[str, Any]:
    """딕셔너리 암호화 (편의 함수)"""
    return EncryptionUtils().encrypt_dict(data, key, exclude_keys)


def decrypt_dict(
    encrypted_data: dict[str, Any], key: str | None = None, exclude_keys: set[str] | None = None
) -> dict[str, Any]:
    """딕셔너리 복호화 (편의 함수)"""
    return EncryptionUtils().decrypt_dict(encrypted_data, key, exclude_keys)


def hash_data(data: str, algorithm: str = "sha256") -> str:
    """데이터 해시 (편의 함수)"""
    return EncryptionUtils().hash_data(data, algorithm)


__all__ = [
    "EncryptionUtils",
    "SecureKeyManager",
    "generate_key",
    "encrypt",
    "decrypt",
    "encrypt_dict",
    "decrypt_dict",
]
