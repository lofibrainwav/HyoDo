# Trinity Score: 90.0 (Established by Chancellor)
"""
Mirror Module - Chancellor Mirror (승상의 거울)

Trinity Score 실시간 모니터링 및 자동 알람 시스템.
AFO 왕국의 眞善美孝永 철학을 실시간으로 모니터링합니다.

Modules:
- models: Data models (TrinityScoreAlert, MirrorConfig)
- core: ChancellorMirror main class
- alerts: Alert management
- notifiers: Multi-channel notifications (Discord/Slack/Local)
- recovery: Auto-recovery engine
"""

from scripts.mirror.alerts import AlertManager
from scripts.mirror.core import ChancellorMirror
from scripts.mirror.models import MirrorConfig, TrinityScoreAlert
from scripts.mirror.notifiers import (
    DiscordNotifier,
    LocalLogNotifier,
    NotifierBase,
    SlackNotifier,
)
from scripts.mirror.recovery import RecoveryEngine

__all__ = [
    "TrinityScoreAlert",
    "MirrorConfig",
    "ChancellorMirror",
    "AlertManager",
    "NotifierBase",
    "DiscordNotifier",
    "SlackNotifier",
    "LocalLogNotifier",
    "RecoveryEngine",
]
