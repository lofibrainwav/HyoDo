# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""
승상의 거울 (Mirror of Chancellor)
Trinity Score 실시간 모니터링 및 자동 알람 시스템

⚠️ DEPRECATED: This file is a thin wrapper for backward compatibility.
   Use `scripts.mirror` module directly for new code.

AFO 왕국의 眞善美孝永 철학을 실시간으로 모니터링하여
Trinity Score가 90점 미만으로 떨어질 경우 즉시 알람을 발생시킵니다.

Author: AFO Kingdom Development Team
Date: 2025-12-24
Version: 2.0.0 (Modularized)

Usage:
    python scripts/trinity_mirror.py
    python -m scripts.mirror.cli
"""

import asyncio

# Re-export from modular structure for backward compatibility
from scripts.mirror.alerts import AlertManager
from scripts.mirror.cli import main
from scripts.mirror.core import ChancellorMirror
from scripts.mirror.models import MirrorConfig, TrinityScoreAlert
from scripts.mirror.notifiers import DiscordNotifier, LocalLogNotifier, SlackNotifier
from scripts.mirror.recovery import RecoveryEngine

__all__ = [
    "TrinityScoreAlert",
    "MirrorConfig",
    "ChancellorMirror",
    "AlertManager",
    "DiscordNotifier",
    "SlackNotifier",
    "LocalLogNotifier",
    "RecoveryEngine",
    "main",
]

if __name__ == "__main__":
    # Python 3.7+ asyncio run
    asyncio.run(main())
