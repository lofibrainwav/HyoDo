# Trinity Score: 95.0 (美 - UX, Narrative & Aesthetics)
"""[DEPRECATED] Zhou Yu Agent - Use ShinSaimdangAgent instead.

이 파일은 하위 호환성을 위해 유지됩니다.
새로운 코드에서는 shin_saimdang_agent.py의 ShinSaimdangAgent를 사용하세요.

변경 사유: 세종대왕의 정신 (King Sejong's Spirit)
- 중국 삼국지 인물 → 한국 역사 인물로 변경
- Zhou Yu (주유) → Shin Saimdang (신사임당)
"""

import warnings

from .shin_saimdang_agent import ShinSaimdangAgent

# Emit deprecation warning on import
warnings.warn(
    "ZhouYuAgent is deprecated. Use ShinSaimdangAgent from "
    "api.chancellor_v2.sub_agents.shin_saimdang_agent instead. "
    "세종대왕의 정신으로 신사임당(Shin Saimdang)을 사용하세요.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for backwards compatibility
ZhouYuAgent = ShinSaimdangAgent

__all__ = ["ZhouYuAgent"]
