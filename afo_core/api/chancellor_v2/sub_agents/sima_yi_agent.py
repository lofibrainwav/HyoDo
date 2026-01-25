# Trinity Score: 95.0 (善 - Ethics, Risk & Stability)
"""[DEPRECATED] Sima Yi Agent - Use YiSunSinAgent instead.

이 파일은 하위 호환성을 위해 유지됩니다.
새로운 코드에서는 yi_sun_sin_agent.py의 YiSunSinAgent를 사용하세요.

변경 사유: 세종대왕의 정신 (King Sejong's Spirit)
- 중국 삼국지 인물 → 한국 역사 인물로 변경
- Sima Yi (사마의) → Yi Sun-sin (이순신)
"""

import warnings

from .yi_sun_sin_agent import YiSunSinAgent

# Emit deprecation warning on import
warnings.warn(
    "SimaYiAgent is deprecated. Use YiSunSinAgent from "
    "api.chancellor_v2.sub_agents.yi_sun_sin_agent instead. "
    "세종대왕의 정신으로 이순신(Yi Sun-sin)을 사용하세요.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for backwards compatibility
SimaYiAgent = YiSunSinAgent

__all__ = ["SimaYiAgent"]
