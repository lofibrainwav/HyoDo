"""AFO Scholars Module.

Scholars for specialized AI tasks:
- Bangtong (Vladimir): Code Implementation
- Jaryong (Guan Yu): Code Review & Verification
- Yeongdeok (Zhang Liao): Documentation & Security
- Yukson (Xun Yu): Strategy & Planning
"""

from .bangtong import BangtongScholar, bangtong
from .jaryong import JaryongScholar, jaryong
from .kim_yu_sin import KimYuSinScholar, close_eyes, kim_yu_sin
from .yukson import YuksonScholar, yukson

__all__ = [
    "BangtongScholar",
    "bangtong",
    "JaryongScholar",
    "jaryong",
    "YeongdeokScholar",
    "yeongdeok",
    "close_eyes",
    "YuksonScholar",
    "yukson",
]
