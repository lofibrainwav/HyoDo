"""Message Security Layer (TICKET-108)

L2 Infrastructure Layer - 보안 채널 표준화
SSOT: AGENTS.md

인증, 권한 부여, 서명, 암호화를 위한 보안 레이어.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from AFO.trinity_score_sharing.domain_models import (
    THRESHOLD_AUTO_RUN_RISK,
    THRESHOLD_AUTO_RUN_SCORE,
    AgentType,
)

logger = logging.getLogger(__name__)


class AuthToken(BaseModel):
    """인증 토큰

    Agent 인증을 위한 토큰. JWT 대신 간단한 HMAC 기반 토큰 사용.
    """

    token_id: UUID = Field(default_factory=uuid4)
    agent_type: AgentType
    session_id: str = Field(min_length=1, max_length=256)

    # 토큰 메타데이터
    issued_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime | None = None
    ttl_seconds: int = Field(default=3600, ge=60, le=86400)

    # 권한
    permissions: list[str] = Field(default_factory=list)
    trinity_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # 토큰 값 (서명 후 설정)
    token_value: str | None = None

    @property
    def is_expired(self) -> bool:
        """토큰 만료 여부"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        elapsed = (datetime.now() - self.issued_at).total_seconds()
        return elapsed > self.ttl_seconds

    @property
    def can_auto_run(self) -> bool:
        """AUTO_RUN 권한 여부 (Trinity >= 90)"""
        return self.trinity_score * 100 >= THRESHOLD_AUTO_RUN_SCORE

    def has_permission(self, permission: str) -> bool:
        """권한 확인"""
        return permission in self.permissions or "*" in self.permissions


class SecurityContext(BaseModel):
    """보안 컨텍스트

    현재 Agent의 보안 상태를 나타내는 컨텍스트.
    """

    context_id: UUID = Field(default_factory=uuid4)
    agent_type: AgentType
    session_id: str

    # 인증 상태
    authenticated: bool = False
    auth_token: AuthToken | None = None
    auth_method: str | None = None  # "token", "certificate", "api_key"

    # Trinity Score 기반 권한
    trinity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # 활동 추적
    last_activity: datetime = Field(default_factory=datetime.now)
    message_count: int = Field(default=0, ge=0)
    error_count: int = Field(default=0, ge=0)

    @property
    def governance_decision(self) -> str:
        """거버넌스 결정 (AGENTS.md SSOT)"""
        if not self.authenticated:
            return "BLOCK"

        score_100 = self.trinity_score * 100
        risk_100 = self.risk_score * 100

        if score_100 >= THRESHOLD_AUTO_RUN_SCORE and risk_100 <= THRESHOLD_AUTO_RUN_RISK:
            return "AUTO_RUN"
        return "ASK_COMMANDER"

    def update_activity(self) -> None:
        """활동 업데이트"""
        self.last_activity = datetime.now()
        self.message_count += 1

    def record_error(self) -> None:
        """에러 기록"""
        self.error_count += 1


