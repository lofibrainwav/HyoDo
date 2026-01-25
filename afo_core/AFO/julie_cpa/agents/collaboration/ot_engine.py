"""Operational Transform Engine.

실시간 편집 충돌 해결을 위한 OT(Operational Transform) 로직.
"""

from __future__ import annotations

from typing import Any


class OTEngine:
    """운영 변환(Operational Transform) 엔진."""

    @staticmethod
    def transform_operation(
        operation: dict[str, Any], concurrent_operations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """다른 동시 작업들에 대해 현재 작업을 변환합니다."""
        transformed_op = operation.copy()

        for concurrent_op in concurrent_operations:
            transformed_op = OTEngine._resolve_conflict(transformed_op, concurrent_op)

        return transformed_op

    @staticmethod
    def _resolve_conflict(op1: dict[str, Any], op2: dict[str, Any]) -> dict[str, Any]:
        """두 작업 간의 충돌을 해결하여 op1을 변환합니다."""
        # 기본적으로 동일한 위치의 편집 시 user_id 사전순 등 우선순위 적용 (단순화된 로직)
        if OTEngine._is_conflicting(op1, op2):
            # 실제 OT 로직 구현 (원본 파일의 _resolve_operation_conflict 참고)
            # 여기서는 예시로 op1의 인덱스를 조정하거나 속성을 병합하는 등의 로직이 들어감
            pass

        return op1

    @staticmethod
    def _is_conflicting(op1: dict[str, Any], op2: dict[str, Any]) -> bool:
        """두 작업이 충돌하는지 확인합니다."""
        if op1.get("document_id") != op2.get("document_id"):
            return False

        # 동일한 인덱스에 작업을 시도하는 경우 등
        return op1.get("index") == op2.get("index") and op1.get("type") == op2.get("type")


def apply_operation_to_doc(document: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    """변환된 작업을 문서 데이터에 실제로 적용합니다."""
    op_type = operation.get("type")

    if op_type == "text_edit":
        # 텍스트 수정 로직
        pass
    elif op_type == "data_update":
        # 필드 값 업데이트
        field = operation.get("field")
        value = operation.get("value")
        if field:
            document[field] = value
    elif op_type == "structure_change":
        # 문서 구조 변경
        pass

    return document
