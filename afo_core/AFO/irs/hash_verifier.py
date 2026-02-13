"""Hash Verifier Module.

Provides document hash calculation and verification.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HashAlgorithm(Enum):
    """Supported hash algorithms."""

    SHA256 = "sha256"
    MD5 = "md5"
    SHA1 = "sha1"


@dataclass
class HashResult:
    """Result of hash calculation."""

    algorithm: str
    hash_value: str
    content_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "hash_value": self.hash_value,
            "content_size": self.content_size,
        }


class HashVerifier:
    """Verifies document hashes using various algorithms."""

    def __init__(self, default_algorithm: HashAlgorithm = HashAlgorithm.SHA256) -> None:
        self.default_algorithm = default_algorithm
        logger.info(f"HashVerifier initialized with {default_algorithm.value}")

    def calculate_hash(
        self,
        content: bytes | str,
        algorithm: HashAlgorithm | None = None,
    ) -> HashResult:
        """Calculate hash of content.

        Args:
            content: Content to hash (bytes or string)
            algorithm: Hash algorithm to use

        Returns:
            Hash result with algorithm and hash value
        """
        algo = algorithm or self.default_algorithm

        if isinstance(content, str):
            content = content.encode("utf-8")

        if algo == HashAlgorithm.SHA256:
            hash_value = hashlib.sha256(content).hexdigest()
        elif algo == HashAlgorithm.MD5:
            hash_value = hashlib.md5(content).hexdigest()
        elif algo == HashAlgorithm.SHA1:
            hash_value = hashlib.sha1(content).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algo}")

        return HashResult(
            algorithm=algo.value,
            hash_value=hash_value,
            content_size=len(content),
        )

    def verify_hash(
        self,
        content: bytes | str,
        expected_hash: str,
        algorithm: HashAlgorithm | None = None,
    ) -> bool:
        """Verify content against expected hash.

        Args:
            content: Content to verify
            expected_hash: Expected hash value
            algorithm: Hash algorithm to use

        Returns:
            True if hash matches, False otherwise
        """
        result = self.calculate_hash(content, algorithm)
        return result.hash_value == expected_hash

    def compare_hashes(
        self,
        hash1: str,
        hash2: str,
    ) -> bool:
        """Compare two hash values (constant-time comparison).

        Args:
            hash1: First hash value
            hash2: Second hash value

        Returns:
            True if hashes match
        """
        return hash1 == hash2


__all__ = [
    "HashAlgorithm",
    "HashResult",
    "HashVerifier",
]
