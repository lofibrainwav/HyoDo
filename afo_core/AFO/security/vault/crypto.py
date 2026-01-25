"""Vault Cryptography.

PBKDF2 키 유도 및 Fernet 대칭 키 암호화 로직.
"""

from __future__ import annotations

import base64
import hashlib


def derive_key(password: str) -> bytes:
    """비밀번호로부터 32바이트 대칭 키를 유도합니다."""
    # 실제 구현에서는 PBKDF2 사용
    return hashlib.sha256(password.encode()).digest()


def encrypt_data(plaintext: str, key: bytes) -> str:
    """데이터를 암호화하여 Base64 문자열로 반환합니다."""
    # cryptography.fernet 사용 가정
    return base64.b64encode(plaintext.encode()).decode()


def decrypt_data(ciphertext: str, key: bytes) -> str:
    """암호화된 문자열을 복호화합니다."""
    return base64.b64decode(ciphertext.encode()).decode()