class MessageSecurity:
    """메시지 보안 관리자

    Agent 간 통신의 인증, 권한 부여, 서명, 암호화를 담당.
    """

    def __init__(self, secret_key: str | None = None) -> None:
        """
        Args:
            secret_key: HMAC 서명용 비밀 키. None이면 자동 생성.
        """
        self._secret_key = secret_key or secrets.token_hex(32)
        self._active_tokens: dict[UUID, AuthToken] = {}
        self._security_contexts: dict[str, SecurityContext] = {}
        self._revoked_tokens: set[UUID] = set()

        logger.info("MessageSecurity initialized")

    def generate_token(
        self,
        agent_type: AgentType,
        session_id: str,
        permissions: list[str] | None = None,
        trinity_score: float = 0.8,
        ttl_seconds: int = 3600,
    ) -> AuthToken:
        """인증 토큰 생성"""
        token = AuthToken(
            agent_type=agent_type,
            session_id=session_id,
            permissions=permissions or ["message:send", "message:receive"],
            trinity_score=trinity_score,
            ttl_seconds=ttl_seconds,
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
        )

        # 토큰 값 생성 (서명)
        payload = f"{token.token_id}:{agent_type.value}:{session_id}:{token.issued_at.isoformat()}"
        signature = hmac.new(
            self._secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        token.token_value = f"{token.token_id}:{signature}"

        # 활성 토큰에 추가
        self._active_tokens[token.token_id] = token

        logger.info(f"Token generated for {agent_type.value} in session {session_id}")
        return token

    def validate_token(self, token_value: str) -> tuple[bool, AuthToken | None, str | None]:
        """토큰 검증

        Returns:
            (성공 여부, 토큰 객체, 에러 메시지)
        """
        if not token_value or ":" not in token_value:
            return False, None, "Invalid token format"

        parts = token_value.split(":", 1)
        if len(parts) != 2:
            return False, None, "Invalid token format"

        try:
            token_id = UUID(parts[0])
        except ValueError:
            return False, None, "Invalid token ID"

        # 취소된 토큰 확인
        if token_id in self._revoked_tokens:
            return False, None, "Token revoked"

        # 활성 토큰 조회
        token = self._active_tokens.get(token_id)
        if not token:
            return False, None, "Token not found"

        # 만료 확인
        if token.is_expired:
            return False, None, "Token expired"

        # 서명 검증
        payload = f"{token.token_id}:{token.agent_type.value}:{token.session_id}:{token.issued_at.isoformat()}"
        expected_signature = hmac.new(
            self._secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(parts[1], expected_signature):
            return False, None, "Invalid signature"

        return True, token, None

    def revoke_token(self, token_id: UUID) -> bool:
        """토큰 취소"""
        if token_id in self._active_tokens:
            del self._active_tokens[token_id]
            self._revoked_tokens.add(token_id)
            logger.info(f"Token {token_id} revoked")
            return True
        return False

    def create_security_context(
        self,
        agent_type: AgentType,
        session_id: str,
        token: AuthToken | None = None,
    ) -> SecurityContext:
        """보안 컨텍스트 생성"""
        context_key = f"{agent_type.value}:{session_id}"

        context = SecurityContext(
            agent_type=agent_type,
            session_id=session_id,
            authenticated=token is not None and not token.is_expired,
            auth_token=token,
            auth_method="token" if token else None,
            trinity_score=token.trinity_score if token else 0.0,
        )

        self._security_contexts[context_key] = context
        return context

    def sign_message(self, message_content: str, token: AuthToken) -> str:
        """메시지 서명

        Args:
            message_content: 서명할 메시지 내용
            token: 서명에 사용할 토큰

        Returns:
            HMAC 서명 (hex)
        """
        payload = f"{token.token_id}:{message_content}:{int(time.time())}"
        signature = hmac.new(
            self._secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def verify_message_signature(
        self,
        message_content: str,
        signature: str,
        token: AuthToken,
        max_age_seconds: int = 300,
    ) -> bool:
        """메시지 서명 검증

        Note:
            시간 기반 검증으로 리플레이 공격 방지.
            max_age_seconds 이내의 서명만 유효.
        """
        now = int(time.time())

        # 최근 max_age_seconds 범위 내의 타임스탬프로 검증 시도
        for ts in range(now - max_age_seconds, now + 1):
            payload = f"{token.token_id}:{message_content}:{ts}"
            expected = hmac.new(
                self._secret_key.encode(),
                payload.encode(),
                hashlib.sha256,
            ).hexdigest()

            if hmac.compare_digest(signature, expected):
                return True

        return False

    def encrypt_payload(self, payload: dict[str, Any]) -> str:
        """페이로드 암호화 (간단한 XOR 기반)

        Note:
            프로덕션에서는 AES-GCM 등 강력한 암호화 사용 권장.
            현재는 시연용 간단 구현.
        """
        import json

        data = json.dumps(payload, default=str).encode()
        key = self._secret_key.encode()[:32].ljust(32, b"\0")

        # XOR 암호화 (시연용)
        encrypted = bytes(
            a ^ b for a, b in zip(data, (key * (len(data) // len(key) + 1))[: len(data)])
        )
        return base64.b64encode(encrypted).decode()

    def decrypt_payload(self, encrypted: str) -> dict[str, Any]:
        """페이로드 복호화"""
        import json

        data = base64.b64decode(encrypted.encode())
        key = self._secret_key.encode()[:32].ljust(32, b"\0")

        # XOR 복호화
        decrypted = bytes(
            a ^ b for a, b in zip(data, (key * (len(data) // len(key) + 1))[: len(data)])
        )
        return json.loads(decrypted.decode())

    def cleanup_expired(self) -> int:
        """만료된 토큰 및 컨텍스트 정리

        Returns:
            정리된 항목 수
        """
        cleaned = 0

        # 만료된 토큰 정리
        expired_tokens = [
            token_id for token_id, token in self._active_tokens.items() if token.is_expired
        ]
        for token_id in expired_tokens:
            del self._active_tokens[token_id]
            cleaned += 1

        # 비활성 컨텍스트 정리 (30분 이상 비활성)
        cutoff = datetime.now() - timedelta(minutes=30)
        inactive_contexts = [
            key for key, ctx in self._security_contexts.items() if ctx.last_activity < cutoff
        ]
        for key in inactive_contexts:
            del self._security_contexts[key]
            cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired items")

        return cleaned

    def get_security_stats(self) -> dict[str, Any]:
        """보안 통계"""
        return {
            "active_tokens": len(self._active_tokens),
            "revoked_tokens": len(self._revoked_tokens),
            "security_contexts": len(self._security_contexts),
            "contexts_by_agent": {
                agent.value: sum(
                    1 for ctx in self._security_contexts.values() if ctx.agent_type == agent
                )
                for agent in AgentType
            },
        }
