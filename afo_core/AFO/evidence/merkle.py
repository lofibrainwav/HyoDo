"""
Merkle Tree - 증거 데이터 구조 최적화

Merkle Tree는 증거 데이터의 효율적인 검증을 위한 자료구조입니다.
"""

import hashlib


class MerkleTree:
    """Merkle Tree - 증거 데이터 구조 최적화"""

    def __init__(self, leaves: list[str]) -> None:
        self.leaves = leaves
        self.tree = self._build_tree(leaves)

    def _build_tree(self, nodes: list[str]) -> list[list[str]]:
        """Merkle Tree 구축"""
        tree = [nodes]

        while len(nodes) > 1:
            next_level = []

            for i in range(0, len(nodes), 2):
                left = nodes[i]
                right = nodes[i + 1] if i + 1 < len(nodes) else left

                combined = left + right
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())

            nodes = next_level
            tree.append(nodes)

        return tree

    def get_root(self) -> str:
        """Merkle Root 반환"""
        return self.tree[-1][0] if self.tree[-1] else ""

    def get_proof(self, leaf_index: int) -> list[dict[str, str]]:
        """Merkle Proof 생성"""
        proof = []
        index = leaf_index

        for level in range(len(self.tree) - 1):
            level_nodes = self.tree[level]
            is_right = index % 2 == 1
            sibling_index = index - 1 if is_right else index + 1

            if sibling_index < len(level_nodes):
                proof.append(
                    {
                        "position": "right" if is_right else "left",
                        "hash": level_nodes[sibling_index],
                    }
                )

            index = index // 2

        return proof
