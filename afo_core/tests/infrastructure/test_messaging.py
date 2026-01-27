"""Tests for Agent Messaging Infrastructure (TICKET-108)

L2 Infrastructure Layer 메시징 시스템 단위 테스트.
SSOT: AGENTS.md
"""

import asyncio
from uuid import UUID

import pytest
from infrastructure.messaging.channel import (
    InMemoryBackplane,
    SecureAgentChannel,
)
from infrastructure.messaging.protocol import (
    AgentMessage,
    AgentMessagingProtocol,
    MessageEnvelope,
    MessagePriority,
    MessageStatus,
    MessageType,
    SecureChannelConfig,
    SecurityLevel,
)
from infrastructure.messaging.security import (
    AuthToken,
    MessageSecurity,
    SecurityContext,
)

from AFO.trinity_score_sharing.domain_models import AgentType, PillarScores


class TestMessageSecurity:
    """MessageSecurity 테스트"""

    def test_generate_token(self) -> None:
        """토큰 생성"""
        security = MessageSecurity()
        token = security.generate_token(
            agent_type=AgentType.ASSOCIATE,
            session_id="test-session",
            permissions=["message:send"],
            trinity_score=0.9,
        )

        assert isinstance(token, AuthToken)
        assert token.agent_type == AgentType.ASSOCIATE
        assert token.session_id == "test-session"
        assert token.trinity_score == 0.9
        assert token.token_value is not None
        assert not token.is_expired

    def test_validate_token(self) -> None:
        """토큰 검증"""
        security = MessageSecurity()
        token = security.generate_token(
            agent_type=AgentType.MANAGER,
            session_id="test-session",
        )

        is_valid, validated_token, error = security.validate_token(token.token_value)

        assert is_valid is True
        assert validated_token is not None
        assert validated_token.agent_type == AgentType.MANAGER
        assert error is None

    def test_invalid_token(self) -> None:
        """유효하지 않은 토큰"""
        security = MessageSecurity()

        is_valid, token, error = security.validate_token("invalid:token")

        assert is_valid is False
        assert token is None
        assert error is not None

    def test_revoke_token(self) -> None:
        """토큰 취소"""
        security = MessageSecurity()
        token = security.generate_token(
            agent_type=AgentType.AUDITOR,
            session_id="test",
        )

        # 취소 전 유효
        is_valid, _, _ = security.validate_token(token.token_value)
        assert is_valid is True

        # 토큰 취소
        security.revoke_token(token.token_id)

        # 취소 후 무효
        is_valid, _, error = security.validate_token(token.token_value)
        assert is_valid is False
        assert "revoked" in error.lower()

    def test_sign_and_verify_message(self) -> None:
        """메시지 서명 및 검증"""
        security = MessageSecurity()
        token = security.generate_token(
            agent_type=AgentType.ASSOCIATE,
            session_id="test",
        )

        message_content = "test message content"
        signature = security.sign_message(message_content, token)

        assert signature is not None
        assert len(signature) == 64  # SHA256 hex

        # 검증
        is_valid = security.verify_message_signature(
            message_content, signature, token, max_age_seconds=5
        )
        assert is_valid is True

    def test_encrypt_decrypt_payload(self) -> None:
        """페이로드 암호화/복호화"""
        security = MessageSecurity()
        payload = {"key": "value", "number": 42}

        encrypted = security.encrypt_payload(payload)
        decrypted = security.decrypt_payload(encrypted)

        assert encrypted != str(payload)
        assert decrypted == payload


class TestSecurityContext:
    """SecurityContext 테스트"""

    def test_governance_decision_auto_run(self) -> None:
        """거버넌스 결정 - AUTO_RUN"""
        context = SecurityContext(
            agent_type=AgentType.ASSOCIATE,
            session_id="test",
            authenticated=True,
            trinity_score=0.95,  # 95% >= 90%
            risk_score=0.05,  # 5% <= 10%
        )

        assert context.governance_decision == "AUTO_RUN"

    def test_governance_decision_ask_commander(self) -> None:
        """거버넌스 결정 - ASK_COMMANDER"""
        context = SecurityContext(
            agent_type=AgentType.ASSOCIATE,
            session_id="test",
            authenticated=True,
            trinity_score=0.8,  # 80% < 90%
            risk_score=0.1,
        )

        assert context.governance_decision == "ASK_COMMANDER"

    def test_governance_decision_block(self) -> None:
        """거버넌스 결정 - BLOCK (미인증)"""
        context = SecurityContext(
            agent_type=AgentType.ASSOCIATE,
            session_id="test",
            authenticated=False,
        )

        assert context.governance_decision == "BLOCK"


