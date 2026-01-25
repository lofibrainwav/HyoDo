# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Kingdom Action Validator - Visual Agent Safety Guardian
안전 게이트 5개를 통한 자동화된 액션 검증 시스템
"""

from dataclasses import dataclass
from datetime import UTC
from enum import Enum
from typing import Any, cast


class SafetyLevel(Enum):
    SAFE = "safe"
    CONFIRM = "confirm"
    BLOCK = "block"


class ActionType(Enum):
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    GOTO = "goto"


@dataclass
class ValidatedAction:
    """검증된 액션"""

    action_id: str
    type: ActionType
    bbox: dict[str, int]
    text: str | None
    confidence: float
    why: str
    safety: SafetyLevel
    validated_at: str
    risk_score: int
    is_allowed: bool
    block_reason: str | None = None


class ActionValidator:
    """Visual Agent 액션 검증기
    5개 안전 게이트를 통한 철저한 검증
    """

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 위험 액션 패턴
        self.destructive_patterns = [
            "delete",
            "remove",
            "clear",
            "reset",
            "pay",
            "purchase",
            "buy",
            "checkout",
            "logout",
            "signout",
            "exit",
            "submit",
            "send",
            "post",
            "publish",
        ]

        # 허용된 도메인 (환경변수에서 로드 가능)
        self.allowed_domains = [
            "localhost:3000",
            "localhost:8010",
            "github.com",
            "vercel.app",
        ]

    def validate_actions(
        self, actions: list[dict[str, Any]], context: dict[str, Any]
    ) -> list[ValidatedAction]:
        """액션 리스트 전체 검증
        5개 게이트를 순차적으로 적용
        """
        validated_actions: list[ValidatedAction] = []

        for i, action in enumerate(actions):
            try:
                validated = self._validate_single_action(action, context, i)

                # Gate 1: Max steps per turn (3-5개 제한)
                if len(validated_actions) >= 5:
                    validated.is_allowed = False
                    validated.block_reason = "Max steps per turn exceeded (5)"
                    validated.safety = SafetyLevel.BLOCK

                validated_actions.append(validated)

            except Exception as e:
                # 검증 실패 시 블록
                validated_actions.append(
                    ValidatedAction(
                        action_id=f"action_{i}",
                        type=ActionType.CLICK,  # fallback
                        bbox={"x": 0, "y": 0, "w": 0, "h": 0},
                        text=None,
                        confidence=0.0,
                        why="Validation failed",
                        safety=SafetyLevel.BLOCK,
                        validated_at=self._get_timestamp(),
                        risk_score=100,
                        is_allowed=False,
                        block_reason=f"Validation error: {e!s}",
                    )
                )

        return validated_actions

    def _validate_single_action(
        self, action: dict[str, Any], context: dict[str, Any], index: int
    ) -> ValidatedAction:
        """단일 액션 검증 (5개 게이트)"""
        action_id = f"action_{index}"

        # 기본 검증
        action_type = self._validate_action_type(cast("str", action.get("type")))
        bbox = self._validate_bbox(action.get("bbox", {}))
        confidence = max(0.0, min(1.0, action.get("confidence", 0.0)))

        # Gate 1: 좌표 검증 (화면 범위 내인지)
        if not self._is_bbox_valid(bbox):
            return ValidatedAction(
                action_id=action_id,
                type=action_type,
                bbox=bbox,
                text=action.get("text"),
                confidence=confidence,
                why=action.get("why", "Bbox validation failed"),
                safety=SafetyLevel.BLOCK,
                validated_at=self._get_timestamp(),
                risk_score=80,
                is_allowed=False,
                block_reason="Bounding box outside screen bounds",
            )

        # Gate 2: 도메인/앱 Allowlist 검증
        current_domain = context.get("domain", "")
        if not self._is_domain_allowed(current_domain):
            return ValidatedAction(
                action_id=action_id,
                type=action_type,
                bbox=bbox,
                text=action.get("text"),
                confidence=confidence,
                why=action.get("why", "Domain not allowed"),
                safety=SafetyLevel.BLOCK,
                validated_at=self._get_timestamp(),
                risk_score=90,
                is_allowed=False,
                block_reason=f"Domain not in allowlist: {current_domain}",
            )

        # Gate 3: 파괴적 액션 검증
        safety_level = self._assess_action_safety(action)

        # Gate 4: 신뢰도 검증 (낮은 신뢰도는 확인 필요)
        if confidence < 0.7:
            safety_level = SafetyLevel.CONFIRM

        # Gate 5: Trinity Score 재검증 (컨텍스트 기반)
        trinity_score = context.get("trinity_score", 95)
        risk_score = self._calculate_action_risk(action, context)

        if trinity_score < 90 or risk_score > 10:
            safety_level = SafetyLevel.BLOCK

        # 최종 판정
        is_allowed = safety_level != SafetyLevel.BLOCK
        block_reason = (
            None if is_allowed else f"Trinity Gate: {trinity_score}/90, Risk: {risk_score}/10"
        )

        return ValidatedAction(
            action_id=action_id,
            type=action_type,
            bbox=bbox,
            text=action.get("text"),
            confidence=confidence,
            why=action.get("why", "Action validated"),
            safety=safety_level,
            validated_at=self._get_timestamp(),
            risk_score=risk_score,
            is_allowed=is_allowed,
            block_reason=block_reason,
        )

    def _validate_action_type(self, action_type: str) -> ActionType:
        """액션 타입 검증"""
        try:
            return ActionType(action_type.upper())
        except ValueError:
            return ActionType.CLICK  # fallback

    def _validate_bbox(self, bbox: dict[str, Any]) -> dict[str, int]:
        """좌표 검증 및 정규화"""
        return {
            "x": max(0, int(bbox.get("x", 0))),
            "y": max(0, int(bbox.get("y", 0))),
            "w": max(0, int(bbox.get("w", 0))),
            "h": max(0, int(bbox.get("h", 0))),
        }

    def _is_bbox_valid(self, bbox: dict[str, int]) -> bool:
        """좌표가 화면 범위 내인지 검증"""
        x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]

        # 기본 범위 검증
        if x < 0 or y < 0 or w <= 0 or h <= 0:
            return False

        # 화면 범위 검증
        return not (x + w > self.screen_width or y + h > self.screen_height)

    def _is_domain_allowed(self, domain: str) -> bool:
        """도메인이 허용 목록에 있는지 검증"""
        if not domain:
            return False

        return any(allowed in domain for allowed in self.allowed_domains)

    def _assess_action_safety(self, action: dict[str, Any]) -> SafetyLevel:
        """액션의 안전도 평가"""
        action_text = (action.get("text") or "").lower()
        action_type = action.get("type", "").lower()

        # 파괴적 액션 검증
        if any(pattern in action_text for pattern in self.destructive_patterns):
            return SafetyLevel.CONFIRM

        # 타입 기반 안전도
        if action_type in ["click", "scroll", "wait"]:
            return SafetyLevel.SAFE
        elif action_type == "type":
            # 타이핑은 신중하게
            return SafetyLevel.CONFIRM
        elif action_type == "goto":
            # URL 이동은 확인 필요
            return SafetyLevel.CONFIRM

        return SafetyLevel.SAFE

    def _calculate_action_risk(self, action: dict[str, Any], context: dict[str, Any]) -> int:
        """액션별 리스크 점수 계산 (0-100)"""
        risk_score = 0

        # 신뢰도 기반 리스크
        confidence = action.get("confidence", 0.0)
        if confidence < 0.5:
            risk_score += 40
        elif confidence < 0.7:
            risk_score += 20

        # 액션 타입 기반 리스크
        action_type = action.get("type", "")
        if action_type == "click":
            risk_score += 10
        elif action_type == "type":
            risk_score += 30
        elif action_type == "goto":
            risk_score += 50

        # 컨텍스트 기반 리스크
        if context.get("is_production", False):
            risk_score += 20

        return min(100, risk_score)

    def _get_timestamp(self) -> str:
        """현재 타임스탬프"""
        from datetime import datetime

        return datetime.now(UTC).isoformat()


# 글로벌 인스턴스
action_validator = ActionValidator()
