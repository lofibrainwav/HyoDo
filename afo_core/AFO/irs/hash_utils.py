"""
Hash Utils - 해시 기반 변경 감지 유틸리티

眞 (장영실 - Jang Yeong-sil): 아키텍처 설계
- SHA256 해시 생성
- 해시 비교 알고리즘
- 무결성 검증
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class HashUtils:
    """해시 유틸리티 클래스"""

    # 지원하는 해시 알고리즘
    SUPPORTED_ALGORITHMS = {
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
    }

    # 기본 해시 알고리즘
    DEFAULT_ALGORITHM = "sha256"
    DEFAULT_ENCODING = "utf-8"

    @staticmethod
    def calculate_hash(
        content: str | bytes,
        algorithm: str = DEFAULT_ALGORITHM,
        encoding: str = DEFAULT_ENCODING,
    ) -> str:
        """
        콘텐츠 해시 계산

        Args:
            content: 해시할 콘텐츠 (문자열 또는 바이트)
            algorithm: 해시 알고리즘 (sha256, sha512, md5, sha1)
            encoding: 문자열 인코딩

        Returns:
            16진수 해시 문자열

        Raises:
            ValueError: 지원하지 않는 알고리즘
        """
        if algorithm not in HashUtils.SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"지원하지 않는 알고리즘: {algorithm}. "
                f"지원: {', '.join(HashUtils.SUPPORTED_ALGORITHMS.keys())}"
            )

        if isinstance(content, str):
            content = content.encode(encoding)

        # 해시 계산
        hash_func = HashUtils.SUPPORTED_ALGORITHMS[algorithm]
        hash_obj = hash_func()
        hash_obj.update(content)

        hex_hash = hash_obj.hexdigest()

        logger.debug(
            f"해시 계산: 알고리즘={algorithm}, 길이={len(hex_hash)}, 앞부분={hex_hash[:16]}..."
        )

        return hex_hash

    @staticmethod
    def calculate_file_hash(
        file_path: str | Path,
        algorithm: str = DEFAULT_ALGORITHM,
        _encoding: str = DEFAULT_ENCODING,
    ) -> str:
        """
        파일 해시 계산

        Args:
            file_path: 파일 경로
            algorithm: 해시 알고리즘
            encoding: 인코딩

        Returns:
            16진수 해시 문자열

        Raises:
            FileNotFoundError: 파일이 존재하지 않음
            ValueError: 지원하지 않는 알고리즘
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"파일이 존재하지 않음: {file_path}")

        # 파일 읽기 (대용량 파일 청크 단위로)
        if algorithm not in HashUtils.SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"지원하지 않는 알고리즘: {algorithm}. "
                f"지원: {', '.join(HashUtils.SUPPORTED_ALGORITHMS.keys())}"
            )

        hash_func = HashUtils.SUPPORTED_ALGORITHMS[algorithm]
        hash_obj = hash_func()

        file_size = file_path.stat().st_size
        chunk_size = 8192  # 8KB 청크

        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hash_obj.update(chunk)

        hex_hash = hash_obj.hexdigest()

        logger.debug(
            f"파일 해시 계산: 경로={file_path.name}, 크기={file_size}바이트, "
            f"알고리즘={algorithm}, 해시={hex_hash[:16]}..."
        )

        return hex_hash

    @staticmethod
    def compare_hashes(
        hash1: str, hash2: str, algorithm: str = DEFAULT_ALGORITHM
    ) -> dict[str, Any]:
        """
        두 해시 비교

        Args:
            hash1: 첫 번째 해시
            hash2: 두 번째 해시
            algorithm: 해시 알고리즘 (검증용)

        Returns:
            비교 결과 딕셔너리
            {
                "equal": bool,  # 해시 일치 여부
                "algorithm": str,  # 사용된 알고리즘
                "hash1": str,  # 첫 번째 해시
                "hash2": str,  # 두 번째 해시
                "diff_count": int,  # 다른 비트 수 (SHA256은 256비트)
            }

        Raises:
            ValueError: 다른 길이의 해시
        """
        if len(hash1) != len(hash2):
            raise ValueError(f"다른 길이의 해시: hash1={len(hash1)}, hash2={len(hash2)}")

        if len(hash1) != 64:  # SHA256은 64자 (16진수)
            logger.warning(f"SHA256 해시 길이가 아님: {len(hash1)} (예상: 64)")

        equal = hash1 == hash2

        # 다른 비트 수 계산 (해밍 거리)
        hash1_int = int(hash1, 16)
        hash2_int = int(hash2, 16)
        diff_bits = bin(hash1_int ^ hash2_int).count("1")

        logger.debug(f"해시 비교: equal={equal}, 알고리즘={algorithm}, diff_bits={diff_bits}")

        return {
            "equal": equal,
            "algorithm": algorithm,
            "hash1": hash1,
            "hash2": hash2,
            "diff_bits": diff_bits,
        }

    @staticmethod
    def verify_integrity(
        content: str | bytes,
        expected_hash: str,
        algorithm: str = DEFAULT_ALGORITHM,
    ) -> bool:
        """
        무결성 검증

        Args:
            content: 검증할 콘텐츠
            expected_hash: 예상 해시
            algorithm: 해시 알고리즘

        Returns:
            True if 무결함, False if 손상됨
        """
        actual_hash = HashUtils.calculate_hash(content, algorithm)
        equal = actual_hash == expected_hash

        if equal:
            logger.debug("무결성 검증: ✅ PASS")
        else:
            logger.warning(
                f"무결성 검증: ❌ FAIL (예상: {expected_hash[:16]}..., 실제: {actual_hash[:16]}...)"
            )

        return equal

    @staticmethod
    def get_hash_info(hash_str: str) -> dict[str, Any]:
        """
        해시 정보 추출

        Args:
            hash_str: 해시 문자열

        Returns:
            해시 정보 딕셔너리
            {
                "length": int,  # 해시 길이
                "algorithm": str | None,  # 알고리즘 (추정)
                "prefix": str,  # 앞부분 16자
                "suffix": str,  # 뒤부분 16자
            }
        """
        hash_length = len(hash_str)
        algorithm = None

        # 알고리즘 추정 (길이 기반)
        if hash_length == 32:
            algorithm = "MD5"
        elif hash_length == 40:
            algorithm = "SHA1"
        elif hash_length == 64:
            algorithm = "SHA256"
        elif hash_length == 128:
            algorithm = "SHA512"

        prefix = hash_str[:16]
        suffix = hash_str[-16:] if hash_length > 32 else ""

        return {
            "length": hash_length,
            "algorithm": algorithm,
            "prefix": prefix,
            "suffix": suffix,
        }