class TestAgentMessage:
    """AgentMessage 테스트"""

    def test_create_message(self) -> None:
        """메시지 생성"""
        message = AgentMessage(
            from_agent=AgentType.ASSOCIATE,
            to_agent=AgentType.MANAGER,
            message_type=MessageType.TRINITY_SCORE_UPDATE,
            session_id="test-session",
            payload={"trinity_score": 0.95},
        )

        assert isinstance(message.message_id, UUID)
        assert message.from_agent == AgentType.ASSOCIATE
        assert message.to_agent == AgentType.MANAGER
        assert message.status == MessageStatus.PENDING
        assert not message.is_expired

    def test_broadcast_message(self) -> None:
        """브로드캐스트 메시지"""
        message = AgentMessage(
            from_agent=AgentType.CHANCELLOR,
            to_agent="ALL",
            message_type=MessageType.SYSTEM_ALERT,
            session_id="test",
        )

        assert message.is_broadcast is True
        assert len(message.get_target_agents()) == len(AgentType)

    def test_strategist_broadcast(self) -> None:
        """3책사 브로드캐스트"""
        message = AgentMessage(
            from_agent=AgentType.CHANCELLOR,
            to_agent="STRATEGISTS",
            message_type=MessageType.INSIGHT,
            session_id="test",
        )

        targets = message.get_target_agents()
        assert AgentType.JANG_YEONG_SIL in targets
        assert AgentType.YI_SUN_SIN in targets
        assert AgentType.SHIN_SAIMDANG in targets
        assert AgentType.ASSOCIATE not in targets

    def test_message_with_pillar_scores(self) -> None:
        """5기둥 점수 포함 메시지"""
        scores = PillarScores(
            truth=0.9,
            goodness=0.85,
            beauty=0.8,
            serenity=0.9,
            eternity=0.95,
        )

        message = AgentMessage(
            from_agent=AgentType.ASSOCIATE,
            to_agent=AgentType.MANAGER,
            message_type=MessageType.TRINITY_SCORE_SYNC,
            session_id="test",
            pillar_scores=scores,
        )

        assert message.pillar_scores is not None
        assert message.pillar_scores.truth == 0.9


class TestMessageEnvelope:
    """MessageEnvelope 테스트"""

    def test_create_envelope(self) -> None:
        """봉투 생성"""
        message = AgentMessage(
            from_agent=AgentType.ASSOCIATE,
            to_agent=AgentType.MANAGER,
            message_type=MessageType.AGENT_REQUEST,
            session_id="test",
        )

        envelope = MessageEnvelope(
            message=message,
            security_level=SecurityLevel.AUTHENTICATED,
        )

        assert envelope.message == message
        assert envelope.security_level == SecurityLevel.AUTHENTICATED
        assert envelope.hop_count == 0

    def test_sign_envelope(self) -> None:
        """봉투 서명"""
        message = AgentMessage(
            from_agent=AgentType.ASSOCIATE,
            to_agent=AgentType.MANAGER,
            message_type=MessageType.AGENT_REQUEST,
            session_id="test",
        )

        envelope = MessageEnvelope(message=message)
        signature = envelope.sign("secret-key")

        assert signature is not None
        assert envelope.signature == signature

    def test_verify_signature(self) -> None:
        """서명 검증"""
        message = AgentMessage(
            from_agent=AgentType.ASSOCIATE,
            to_agent=AgentType.MANAGER,
            message_type=MessageType.AGENT_REQUEST,
            session_id="test",
        )

        envelope = MessageEnvelope(message=message)
        envelope.sign("secret-key")

        assert envelope.verify_signature("secret-key") is True
        assert envelope.verify_signature("wrong-key") is False


class TestAgentMessagingProtocol:
    """AgentMessagingProtocol 테스트"""

    def test_create_protocol(self) -> None:
        """프로토콜 생성"""
        protocol = AgentMessagingProtocol()

        assert protocol.VERSION == "1.0.0"
        assert protocol.config is not None

    def test_create_message_via_protocol(self) -> None:
        """프로토콜을 통한 메시지 생성"""
        protocol = AgentMessagingProtocol()

        message = protocol.create_message(
            from_agent=AgentType.ASSOCIATE,
            to_agent=AgentType.MANAGER,
            message_type=MessageType.COLLABORATION_REQUEST,
            session_id="test",
            payload={"request": "help"},
        )

        assert message.from_agent == AgentType.ASSOCIATE
        assert message.payload == {"request": "help"}

    def test_rate_limiting(self) -> None:
        """속도 제한"""
        config = SecureChannelConfig(
            rate_limit_enabled=True,
            max_messages_per_minute=5,
        )
        protocol = AgentMessagingProtocol(config)

        # 5개까지 허용
        for _ in range(5):
            assert protocol.check_rate_limit(AgentType.ASSOCIATE) is True

        # 6번째부터 제한
        assert protocol.check_rate_limit(AgentType.ASSOCIATE) is False

    def test_validate_envelope(self) -> None:
        """봉투 검증"""
        protocol = AgentMessagingProtocol()

        message = protocol.create_message(
            from_agent=AgentType.ASSOCIATE,
            to_agent=AgentType.MANAGER,
            message_type=MessageType.AGENT_REQUEST,
            session_id="test",
        )
        envelope = protocol.wrap_message(message)

        is_valid, error = protocol.validate_envelope(envelope)

        assert is_valid is True
        assert error is None


