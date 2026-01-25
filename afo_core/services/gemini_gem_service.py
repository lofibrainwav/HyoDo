# Trinity Score: 90.0 (Established by Chancellor)
"""
Gemini Gem Service - Conversation Management for Gem Emulation

Handles session management and conversation history for the
Gemini Gem chat widget.
"""

import logging
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import TypedDict

from AFO.llms.gemini_api import gemini_api
from config.gemini_gem_config import GeminiGemConfig, default_gem_config

logger = logging.getLogger("AFO.GeminiGemService")


# --- Typed Response Models ---


class GemChatResult(TypedDict, total=False):
    """Typed response for chat method."""

    success: bool
    response: str
    error: str
    session_id: str | None
    model: str
    usage: dict[str, int]
    timestamp: str


class GemSessionInfo(TypedDict):
    """Typed response for session info."""

    session_id: str
    created_at: str
    updated_at: str
    message_count: int


class GemServiceStatus(TypedDict):
    """Typed response for service status."""

    available: bool
    model: str
    active_sessions: int
    max_sessions: int
    gem_url: str


class ConversationSession:
    """Represents a single conversation session."""

    def __init__(self, session_id: str, max_history: int = 10) -> None:
        self.session_id = session_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.history: list[dict[str, str]] = []
        self.max_history = max_history

    def add_message(self, role: str, content: str) -> None:
        """Add a message to history, maintaining max_history limit."""
        self.history.append({"role": role, "content": content})
        self.updated_at = datetime.now()

        # Trim history if exceeds max (keep pairs to maintain context)
        while len(self.history) > self.max_history * 2:
            self.history.pop(0)
            self.history.pop(0)

    def get_history(self) -> list[dict[str, str]]:
        """Get conversation history."""
        return self.history.copy()

    def clear(self) -> None:
        """Clear conversation history."""
        self.history = []
        self.updated_at = datetime.now()


class GeminiGemService:
    """
    Service for managing Gemini Gem conversations.

    Features:
    - Session management with LRU cache
    - Conversation history tracking
    - Gemini API integration with system instruction
    """

    def __init__(self, config: GeminiGemConfig | None = None) -> None:
        self.config = config or default_gem_config
        # LRU cache for sessions (max 100 sessions)
        self._sessions: OrderedDict[str, ConversationSession] = OrderedDict()
        self._max_sessions = 100
        logger.info("GeminiGemService initialized")

    def _get_or_create_session(self, session_id: str | None = None) -> ConversationSession:
        """Get existing session or create a new one."""
        if session_id is None:
            session_id = f"gem-{uuid.uuid4().hex[:8]}"

        if session_id in self._sessions:
            # Move to end (most recently used)
            self._sessions.move_to_end(session_id)
            return self._sessions[session_id]

        # Create new session
        session = ConversationSession(session_id, self.config.max_history)
        self._sessions[session_id] = session

        # Evict oldest if over limit
        while len(self._sessions) > self._max_sessions:
            self._sessions.popitem(last=False)

        return session

    async def chat(self, message: str, session_id: str | None = None) -> GemChatResult:
        """
        Process a chat message and return the response.

        Args:
            message: User message
            session_id: Optional session ID for conversation continuity

        Returns:
            dict with success, response, session_id, timestamp
        """
        # Get or create session first (always generate session_id)
        session = self._get_or_create_session(session_id)

        # Check Gemini API availability
        if not gemini_api.is_available():
            return {
                "success": False,
                "error": "Gemini API not configured. Please set GEMINI_API_KEY.",
                "session_id": session.session_id,
                "timestamp": datetime.now().isoformat(),
            }

        try:
            # Call Gemini API with system instruction
            result = await gemini_api.generate_with_system_instruction(
                prompt=message,
                system_instruction=self.config.system_instruction,
                conversation_history=session.get_history(),
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            if result.get("success"):
                response_content = result.get("content", "")

                # Add to conversation history
                session.add_message("user", message)
                session.add_message("model", response_content)

                return {
                    "success": True,
                    "response": response_content,
                    "session_id": session.session_id,
                    "model": result.get("model"),
                    "usage": result.get("usage"),
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Gemini Gem API error: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "session_id": session.session_id,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Gemini Gem Service exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session.session_id if session else session_id,
                "timestamp": datetime.now().isoformat(),
            }

    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session's history."""
        if session_id in self._sessions:
            self._sessions[session_id].clear()
            return True
        return False

    def get_session_info(self, session_id: str) -> GemSessionInfo | None:
        """Get information about a session."""
        if session_id not in self._sessions:
            return None

        session = self._sessions[session_id]
        return {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": len(session.history),
        }

    def get_service_status(self) -> GemServiceStatus:
        """Get service status for monitoring."""
        return {
            "available": gemini_api.is_available(),
            "model": self.config.model,
            "active_sessions": len(self._sessions),
            "max_sessions": self._max_sessions,
            "gem_url": self.config.gem_url,
        }


# Singleton instance
gemini_gem_service = GeminiGemService()
