# Trinity Score: 97.0 (Operational Transform for Real-time Collaboration)
"""
Operational Transform (OT) Service (PH-SE-10.01)

실시간 협업을 위한 충돌 해결 알고리즘.
커뮤터티브 연산 변환으로 다중 사용자 편집 충돌을 자동 해결.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# OT Operation Types
# ============================================================================


class OperationType(str, Enum):
    """연산 유형."""

    INSERT_NODE = "insert_node"
    DELETE_NODE = "delete_node"
    UPDATE_NODE = "update_node"
    MOVE_NODE = "move_node"
    INSERT_CONNECTION = "insert_connection"
    DELETE_CONNECTION = "delete_connection"
    UPDATE_CONNECTION = "update_connection"


class OperationPriority(str, Enum):
    """연산 우선순위."""

    HIGH = "high"  # 관리자 연산
    MEDIUM = "medium"  # 일반 편집
    LOW = "low"  # 읽기 전용


# ============================================================================
# Core Operation Classes
# ============================================================================


@dataclass
class Operation:
    """다이어그램 편집 연산."""

    id: str = field(default_factory=lambda: f"op_{datetime.now(UTC).timestamp()}")
    type: OperationType = OperationType.UPDATE_NODE
    element_id: str = ""
    user_id: str = ""
    session_id: str = ""
    priority: OperationPriority = OperationPriority.MEDIUM

    # 연산 데이터
    data: dict[str, Any] = field(default_factory=dict)
    old_data: dict[str, Any] = field(default_factory=dict)  # undo용

    # 메타데이터
    timestamp: float = field(default_factory=lambda: datetime.now(UTC).timestamp())
    version: int = 0
    dependencies: list[str] = field(default_factory=list)  # 의존하는 연산 ID들

    def to_dict(self) -> dict[str, Any]:
        """직렬화를 위한 딕셔너리 변환."""
        return {
            "id": self.id,
            "type": self.type.value,
            "element_id": self.element_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "priority": self.priority.value,
            "data": self.data,
            "old_data": self.old_data,
            "timestamp": self.timestamp,
            "version": self.version,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Operation":
        """딕셔너리로부터 Operation 생성."""
        return cls(
            id=data.get("id", ""),
            type=OperationType(data.get("type", "update_node")),
            element_id=data.get("element_id", ""),
            user_id=data.get("user_id", ""),
            session_id=data.get("session_id", ""),
            priority=OperationPriority(data.get("priority", "medium")),
            data=data.get("data", {}),
            old_data=data.get("old_data", {}),
            timestamp=data.get("timestamp", 0),
            version=data.get("version", 0),
            dependencies=data.get("dependencies", []),
        )

    def copy(self) -> "Operation":
        """Operation 객체 복사본 생성."""
        return Operation(
            id=self.id,
            type=self.type,
            element_id=self.element_id,
            user_id=self.user_id,
            session_id=self.session_id,
            priority=self.priority,
            data=self.data.copy(),
            old_data=self.old_data.copy(),
            timestamp=self.timestamp,
            version=self.version,
            dependencies=self.dependencies.copy(),
        )


@dataclass
class OperationPair:
    """변환할 두 연산의 쌍."""

    op1: Operation
    op2: Operation

    def __post_init__(self) -> None:
        # 시간순으로 정렬 (op1이 먼저, op2가 나중)
        if self.op1.timestamp > self.op2.timestamp:
            self.op1, self.op2 = self.op2, self.op1


# ============================================================================
# Conflict Detection
# ============================================================================


class ConflictDetector:
    """충돌 감지기."""

    @staticmethod
    def detect_conflict(op1: Operation, op2: Operation) -> bool:
        """두 연산 간 충돌 감지.

        충돌 조건:
        1. 동일한 요소에 대한 서로 다른 타입의 연산
        2. 한 연산이 다른 연산의 결과를 변경
        3. 순서 의존성 위반
        """
        # 동일 요소에 대한 연산인지 확인
        if op1.element_id != op2.element_id:
            return False

        # 노드 관련 연산들
        node_ops = {
            OperationType.INSERT_NODE,
            OperationType.DELETE_NODE,
            OperationType.UPDATE_NODE,
            OperationType.MOVE_NODE,
        }

        # 연결 관련 연산들
        conn_ops = {
            OperationType.INSERT_CONNECTION,
            OperationType.DELETE_CONNECTION,
            OperationType.UPDATE_CONNECTION,
        }

        # 노드 연산 간 충돌
        if op1.type in node_ops and op2.type in node_ops:
            return ConflictDetector._detect_node_conflict(op1, op2)

        # 연결 연산 간 충돌
        if op1.type in conn_ops and op2.type in conn_ops:
            return ConflictDetector._detect_connection_conflict(op1, op2)

        # 노드와 연결 간 충돌 (연결이 노드에 의존)
        if (op1.type in node_ops and op2.type in conn_ops) or (
            op1.type in conn_ops and op2.type in node_ops
        ):
            return ConflictDetector._detect_node_connection_conflict(op1, op2)

        return False

    @staticmethod
    def _detect_node_conflict(op1: Operation, op2: Operation) -> bool:
        """노드 연산 간 충돌 감지."""
        # INSERT vs DELETE: 항상 충돌
        if (op1.type == OperationType.INSERT_NODE and op2.type == OperationType.DELETE_NODE) or (
            op1.type == OperationType.DELETE_NODE and op2.type == OperationType.INSERT_NODE
        ):
            return True

        # DELETE vs UPDATE: 충돌 (삭제 후 업데이트 불가)
        if (op1.type == OperationType.DELETE_NODE and op2.type == OperationType.UPDATE_NODE) or (
            op1.type == OperationType.UPDATE_NODE and op2.type == OperationType.DELETE_NODE
        ):
            return True

        # 동일한 속성 UPDATE: 충돌 가능성 (값에 따라)
        if op1.type == op2.type == OperationType.UPDATE_NODE:
            return ConflictDetector._detect_update_conflict(op1, op2)

        return False

    @staticmethod
    def _detect_connection_conflict(op1: Operation, op2: Operation) -> bool:
        """연결 연산 간 충돌 감지."""
        # 유사한 논리로 연결 충돌 감지
        return bool(
            (
                op1.type == OperationType.INSERT_CONNECTION
                and op2.type == OperationType.DELETE_CONNECTION
            )
            or (
                op1.type == OperationType.DELETE_CONNECTION
                and op2.type == OperationType.INSERT_CONNECTION
            )
        )

    @staticmethod
    def _detect_node_connection_conflict(op1: Operation, op2: Operation) -> bool:
        """노드-연결 간 충돌 감지."""
        # 노드가 삭제되면 연결도 영향을 받음
        node_op = op1 if op1.type in {OperationType.DELETE_NODE} else op2
        conn_op = op2 if op1.type in {OperationType.DELETE_NODE} else op1

        # 삭제되는 노드에 연결된 경우 충돌
        return node_op.type == OperationType.DELETE_NODE and (
            conn_op.data.get("from") == node_op.element_id
            or conn_op.data.get("to") == node_op.element_id
        )

    @staticmethod
    def _detect_update_conflict(op1: Operation, op2: Operation) -> bool:
        """UPDATE 연산 간 충돌 감지."""
        # 동일한 속성을 변경하는 경우 충돌
        op1_keys = set(op1.data.keys())
        op2_keys = set(op2.data.keys())

        return bool(op1_keys & op2_keys)  # 교집합이 있으면 충돌


# ============================================================================
# Operational Transform Engine
# ============================================================================


class OperationalTransformer:
    """Operational Transform 엔진."""

    def transform(self, pair: OperationPair) -> tuple[Operation, Operation]:
        """두 연산을 상호 변환.

        Args:
            pair: 변환할 연산 쌍 (op1이 op2보다 먼저 수행된 것으로 가정)

        Returns:
            변환된 연산 쌍 (op1', op2')
        """
        op1, op2 = pair.op1, pair.op2

        # 충돌하지 않으면 변환 불필요
        if not ConflictDetector.detect_conflict(op1, op2):
            return op1, op2

        # 연산 유형별 변환
        if op1.type == OperationType.UPDATE_NODE and op2.type == OperationType.UPDATE_NODE:
            return self._transform_update_update(op1, op2)

        elif op1.type == OperationType.INSERT_NODE and op2.type == OperationType.DELETE_NODE:
            return self._transform_insert_delete(op1, op2)

        elif op1.type == OperationType.DELETE_NODE and op2.type == OperationType.INSERT_NODE:
            return self._transform_delete_insert(op1, op2)

        else:
            # 기본적으로 op1을 우선시 (시간순)
            return op1, self._nullify_operation(op2)

    def _transform_update_update(
        self, op1: Operation, op2: Operation
    ) -> tuple[Operation, Operation]:
        """UPDATE vs UPDATE 변환."""
        # op1의 변경사항을 op2에 적용
        transformed_op2 = op1.copy()
        transformed_op2.data = {**op2.data, **op1.data}  # op1의 변경사항을 우선
        transformed_op2.id = f"{op2.id}_transformed"
        transformed_op2.dependencies.append(op1.id)

        # op1은 변경 없음
        return op1, transformed_op2

    def _transform_insert_delete(
        self, op1: Operation, op2: Operation
    ) -> tuple[Operation, Operation]:
        """INSERT vs DELETE 변환."""
        # INSERT 후 DELETE는 서로 상쇄
        return self._nullify_operation(op1), self._nullify_operation(op2)

    def _transform_delete_insert(
        self, op1: Operation, op2: Operation
    ) -> tuple[Operation, Operation]:
        """DELETE vs INSERT 변환."""
        # DELETE 후 INSERT는 UPDATE로 변환
        update_op = Operation(
            type=OperationType.UPDATE_NODE,
            element_id=op1.element_id,
            user_id=op2.user_id,  # 나중 연산의 사용자
            session_id=op2.session_id,
            data=op2.data,
            old_data=op1.old_data,
            dependencies=[op1.id, op2.id],
        )
        return op1, update_op

    def _nullify_operation(self, op: Operation) -> Operation:
        """연산을 무효화 (no-op로 변환)."""
        null_op = op.copy()
        null_op.type = OperationType.UPDATE_NODE
        null_op.data = {}
        null_op.id = f"{op.id}_nullified"
        return null_op


# ============================================================================
# Conflict Resolution
# ============================================================================


class ConflictResolver:
    """충돌 해결자."""

    def __init__(self, transformer: OperationalTransformer = None) -> None:
        self.transformer = transformer or OperationalTransformer()

    def resolve_conflicts(self, operations: list[Operation]) -> list[Operation]:
        """연산 리스트에서 충돌을 해결.

        Args:
            operations: 시간순으로 정렬된 연산 리스트

        Returns:
            충돌이 해결된 연산 리스트
        """
        if len(operations) <= 1:
            return operations

        resolved = []

        for i, op in enumerate(operations):
            current_op = op

            # 이전 모든 연산과 비교하여 변환
            for prev_op in resolved:
                if ConflictDetector.detect_conflict(prev_op, current_op):
                    _, transformed_op = self.transformer.transform(
                        OperationPair(prev_op, current_op)
                    )
                    current_op = transformed_op

            resolved.append(current_op)

        return resolved

    def resolve_priority_conflicts(self, operations: list[Operation]) -> list[Operation]:
        """우선순위 기반 충돌 해결."""
        # 우선순위에 따라 정렬
        priority_order = {
            OperationPriority.HIGH: 0,
            OperationPriority.MEDIUM: 1,
            OperationPriority.LOW: 2,
        }

        sorted_ops = sorted(operations, key=lambda op: priority_order[op.priority])

        # 우선순위가 높은 연산을 먼저 적용
        resolved = []
        for op in sorted_ops:
            # 우선순위가 높은 연산은 그대로 적용
            if op.priority == OperationPriority.HIGH:
                resolved.append(op)
            else:
                # 다른 연산들과의 충돌 해결
                current_op = op
                for prev_op in resolved:
                    if ConflictDetector.detect_conflict(prev_op, current_op):
                        _, transformed_op = self.transformer.transform(
                            OperationPair(prev_op, current_op)
                        )
                        current_op = transformed_op
                resolved.append(current_op)

        return resolved


# ============================================================================
# Operation History & Undo/Redo
# ============================================================================


@dataclass
class OperationHistory:
    """연산 히스토리 관리."""

    operations: list[Operation] = field(default_factory=list)
    undo_stack: list[Operation] = field(default_factory=list)
    redo_stack: list[Operation] = field(default_factory=list)

    def add_operation(self, operation: Operation) -> None:
        """연산 추가."""
        self.operations.append(operation)
        self.redo_stack.clear()  # 새로운 연산 추가 시 redo 초기화

    def undo(self) -> Operation | None:
        """마지막 연산 취소."""
        if not self.operations:
            return None

        last_op = self.operations.pop()
        self.undo_stack.append(last_op)

        # 역연산 생성
        inverse_op = self._create_inverse_operation(last_op)
        return inverse_op

    def redo(self) -> Operation | None:
        """취소된 연산 재실행."""
        if not self.undo_stack:
            return None

        op = self.undo_stack.pop()
        self.operations.append(op)
        return op

    def _create_inverse_operation(self, operation: Operation) -> Operation:
        """역연산 생성."""
        inverse = operation.copy()
        inverse.id = f"{operation.id}_inverse"
        inverse.timestamp = datetime.now(UTC).timestamp()

        if operation.type == OperationType.INSERT_NODE:
            inverse.type = OperationType.DELETE_NODE
        elif operation.type == OperationType.DELETE_NODE:
            inverse.type = OperationType.INSERT_NODE
        elif operation.type == OperationType.UPDATE_NODE:
            # old_data와 data를 교환
            inverse.data = operation.old_data
            inverse.old_data = operation.data

        return inverse


# ============================================================================
# Integration with Collaboration System
# ============================================================================


class CollaborativeEditor:
    """협업 편집기 - OT와 협업 시스템 통합."""

    def __init__(self) -> None:
        self.transformer = OperationalTransformer()
        self.resolver = ConflictResolver(self.transformer)
        self.history = OperationHistory()
        self.pending_operations: list[Operation] = []

    def apply_operation(self, operation: Operation) -> list[Operation]:
        """연산 적용 및 충돌 해결.

        Args:
            operation: 적용할 연산

        Returns:
            브로드캐스트할 연산 리스트
        """
        # 대기 중인 연산들과 함께 충돌 해결
        all_ops = [*self.pending_operations, operation]
        resolved_ops = self.resolver.resolve_conflicts(all_ops)

        # 해결된 연산들 적용
        broadcast_ops = []
        for op in resolved_ops:
            if op.id == operation.id:
                # 새 연산인 경우에만 브로드캐스트
                broadcast_ops.append(op)
                self.history.add_operation(op)

        self.pending_operations.clear()
        return broadcast_ops

    def apply_remote_operation(self, operation: Operation) -> list[Operation]:
        """원격 연산 적용.

        Args:
            operation: 원격에서 받은 연산

        Returns:
            로컬에서 재적용할 연산 리스트
        """
        # 로컬 히스토리와의 충돌 해결
        local_ops = self.history.operations[-10:]  # 최근 10개 연산만 고려
        all_ops = [*local_ops, operation]

        resolved_ops = self.resolver.resolve_conflicts(all_ops)

        # 새 연산들만 추출
        new_ops = resolved_ops[len(local_ops) :]

        # 히스토리에 추가
        for op in new_ops:
            self.history.add_operation(op)

        return new_ops

    def get_operation_history(self, limit: int = 50) -> list[Operation]:
        """연산 히스토리 조회."""
        return self.history.operations[-limit:]

    def undo_last_operation(self) -> Operation | None:
        """마지막 연산 취소."""
        return self.history.undo()

    def redo_last_operation(self) -> Operation | None:
        """취소된 연산 재실행."""
        return self.history.redo()


# ============================================================================
# Testing & Validation
# ============================================================================


def test_basic_ot() -> bool:
    """기본 OT 기능 테스트."""
    try:
        # 두 개의 충돌하는 UPDATE 연산 생성
        op1 = Operation(
            type=OperationType.UPDATE_NODE,
            element_id="node1",
            user_id="user1",
            data={"x": 100, "y": 200},
            old_data={"x": 0, "y": 0},
        )

        op2 = Operation(
            type=OperationType.UPDATE_NODE,
            element_id="node1",
            user_id="user2",
            data={"x": 150, "label": "Updated"},
            old_data={"x": 0, "y": 0},
        )

        # 충돌 감지
        has_conflict = ConflictDetector.detect_conflict(op1, op2)
        assert has_conflict, "충돌이 감지되어야 함"

        # 연산 변환
        transformer = OperationalTransformer()
        _transformed_op1, transformed_op2 = transformer.transform(OperationPair(op1, op2))

        # 변환 결과 검증
        assert transformed_op2.data.get("x") == 100, "op1의 변경사항이 op2에 적용되어야 함"

        print("✅ OT 기본 테스트 통과")
        return True

    except Exception as e:
        print(f"❌ OT 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_basic_ot()
