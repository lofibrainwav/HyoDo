"""
MusicProvider 구현체들

각 Provider를 별도 모듈로 분리하여 500줄 규칙 준수
"""

from AFO.multimodal.providers.audiocraft import AudioCraftProvider
from AFO.multimodal.providers.base import MusicProvider
from AFO.multimodal.providers.mlx_musicgen import MLXMusicGenProvider
from AFO.multimodal.providers.musicgen import MusicGenProvider
from AFO.multimodal.providers.stable_audio import StableAudioProvider
from AFO.multimodal.providers.suno import SunoProvider

__all__ = [
    "MusicProvider",
    "AudioCraftProvider",
    "MusicGenProvider",
    "StableAudioProvider",
    "MLXMusicGenProvider",
    "SunoProvider",
]
