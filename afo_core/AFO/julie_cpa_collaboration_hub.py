"""
Julie CPA Agent Collaboration Hub

이 파일은 하위 호환성을 위한 래퍼입니다.
실제 구현은 AFO.julie_cpa.collaboration 모듈로 이동되었습니다.

Migration Guide:
    # Before
    from AFO.julie_cpa_collaboration_hub import collaboration_hub

    # After (recommended)
    from AFO.julie_cpa.collaboration import collaboration_hub
"""

from AFO.julie_cpa.collaboration import (
    CollaborationMessage,
    CollaborationSession,
    JulieCPAAgentCollaborationHub,
    collaboration_hub,
    get_collaboration_stats,
    handle_agent_message,
    register_agent_connection,
    start_collaboration_hub,
    stop_collaboration_hub,
    unregister_agent_connection,
)

__all__ = [
    "JulieCPAAgentCollaborationHub",
    "CollaborationMessage",
    "CollaborationSession",
    "collaboration_hub",
    "start_collaboration_hub",
    "stop_collaboration_hub",
    "get_collaboration_stats",
    "register_agent_connection",
    "unregister_agent_connection",
    "handle_agent_message",
]
