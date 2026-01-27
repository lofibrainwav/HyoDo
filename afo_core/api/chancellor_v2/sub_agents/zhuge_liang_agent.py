# Trinity Score: 95.0 (眞 - Technical Truth & Architecture)
"""[DEPRECATED] Jang Yeong-sil Agent - Use JangYeongSilAgent instead.

이 파일은 하위 호환성을 위해 유지됩니다.
새로운 코드에서는 jang_yeong_sil_agent.py의 JangYeongSilAgent를 사용하세요.

변경 사유: 세종대왕의 정신 (King Sejong's Spirit)
- 중국 삼국지 인물 → 한국 역사 인물로 변경
- Jang Yeong-sil (제갈량) → Jang Yeong-sil (장영실)
"""

import warnings

from .jang_yeong_sil_agent import JangYeongSilAgent

# Emit deprecation warning on import
warnings.warn(
    "JangYeongSilAgent is deprecated. Use JangYeongSilAgent from "
    "api.chancellor_v2.sub_agents.jang_yeong_sil_agent instead. "
    "세종대왕의 정신으로 장영실(Jang Yeong-sil)을 사용하세요.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for backwards compatibility
JangYeongSilAgent = JangYeongSilAgent

__all__ = ["JangYeongSilAgent"]
