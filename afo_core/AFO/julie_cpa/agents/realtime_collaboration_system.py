"""Real-time Collaboration System - Refactored Wrapper.

Original code moved to: AFO/julie_cpa/agents/collaboration/
"""

from .collaboration import (
    CollaborationSession,
    Operation,
    Participant,
    RealtimeCollaborationSystem,
)

__all__ = ["RealtimeCollaborationSystem", "CollaborationSession", "Participant", "Operation"]
