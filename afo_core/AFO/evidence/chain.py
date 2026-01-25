"""
Evidence Chain - 암호화된 증거 연결 고리

증거 체인은 블록체인 원리를 적용하여 증거의 무결성을 보장합니다.
"""

import hashlib
import json
from datetime import datetime
from typing import Any


class EvidenceChain:
    """증거 체인 - 암호화된 증거 연결 고리"""

    def __init__(self, evidence_data: dict[str, Any], previous_hash: str | None = None) -> None:
        self.timestamp = datetime.now().isoformat()
        self.evidence_data = evidence_data
        self.previous_hash = previous_hash
        self.nonce = 0  # 간단한 proof-of-work용

        # 체인 해시 생성
        self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """SHA256 해시 계산"""
        # 간단한 proof-of-work (nonce 찾기)
        while True:
            block_data = {
                "timestamp": self.timestamp,
                "evidence_data": self.evidence_data,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            }

            block_string = json.dumps(block_data, sort_keys=True)
            hash_value = hashlib.sha256(block_string.encode()).hexdigest()

            # 간단한 difficulty: 해시가 '00'으로 시작
            if hash_value.startswith("00"):
                return hash_value

            self.nonce += 1
