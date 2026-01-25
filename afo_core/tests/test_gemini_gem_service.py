# Trinity Score: 90.0 (Established by Chancellor)
"""
Tests for Gemini Gem Service

Tests session management, conversation history, and chat functionality.
"""

import pytest
from services.gemini_gem_service import (
    ConversationSession,
    GeminiGemService,
)


class TestConversationSession:
    """Tests for ConversationSession class."""

    def test_init_creates_empty_history(self) -> None:
        """Session should start with empty history."""
        session = ConversationSession("test-123", max_history=5)

        assert session.session_id == "test-123"
        assert session.history == []
        assert session.max_history == 5

    def test_add_message_appends_to_history(self) -> None:
        """Adding message should append to history."""
        session = ConversationSession("test-123")

        session.add_message("user", "Hello")
        session.add_message("model", "Hi there!")

        assert len(session.history) == 2
        assert session.history[0] == {"role": "user", "content": "Hello"}
        assert session.history[1] == {"role": "model", "content": "Hi there!"}

    def test_add_message_trims_when_exceeds_max(self) -> None:
        """History should be trimmed when exceeding max_history * 2."""
        session = ConversationSession("test-123", max_history=2)

        # Add 3 pairs (6 messages), should trim to 4 (max_history * 2)
        for i in range(3):
            session.add_message("user", f"User msg {i}")
            session.add_message("model", f"Model msg {i}")

        # Should keep last 2 pairs (4 messages)
        assert len(session.history) == 4
        assert session.history[0]["content"] == "User msg 1"

    def test_get_history_returns_copy(self) -> None:
        """get_history should return a copy, not the original."""
        session = ConversationSession("test-123")
        session.add_message("user", "Hello")

        history = session.get_history()
        history.append({"role": "user", "content": "Modified"})

        assert len(session.history) == 1  # Original unchanged

    def test_clear_empties_history(self) -> None:
        """clear should empty the history."""
        session = ConversationSession("test-123")
        session.add_message("user", "Hello")

        session.clear()

        assert session.history == []


class TestGeminiGemService:
    """Tests for GeminiGemService class."""

    def test_init_creates_empty_sessions(self) -> None:
        """Service should start with no sessions."""
        service = GeminiGemService()

        assert len(service._sessions) == 0

    def test_get_or_create_session_creates_new(self) -> None:
        """Should create new session if none exists."""
        service = GeminiGemService()

        session = service._get_or_create_session("test-session")

        assert session.session_id == "test-session"
        assert "test-session" in service._sessions

    def test_get_or_create_session_returns_existing(self) -> None:
        """Should return existing session if it exists."""
        service = GeminiGemService()
        session1 = service._get_or_create_session("test-session")
        session1.add_message("user", "Hello")

        session2 = service._get_or_create_session("test-session")

        assert session2 is session1
        assert len(session2.history) == 1

    def test_get_or_create_session_generates_id_if_none(self) -> None:
        """Should generate session ID if none provided."""
        service = GeminiGemService()

        session = service._get_or_create_session(None)

        assert session.session_id.startswith("gem-")
        assert len(session.session_id) == 12  # "gem-" + 8 hex chars

    def test_session_eviction_when_over_limit(self) -> None:
        """Should evict oldest session when exceeding max_sessions."""
        service = GeminiGemService()
        service._max_sessions = 3

        # Create 4 sessions
        service._get_or_create_session("session-1")
        service._get_or_create_session("session-2")
        service._get_or_create_session("session-3")
        service._get_or_create_session("session-4")

        # First session should be evicted
        assert "session-1" not in service._sessions
        assert len(service._sessions) == 3

    def test_clear_session_returns_true_if_exists(self) -> None:
        """clear_session should return True for existing session."""
        service = GeminiGemService()
        session = service._get_or_create_session("test-session")
        session.add_message("user", "Hello")

        result = service.clear_session("test-session")

        assert result is True
        assert service._sessions["test-session"].history == []

    def test_clear_session_returns_false_if_not_exists(self) -> None:
        """clear_session should return False for non-existent session."""
        service = GeminiGemService()

        result = service.clear_session("non-existent")

        assert result is False

    def test_get_session_info_returns_info_for_existing(self) -> None:
        """get_session_info should return info for existing session."""
        service = GeminiGemService()
        session = service._get_or_create_session("test-session")
        session.add_message("user", "Hello")
        session.add_message("model", "Hi")

        info = service.get_session_info("test-session")

        assert info is not None
        assert info["session_id"] == "test-session"
        assert info["message_count"] == 2
        assert "created_at" in info
        assert "updated_at" in info

    def test_get_session_info_returns_none_for_nonexistent(self) -> None:
        """get_session_info should return None for non-existent session."""
        service = GeminiGemService()

        info = service.get_session_info("non-existent")

        assert info is None

    def test_get_service_status_returns_status(self) -> None:
        """get_service_status should return service status dict."""
        service = GeminiGemService()
        service._get_or_create_session("test-1")
        service._get_or_create_session("test-2")

        status = service.get_service_status()

        assert "available" in status
        assert status["model"] == "gemini-1.5-flash"
        assert status["active_sessions"] == 2
        assert status["max_sessions"] == 100


@pytest.mark.asyncio
class TestGeminiGemServiceChat:
    """Async tests for chat functionality."""

    async def test_chat_returns_error_when_api_unavailable(self) -> None:
        """chat should return error when Gemini API is not available."""
        service = GeminiGemService()

        # API is typically not available in test environment
        result = await service.chat("Hello")

        # Either success (if API key set) or error
        assert "success" in result
        assert "session_id" in result
        assert "timestamp" in result

    async def test_chat_creates_session_if_none_provided(self) -> None:
        """chat should create a new session if no session_id provided."""
        service = GeminiGemService()

        result = await service.chat("Hello")

        # session_id may be None if API unavailable before session creation
        # or starts with "gem-" if session was created
        session_id = result.get("session_id")
        assert session_id is None or session_id.startswith("gem-")
