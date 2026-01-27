"""Sub-Agents Package - 3 Strategists 서브에이전트.

독립 컨텍스트에서 실행되는 3명의 Strategist를 정의합니다.

세종대왕의 정신 (King Sejong's Spirit):
- JangYeongSilAgent (眞 Truth): 장영실 - 기술적 정밀함 (측우기, 자격루)
- YiSunSinAgent (善 Goodness): 이순신 - 윤리적 충절 (거북선, 학익진)
- ShinSaimdangAgent (美 Beauty): 신사임당 - 예술적 아름다움 (초충도, 묵죽도)

Backwards Compatibility (구 삼국지 인물 이름):
- JangYeongSilAgent → JangYeongSilAgent
- YiSunSinAgent → YiSunSinAgent
- ShinSaimdangAgent → ShinSaimdangAgent
"""

from .base_strategist import BaseStrategist
from .jang_yeong_sil_agent import JangYeongSilAgent, JangYeongSilAgent
from .shin_saimdang_agent import ShinSaimdangAgent, ShinSaimdangAgent
from .yi_sun_sin_agent import YiSunSinAgent, YiSunSinAgent

__all__ = [
    "BaseStrategist",
    # 새로운 한국 인물 이름 (Primary)
    "JangYeongSilAgent",
    "YiSunSinAgent",
    "ShinSaimdangAgent",
    # 이전 삼국지 인물 이름 (Backwards Compatibility)
    "JangYeongSilAgent",
    "YiSunSinAgent",
    "ShinSaimdangAgent",
]