class TestInMemoryBackplane:
    """InMemoryBackplane 테스트"""

    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        """발행/구독"""
        backplane = InMemoryBackplane()
        received_messages = []

        async def handler(msg):
            received_messages.append(msg)

        # 구독
        await backplane.subscribe("test-channel", handler)

        # 메시지 생성 및 발행
        message = AgentMessage(
            from_agent=AgentType.ASSOCIATE,
            to_agent=AgentType.MANAGER,
            message_type=MessageType.AGENT_REQUEST,
            session_id="test",
        )
        envelope = MessageEnvelope(message=message)

        await backplane.publish("test-channel", envelope)

        # 수신 확인
        assert len(received_messages) == 1
        assert received_messages[0].message.from_agent == AgentType.ASSOCIATE

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """구독 취소"""
        backplane = InMemoryBackplane()
        received_messages = []

        async def handler(msg):
            received_messages.append(msg)

        sub_id = await backplane.subscribe("test-channel", handler)
        await backplane.unsubscribe(sub_id)

        message = AgentMessage(
            from_agent=AgentType.ASSOCIATE,
            to_agent=AgentType.MANAGER,
            message_type=MessageType.AGENT_REQUEST,
            session_id="test",
        )
        envelope = MessageEnvelope(message=message)
        await backplane.publish("test-channel", envelope)

        # 구독 취소 후 메시지 수신 안됨
        assert len(received_messages) == 0


class TestSecureAgentChannel:
    """SecureAgentChannel 테스트"""

    @pytest.mark.asyncio
    async def test_connect_agent(self):
        """Agent 연결"""
        channel = SecureAgentChannel()

        token, context = await channel.connect_agent(
            agent_type=AgentType.ASSOCIATE,
            session_id="test-session",
            trinity_score=0.9,
        )

        assert token is not None
        assert context is not None
        assert context.authenticated is True
        assert context.trinity_score == 0.9

    @pytest.mark.asyncio
    async def test_send_message(self):
        """메시지 전송"""
        channel = SecureAgentChannel()

        # 발신자 연결
        await channel.connect_agent(
            agent_type=AgentType.ASSOCIATE,
            session_id="test",
        )

        # 수신자 연결
        await channel.connect_agent(
            agent_type=AgentType.MANAGER,
            session_id="test",
        )

        # 메시지 전송
        ack, envelope = await channel.send_message(
            from_agent=AgentType.ASSOCIATE,
            to_agent=AgentType.MANAGER,
            message_type=MessageType.AGENT_REQUEST,
            session_id="test",
            payload={"request": "review"},
        )

        assert ack.success is True
        assert envelope.message.from_agent == AgentType.ASSOCIATE

    @pytest.mark.asyncio
    async def test_broadcast_to_strategists(self):
        """3책사 브로드캐스트"""
        channel = SecureAgentChannel()

        # Chancellor 연결
        await channel.connect_agent(
            agent_type=AgentType.CHANCELLOR,
            session_id="test",
        )

        # 브로드캐스트
        ack, envelope = await channel.broadcast_to_strategists(
            from_agent=AgentType.CHANCELLOR,
            message_type=MessageType.INSIGHT,
            session_id="test",
            payload={"insight": "important finding"},
        )

        assert ack.success is True
        assert envelope.message.to_agent == "STRATEGISTS"

    @pytest.mark.asyncio
    async def test_disconnect_agent(self):
        """Agent 연결 해제"""
        channel = SecureAgentChannel()

        await channel.connect_agent(
            agent_type=AgentType.ASSOCIATE,
            session_id="test",
        )

        result = await channel.disconnect_agent(AgentType.ASSOCIATE)
        assert result is True

        # 연결 해제 후 전송 시도 - 실패해야 함
        with pytest.raises(PermissionError):
            await channel.send_message(
                from_agent=AgentType.ASSOCIATE,
                to_agent=AgentType.MANAGER,
                message_type=MessageType.AGENT_REQUEST,
                session_id="test",
            )

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """채널 통계"""
        channel = SecureAgentChannel()

        await channel.connect_agent(
            agent_type=AgentType.ASSOCIATE,
            session_id="test",
        )

        stats = channel.get_stats()

        assert "channel" in stats
        assert "backplane" in stats
        assert "security" in stats
        assert "protocol" in stats
        assert AgentType.ASSOCIATE in stats["channel"]["connected_agents"]