# Convenience Functions
def calculate_hash(
    content: str | bytes,
    algorithm: str = HashUtils.DEFAULT_ALGORITHM,
    encoding: str = HashUtils.DEFAULT_ENCODING,
) -> str:
    """해시 계산 (편의 함수)"""
    return HashUtils.calculate_hash(content, algorithm, encoding)


def calculate_file_hash(
    file_path: str | Path,
    algorithm: str = HashUtils.DEFAULT_ALGORITHM,
    encoding: str = HashUtils.DEFAULT_ENCODING,
) -> str:
    """파일 해시 계산 (편의 함수)"""
    return HashUtils.calculate_file_hash(file_path, algorithm, encoding)


def compare_hashes(
    hash1: str, hash2: str, algorithm: str = HashUtils.DEFAULT_ALGORITHM
) -> dict[str, Any]:
    """해시 비교 (편의 함수)"""
    return HashUtils.compare_hashes(hash1, hash2, algorithm)


def verify_integrity(
    content: str | bytes,
    expected_hash: str,
    algorithm: str = HashUtils.DEFAULT_ALGORITHM,
) -> bool:
    """무결성 검증 (편의 함수)"""
    return HashUtils.verify_integrity(content, expected_hash, algorithm)


__all__ = [
    "HashUtils",
    "calculate_hash",
    "calculate_file_hash",
    "compare_hashes",
    "verify_integrity",
]
